"""Vercel serverless handler: POST /api/extract-documents.

Receives plain text already extracted in the browser by PDF.js. Routes each
document through:
  1. Regex extractor (fast, no API call)
  2. Gemini fallback if regex found nothing (handles real-world table layouts,
     varied units, and label variations that defeat regex)

Backend receives plain text + filename, never the binary PDF.

Request body:
    {
      "documents": [
        {"filename": "p&l_fy24.pdf", "text": "...", "detected_type": "pl"?}
      ]
    }
"""

import json
import os
import sys
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from enrichment import document_extractor, consistency_checker, profile_mapper  # noqa: E402

_GEMINI_FIELDS = [
    "revenue_cr", "cogs_cr", "gross_profit_cr", "ebitda_cr", "net_profit_cr",
    "payroll_cr", "total_assets_cr", "fixed_assets_cr", "current_assets_cr",
    "inventory_cr", "receivables_cr", "total_liabilities_cr", "equity_cr",
    "debt_cr",
]

_GEMINI_PROMPT = """\
You are a financial data extraction assistant for Indian companies.

Extract the following financial figures from the document text below.
Return ONLY a flat JSON object with exactly these keys (no nesting, no extra keys).
All values must be in INR Crore (₹ Cr). If a field is not present, use null.

- revenue_cr          Revenue from operations / total revenue
- cogs_cr             Cost of goods sold / cost of materials consumed / cost of revenue
- gross_profit_cr     Gross profit (if stated; else null — do NOT calculate)
- ebitda_cr           EBITDA / operating profit before D&A
- net_profit_cr       Net profit / profit after tax (PAT)
- payroll_cr          Employee benefit expenses / salaries and wages
- total_assets_cr     Total assets
- fixed_assets_cr     Property, plant and equipment / fixed assets / PPE
- current_assets_cr   Total current assets
- inventory_cr        Inventories
- receivables_cr      Trade receivables / accounts receivable
- total_liabilities_cr Total liabilities
- equity_cr           Total equity / shareholders' funds
- debt_cr             Total borrowings / long-term debt

Unit conversion rules (apply before returning):
- If document states "₹ in Lakhs" or "Rs. in Lakhs": divide each number by 100
- If document states "₹ in Millions" or "Rs. in Millions": divide by 10
- If document states "₹ in Crores" or "Rs. in Crores": use as-is
- If document states "₹ in Thousands": divide by 10,000
- If no unit stated but numbers look like crores (4-6 digits common for mid-cap): use as-is

Document type hint: {doc_type}
Document text (first 12000 characters):
---
{text}
---

Return ONLY the JSON object, no explanation, no markdown."""


def _call_gemini_extraction(text: str, doc_type: str) -> tuple[dict | None, str | None]:
    """Call Gemini to extract financial fields. Returns (fields_dict, error)."""
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return None, "GEMINI_API_KEY not configured"

    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )
    prompt = _GEMINI_PROMPT.format(doc_type=doc_type, text=text[:12000])
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 1024,
            "responseMimeType": "application/json",
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            detail = exc.read().decode()[:200]
        except Exception:
            detail = str(exc)
        return None, f"Gemini HTTP {exc.code}: {detail}"
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return None, f"Gemini request failed: {exc}"
    except json.JSONDecodeError:
        return None, "Gemini returned non-JSON envelope"

    parts = body.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    raw = "".join(p.get("text", "") for p in parts).strip()

    # Strip markdown fences if present.
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.rsplit("```", 1)[0].strip()

    try:
        extracted = json.loads(raw)
    except json.JSONDecodeError:
        return None, f"Gemini returned malformed JSON: {raw[:200]}"

    if not isinstance(extracted, dict):
        return None, "Gemini response was not a JSON object"

    # Convert to our field schema: {field: {value, confidence, source}}
    fields: dict = {}
    for key in _GEMINI_FIELDS:
        val = extracted.get(key)
        if val is not None:
            try:
                val = round(float(val), 2)
            except (TypeError, ValueError):
                val = None
        fields[key] = {
            "value": val,
            "confidence": "extracted" if val is not None else "not_found",
            "source": f"Gemini (LLM) — {doc_type.replace('_', ' ').title()}",
        }
    return fields, None


def _merge_extractions(per_doc: list[dict]) -> dict:
    """Merge field dicts across documents.

    ITR revenue stored under 'itr_revenue_cr' for consistency check.
    First non-None value wins per field.
    """
    merged: dict = {}
    for entry in per_doc:
        doc_type = entry["document_type"]
        fields = entry["fields"]
        for field_name, payload in fields.items():
            if payload.get("value") is None:
                continue
            key = "itr_revenue_cr" if (doc_type == "itr" and field_name == "revenue_cr") else field_name
            if key not in merged or merged[key].get("value") is None:
                merged[key] = dict(payload)
                merged[key]["document_source"] = entry["filename"]
    return merged


def _process_documents(documents: list[dict]) -> list[dict]:
    """Run extraction on each document, returning per-doc results."""
    results: list[dict] = []
    for d in documents:
        filename = (d.get("filename") or "untitled.pdf").strip()
        text = d.get("text") or ""
        declared = d.get("detected_type")
        doc_type = (
            declared if declared in ("pl", "balance_sheet", "itr")
            else document_extractor.detect_type(filename, text)
        )

        if not text.strip():
            results.append({
                "filename": filename,
                "document_type": doc_type,
                "extraction_status": "error",
                "extraction_errors": ["No text — PDF may be a scanned image."],
                "fields": {},
            })
            continue

        # --- Regex extraction ---
        fields: dict = {}
        if doc_type != "unknown":
            fields = document_extractor.extract(doc_type, text)

        found = sum(1 for f in fields.values() if f.get("value") is not None)

        # --- Gemini fallback when regex found nothing ---
        gemini_used = False
        if found == 0:
            # For unknown type, let Gemini infer from text.
            effective_type = doc_type if doc_type != "unknown" else "unknown (auto-detect)"
            gemini_fields, gemini_err = _call_gemini_extraction(text, effective_type)
            if gemini_fields:
                fields = gemini_fields
                found = sum(1 for f in fields.values() if f.get("value") is not None)
                gemini_used = True
                # If Gemini found results for an unknown type, promote to most
                # likely type based on which fields are present.
                if doc_type == "unknown":
                    if fields.get("total_assets_cr", {}).get("value") is not None:
                        doc_type = "balance_sheet"
                    elif fields.get("revenue_cr", {}).get("value") is not None:
                        doc_type = "pl"

        if found > 0:
            results.append({
                "filename": filename,
                "document_type": doc_type,
                "extraction_status": "success",
                "extraction_errors": [],
                "extraction_method": "gemini" if gemini_used else "regex",
                "fields": fields,
            })
        elif doc_type == "unknown":
            results.append({
                "filename": filename,
                "document_type": "unknown",
                "extraction_status": "error",
                "extraction_errors": [
                    "Could not identify document type. Please upload a P&L Statement, "
                    "Balance Sheet, or ITR — not an Annual Report, Shareholding Pattern, "
                    "or other filing."
                ],
                "fields": {},
            })
        else:
            results.append({
                "filename": filename,
                "document_type": doc_type,
                "extraction_status": "error",
                "extraction_errors": [
                    "No financial figures found even after LLM extraction. "
                    "This may not be a standalone financial statement."
                ],
                "fields": {},
            })
    return results


def _overall_status(per_doc: list[dict]) -> str:
    statuses = {d["extraction_status"] for d in per_doc}
    if not per_doc:
        return "error"
    if statuses == {"success"}:
        return "success"
    if "success" in statuses:
        return "partial"
    return "error"


def _build_response(documents: list[dict]) -> dict:
    per_doc = _process_documents(documents)
    merged = _merge_extractions(per_doc)
    checks = consistency_checker.run_all_checks(merged)
    prefill = profile_mapper.map_extracts_to_profile(merged)
    evidence = profile_mapper.build_evidence_packet(merged)

    return {
        "status": _overall_status(per_doc),
        "documents_processed": len(per_doc),
        "documents": per_doc,
        "extraction_summary": merged,
        "consistency_checks": checks,
        "prefill_profile": prefill,
        "evidence_packet": evidence,
    }


class handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _send(self, status: int, body: bytes):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._send(200, json.dumps({
            "ok": True,
            "endpoint": "/api/extract-documents",
            "message": "POST {documents: [{filename, text, detected_type?}]} — text extracted client-side by PDF.js.",
        }).encode())

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        except Exception:
            self._send(400, json.dumps({"error": "Invalid JSON body."}).encode())
            return

        documents = payload.get("documents")
        if not isinstance(documents, list) or not documents:
            self._send(400, json.dumps({"error": "documents (non-empty array) is required."}).encode())
            return

        result = _build_response(documents)
        self._send(200, json.dumps(result, ensure_ascii=False).encode("utf-8"))
