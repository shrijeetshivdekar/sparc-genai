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
    "debt_cr", "tax_paid_cr",
]

_GEMINI_CATEGORICAL = [
    "company_name", "fiscal_year", "sector", "operations", "data_sensitivity",
    "ai_in_product", "regulatory_flags", "inference_confidence", "inference_evidence",
]

_GEMINI_PROMPT = """\
You are a financial data extraction + business classification assistant for Indian companies.

Extract financial figures AND infer business classification from the document text below.
Return ONLY a flat JSON object with EXACTLY the keys listed (no nesting beyond what's shown).

FINANCIAL FIELDS (all values in INR Crore, null if not present):
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
- tax_paid_cr         Current tax / income tax expense

Unit conversion rules (apply before returning):
- "₹ in Lakhs"/"Rs. in Lakhs" → divide by 100
- "₹ in Millions"/"Rs. in Millions" → divide by 10
- "₹ in Crores"/"Rs. in Crores" → use as-is
- "₹ in Thousands" → divide by 10,000
- No unit but numbers look like crores → use as-is

CATEGORICAL INFERENCES (infer from document content — what the company does):
- company_name        Company name as appears in document, or null
- fiscal_year         Year-end like "FY2024" or "FY2023-24", or null
- sector              EXACTLY ONE of: "Fintech" | "Healthtech" | "SaaS / Enterprise Software" |
                      "Deeptech / AI / Robotics" | "Edtech" | "D2C / Consumer Brands" |
                      "Logistics / Mobility" | "Agritech / Foodtech" | "Cleantech / Climatetech" |
                      "Gaming / Media / Content" | "HRtech" | "Legaltech" | "Proptech" |
                      "Spacetech" | "Insurtech" | "IT Services" | "Manufacturing" | "Other"
- operations          EXACTLY ONE of: "Digital-only" | "Physical-only" | "Hybrid"
                      (Digital-only = SaaS/services no physical assets;
                       Physical-only = manufacturing/logistics with significant PPE;
                       Hybrid = mix like D2C with both online and warehouses)
- data_sensitivity    EXACTLY ONE of: "Low" | "Medium" | "High"
                      (High = payments/PII/health records; Medium = B2B customer data;
                       Low = anonymous public data)
- ai_in_product       true | false  (does the product use ML/AI as a feature?)
- regulatory_flags    Array (possibly empty) from:
                      ["RBI", "SEBI", "IRDAI", "DPDP", "CDSCO", "FSSAI", "DGCA",
                       "MeitY", "CERT-In", "ONDC", "PCI-DSS", "HIPAA", "GST", "PF/ESI"]
- inference_confidence A number 0.0-1.0 — how confident you are in the categorical inferences.
                      Low if document text is generic/short; high if rich domain signals found.
- inference_evidence  One short sentence (≤100 chars) citing what in the document drove your
                      sector/operations choice (e.g. "Mentions 'RBI NBFC registration' and
                      'digital lending product'").

Document type hint: {doc_type}
Document text (first 12000 characters):
---
{text}
---

Return ONLY the JSON object, no explanation, no markdown fences."""


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

    # Convert financial fields to our schema: {field: {value, confidence, source}}
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

    # Categorical inferences attached as a separate sub-dict (not a financial field).
    fields["_categorical_inferences"] = {
        k: extracted.get(k) for k in _GEMINI_CATEGORICAL
    }
    return fields, None


def _merge_extractions(per_doc: list[dict]) -> dict:
    """Merge financial field dicts across documents.

    ITR revenue stored under 'itr_revenue_cr' for consistency check.
    First non-None value wins per field. Categorical inferences excluded
    (they're merged separately via _merge_categorical_inferences).
    """
    merged: dict = {}
    for entry in per_doc:
        doc_type = entry["document_type"]
        fields = entry["fields"]
        for field_name, payload in fields.items():
            if field_name.startswith("_"):
                continue  # skip categorical inferences sub-dict
            if not isinstance(payload, dict) or payload.get("value") is None:
                continue
            key = "itr_revenue_cr" if (doc_type == "itr" and field_name == "revenue_cr") else field_name
            if key not in merged or merged[key].get("value") is None:
                merged[key] = dict(payload)
                merged[key]["document_source"] = entry["filename"]
    return merged


def _merge_categorical_inferences(per_doc: list[dict]) -> dict:
    """Merge Gemini's categorical inferences across documents.

    Highest inference_confidence wins for the categorical fields. Regulatory
    flags are unioned across all documents. Returns flat dict or empty.
    """
    best: dict | None = None
    best_conf = -1.0
    regulatory_flags: set = set()

    for entry in per_doc:
        inf = (entry.get("fields") or {}).get("_categorical_inferences")
        if not isinstance(inf, dict):
            continue
        conf = inf.get("inference_confidence")
        try:
            conf = float(conf) if conf is not None else 0.0
        except (TypeError, ValueError):
            conf = 0.0
        # Union regulatory flags across documents
        flags = inf.get("regulatory_flags")
        if isinstance(flags, list):
            regulatory_flags.update(str(f) for f in flags)
        if conf > best_conf:
            best_conf = conf
            best = dict(inf)

    if best is None:
        return {}
    if regulatory_flags:
        best["regulatory_flags"] = sorted(regulatory_flags)
    return best


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

        # --- Gemini-first extraction (returns financials + categorical inferences) ---
        fields: dict = {}
        extraction_method = "none"
        effective_type = doc_type if doc_type != "unknown" else "unknown (auto-detect)"
        gemini_fields, gemini_err = _call_gemini_extraction(text, effective_type)
        if gemini_fields:
            fields = gemini_fields
            extraction_method = "gemini"
            # Promote doc_type from "unknown" based on what Gemini found.
            if doc_type == "unknown":
                if fields.get("total_assets_cr", {}).get("value") is not None:
                    doc_type = "balance_sheet"
                elif fields.get("revenue_cr", {}).get("value") is not None:
                    doc_type = "pl"

        found = sum(
            1 for k, f in fields.items()
            if not k.startswith("_") and isinstance(f, dict) and f.get("value") is not None
        )

        # --- Regex fallback if Gemini failed entirely ---
        if found == 0 and doc_type != "unknown":
            regex_fields = document_extractor.extract(doc_type, text)
            regex_found = sum(1 for f in regex_fields.values() if f.get("value") is not None)
            if regex_found > 0:
                # Preserve any categorical inferences Gemini did return
                cat = fields.get("_categorical_inferences")
                fields = regex_fields
                if cat:
                    fields["_categorical_inferences"] = cat
                found = regex_found
                extraction_method = "regex"
        gemini_used = (extraction_method == "gemini")

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


def _base_scores_from_inferences(inferences: dict) -> dict | None:
    """Build a StartupInput from Gemini-inferred categorical fields and run the
    base 13-dim risk engine on it. Returns scores dict or None if inferences
    are incomplete / engine raises.
    """
    sector = inferences.get("sector")
    operations = inferences.get("operations")
    data_sens = inferences.get("data_sensitivity")
    if not (sector and operations and data_sens):
        return None
    try:
        # Lazy imports to keep the cold-start path light
        from risk_engine import StartupInput, compute_risk_scores, SECTOR_PROFILES
        if sector not in SECTOR_PROFILES:
            # Map non-canonical sectors to closest match. Fall back to "Other".
            mapping = {
                "IT Services": "SaaS / Enterprise Software",
                "Manufacturing": "D2C / Consumer Brands",
            }
            sector = mapping.get(sector, "Other" if "Other" in SECTOR_PROFILES else None)
            if not sector:
                return None
        inp = StartupInput(
            sector=sector,
            funding_stage="Series B+",  # placeholder; financials override via prefill
            team_size=100,                # placeholder
            operations=operations if operations in ("Digital-only", "Physical-only", "Hybrid") else "Hybrid",
            data_sensitivity=data_sens if data_sens in ("Low", "Medium", "High") else "Medium",
            ai_in_product=bool(inferences.get("ai_in_product")),
        )
        return compute_risk_scores(inp)
    except Exception:
        return None


def _build_response(documents: list[dict]) -> dict:
    per_doc = _process_documents(documents)
    merged = _merge_extractions(per_doc)
    inferences = _merge_categorical_inferences(per_doc)
    checks = consistency_checker.run_all_checks(merged)
    prefill = profile_mapper.map_extracts_to_profile(merged)
    evidence = profile_mapper.build_evidence_packet(merged)

    # Merge Gemini's categorical inferences into the form prefill so the user
    # opens the assessment form with sector/operations/data_sensitivity set.
    if inferences:
        if inferences.get("sector"):
            prefill["sector"] = {
                "value": inferences["sector"], "confidence": "extracted",
                "source": f"Inferred by Gemini: {inferences.get('inference_evidence','document analysis')}",
            }
        if inferences.get("operations"):
            prefill["operations"] = {
                "value": inferences["operations"], "confidence": "extracted",
                "source": "Inferred by Gemini from document content",
            }
        if inferences.get("data_sensitivity"):
            prefill["data_sensitivity"] = {
                "value": inferences["data_sensitivity"], "confidence": "extracted",
                "source": "Inferred by Gemini from document content",
            }
        if inferences.get("ai_in_product") is not None:
            prefill["ai_in_product"] = {
                "value": bool(inferences["ai_in_product"]), "confidence": "extracted",
                "source": "Inferred by Gemini from document content",
            }

    # --- Verified financial-ratio assessment layer ---
    verified = None
    base_scores = _base_scores_from_inferences(inferences) if inferences else None
    if base_scores:
        try:
            from pricing.financial_ratio_engine import verified_assessment
            verified = verified_assessment(
                extracts=merged,
                base_scores=base_scores,
                inferred_sector=inferences.get("sector"),
            )
        except Exception as exc:
            verified = {"error": f"verified_assessment failed: {type(exc).__name__}: {exc}"}

    return {
        "status": _overall_status(per_doc),
        "documents_processed": len(per_doc),
        "documents": per_doc,
        "extraction_summary": merged,
        "categorical_inferences": inferences,
        "consistency_checks": checks,
        "prefill_profile": prefill,
        "evidence_packet": evidence,
        "verified_assessment": verified,
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
