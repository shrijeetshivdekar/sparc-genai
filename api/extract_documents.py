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
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from enrichment import document_extractor, consistency_checker, profile_mapper  # noqa: E402

# ─── Annual report detection + section extraction ────────────────────────────

_ANNUAL_REPORT_SIGNALS = [
    "directors' report", "director's report",
    "board of directors",
    "independent auditor's report", "auditor's report",
    "corporate governance",
    "management discussion and analysis",
    "annual report",
    "notice of annual general meeting", "annual general meeting",
]

_PL_HEADERS = [
    "statement of profit and loss",
    "statement of profit & loss",
    "profit and loss account",
    "standalone statement of profit",
    "consolidated statement of profit",
    "statement of income and expenditure",
]

_BS_HEADERS = [
    "balance sheet as at",
    "balance sheet as on",
    "consolidated balance sheet",
    "standalone balance sheet",
    "balance sheet (as at",
]

_NOTES_HEADERS = [
    "notes to financial statements",
    "notes to the financial statements",
    "notes forming part of financial statements",
    "notes to standalone financial statements",
    "notes to consolidated financial statements",
]


def _is_annual_report(filename: str, text: str) -> bool:
    name = (filename or "").lower()
    if "annual" in name or "annualreport" in name:
        return True
    # "Consolidated Financial Statements", "Standalone Financial Statements", etc.
    if "financial" in name and ("statement" in name or "consolidated" in name or "standalone" in name):
        return True
    head = (text or "")[:6000].lower()
    count = sum(1 for s in _ANNUAL_REPORT_SIGNALS if s in head)
    return count >= 2


def _extract_financial_sections(full_text: str) -> str:
    """Find P&L + Balance Sheet sections in an annual report and return them.

    Annual report financials are buried in the middle/end of the document.
    We locate section headers and extract a window after each.
    Falls back to the latter half of the text if headers not found.
    """
    lower = full_text.lower()
    sections = []

    for header in _PL_HEADERS:
        idx = lower.find(header)
        if idx != -1:
            sections.append(full_text[idx: idx + 8000])
            break

    for header in _BS_HEADERS:
        idx = lower.find(header)
        if idx != -1:
            sections.append(full_text[idx: idx + 8000])
            break

    for header in _NOTES_HEADERS:
        idx = lower.find(header)
        if idx != -1:
            sections.append(full_text[idx: idx + 4000])
            break

    if sections:
        return "\n\n---\n\n".join(sections)

    # Fallback: financials are usually in the latter half of Indian annual reports
    mid = len(full_text) // 2
    return full_text[mid: mid + 16000]


# ─── Financial field lists ────────────────────────────────────────────────────

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
- sector              EXACTLY ONE of: "SaaS / Enterprise Software" | "Fintech" | "Healthtech" |
                      "D2C / Consumer Brands" | "Deeptech / AI / Robotics" | "Edtech" |
                      "Agritech" | "Cleantech / Climatetech" | "Logistics / Mobility" |
                      "Legaltech" | "HRtech" | "Gaming / Media / Content" |
                      "Foodtech / Cloud Kitchen" | "IT Services" | "Manufacturing"
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
Document text:
---
{text}
---

Return ONLY the JSON object, no explanation, no markdown fences."""


def _gemini_post(url: str, payload: dict, max_retries: int = 3) -> tuple[dict | None, str | None]:
    """POST to Gemini with exponential backoff on 429/503. Returns (body, error)."""
    data = json.dumps(payload).encode("utf-8")
    for attempt in range(max_retries):
        req = urllib.request.Request(
            url, data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8")), None
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 503) and attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # 1s, 2s
                continue
            try:
                detail = exc.read().decode()[:200]
            except Exception:
                detail = str(exc)
            return None, f"Gemini HTTP {exc.code}: {detail}"
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            return None, f"Gemini request failed: {exc}"
        except json.JSONDecodeError:
            return None, "Gemini returned non-JSON envelope"
    return None, "Gemini max retries exceeded"


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
    prompt = _GEMINI_PROMPT.format(doc_type=doc_type, text=text[:16000])
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 1024,
            "responseMimeType": "application/json",
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }
    body, err = _gemini_post(url, payload)
    if err:
        return None, err

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



# ─── Per-doc-type Gemini prompts ─────────────────────────────────────────────

_GEMINI_GST_PROMPT = """\
You are a financial data extractor for an Indian insurance risk platform.
Extract the following fields from this GST Return document (GSTR-1, GSTR-3B, or summary).
Return ONLY a JSON object. Use null for missing values. All amounts in INR crore.

Fields to extract:
- turnover_cr          Total annual/quarterly turnover (convert lakh→cr, million→cr)
- b2b_invoices_cr      Total B2B invoice value
- b2c_invoices_cr      Total B2C (unregistered) invoice value
- export_invoices_cr   Total export invoice value (zero-rated)
- state_count          Number of distinct states with GSTIN registrations
- has_us_uk_export     true if any invoices to USA or UK clients, else false
- export_share         Export invoices / total turnover (0.0–1.0), or null
- b2b_concentration_top3  Top 3 buyers' share of total B2B revenue (0.0–1.0), or null
- b2c_share            B2C / total turnover (0.0–1.0), or null
- top_quarter_share    Highest single quarter as share of annual turnover (0.0–1.0), or null
- late_filings_4q      Number of quarters with late filing / penalty in last 4 quarters
- hsn_sac_codes        Array of HSN/SAC codes found (strings), or null
- gst_pl_mismatch_pct  null (requires P&L cross-reference)
- sector_mismatch_flag null (requires declared sector cross-reference)

Document text:
---
{text}
---
Return ONLY the JSON object."""

_GEMINI_POLICY_PROMPT = """\
You are an insurance data extractor for an Indian risk platform.
Extract the following fields from this insurance policy schedule or certificate.
Return ONLY a JSON object. Use null for missing values. All monetary amounts in INR crore.

Fields to extract:
- policy_number         Policy number
- insurer               Insurer name
- lob                   Line of business (e.g. "Cyber Liability", "D&O", "Professional Indemnity", "Fire/Property", "Group Health", "Crime/Fidelity", "Employees Compensation")
- inception_date        Policy start date (string)
- expiry_date           Policy end date (string)
- cyber_si              Cyber liability sum insured in crore (null if not cyber policy)
- pi_si                 Professional indemnity sum insured in crore (null if not PI)
- do_si                 D&O liability sum insured in crore (null if not D&O)
- property_si           Property/fire sum insured in crore (null if not property)
- crime_si              Crime/fidelity sum insured in crore (null if not crime)
- ec_si                 Employees compensation sum insured in crore (null if not EC)
- gh_si                 Group health sum insured in crore (null if not GH)
- premium_lakh          Annual premium in lakh
- deductible_lakh       Deductible / excess in lakh (null if not stated)
- cyber_claims_3yr      Number of cyber claims in last 3 years (0 if none stated)
- pi_claims_3yr         Number of PI claims in last 3 years (0 if none)
- do_claims_3yr         Number of D&O claims in last 3 years (0 if none)
- property_claims_3yr   Number of property/fire claims in last 3 years (0 if none)
- crime_claims_3yr      Number of crime claims in last 3 years (0 if none)
- ec_claims_3yr         Number of EC claims in last 3 years (0 if none)
- gh_loss_ratio         Group health loss ratio as decimal (e.g. 0.82 for 82%), or null
- cyber_ncd_years       Consecutive claim-free years for cyber NCD (0 if claims exist)
- pi_ncd_years          Consecutive claim-free years for PI NCD
- do_ncd_years          Consecutive claim-free years for D&O NCD
- property_ncd_years    Consecutive claim-free years for property NCD
- pi_retroactive_years  Number of years of retroactive cover (null if not stated)

Document text:
---
{text}
---
Return ONLY the JSON object."""

_GEMINI_CONTRACT_PROMPT = """\
You are a legal document analyser for an Indian insurance risk platform.
Extract the following risk-relevant fields from this contract (MSA, SOW, or service agreement).
Return ONLY a JSON object. Use null for missing values.

Fields to extract:
- client_name               Client / counterparty name
- contract_type             Type (e.g. "MSA", "SOW", "NDA", "Service Agreement")
- liability_cap_inr         Aggregate liability cap in INR (convert to integer rupees). null if not capped.
- unlimited_liability_flag  true if there is NO liability cap or if liability is stated as "unlimited", else false
- liability_cap_to_revenue  null (requires revenue cross-reference)
- data_processor_role       true if vendor is described as "data processor" or "sub-processor" or processes client PII on their behalf
- pii_volume_est            Estimated number of PII records mentioned (integer), or null
- sla_penalty_per_day_inr   SLA penalty per day of downtime in INR (integer), or null
- foreign_jurisdiction_flag true if governing law is a foreign jurisdiction (USA, UK, Singapore, EU, etc.)
- governing_law             Name of the governing jurisdiction (e.g. "New York", "England and Wales")
- retroactive_required      true if the contract requires vendor to maintain retroactive PI cover
- third_party_indemnity_flag true if vendor must indemnify client's affiliates, subsidiaries, or end-customers

Document text:
---
{text}
---
Return ONLY the JSON object."""

_GEMINI_ASSET_PROMPT = """\
You are a financial data extractor for an Indian insurance risk platform.
Extract the following fields from this fixed asset register or asset inventory.
Return ONLY a JSON object. Use null for missing values. All monetary amounts in INR crore.

Fields to extract:
- total_replacement_cr      Total replacement / reinstatement value of all assets in crore
- total_book_cr             Total book value / WDV (written down value) of all assets in crore
- replacement_vs_book_premium_pct  (replacement - book) / book as decimal, or null if either is missing
- location_count            Number of distinct physical locations / sites
- weighted_avg_age_all      Cost-weighted average age of all assets in years
- weighted_avg_age_electronic  Average age of electronic/IT equipment (servers, laptops, networking) in years
- weighted_avg_age_machinery   Average age of heavy machinery, plant, boilers in years
- imported_share            Share of assets that are imported (0.0–1.0), or null
- oem_service_contracts     true if OEM/manufacturer service contracts are mentioned

Document text:
---
{text}
---
Return ONLY the JSON object."""

_GEMINI_VAPT_PROMPT = """\
You are a cybersecurity data extractor for an Indian insurance risk platform.
Extract the following fields from this VAPT, penetration test, or security audit report.
Return ONLY a JSON object. Use null for missing values.

Fields to extract:
- critical_count            Number of Critical severity vulnerabilities (CVSS 9.0+)
- high_count                Number of High severity vulnerabilities (CVSS 7.0–8.9)
- audit_date                Date of the audit/assessment (string, e.g. "15 Nov 2024")
- audit_age_months          Age of audit in months from today (approximate integer), or null
- mfa_enabled               true if MFA/2FA is enforced on admin/privileged accounts, false if explicitly NOT enforced, null if not stated
- endpoint_protection_deployed  true if EDR/AV/endpoint protection is deployed, false if explicitly absent, null if not stated
- backup_rto_hours          Recovery Time Objective in hours (convert days to hours if stated in days)
- third_party_access_count  Number of third-party vendors with privileged/admin access
- iso27001_or_soc2_active   true if ISO 27001 or SOC 2 Type II certificate is current and in scope
- dpdp_audit_completed      true if a DPDP Act compliance audit has been completed

Document text:
---
{text}
---
Return ONLY the JSON object."""

_NON_FINANCIAL_PROMPTS = {
    "gst_returns":    _GEMINI_GST_PROMPT,
    "prior_policy":   _GEMINI_POLICY_PROMPT,
    "client_contract": _GEMINI_CONTRACT_PROMPT,
    "asset_register": _GEMINI_ASSET_PROMPT,
    "vapt_report":    _GEMINI_VAPT_PROMPT,
}

# Fields each prompt returns — used to build the {field: {value, confidence, source}} schema
_NON_FINANCIAL_FIELDS = {
    "gst_returns": ["turnover_cr","b2b_invoices_cr","b2c_invoices_cr","export_invoices_cr","state_count","has_us_uk_export","export_share","b2b_concentration_top3","b2c_share","top_quarter_share","late_filings_4q","hsn_sac_codes","gst_pl_mismatch_pct","sector_mismatch_flag"],
    "prior_policy": ["policy_number","insurer","lob","inception_date","expiry_date","cyber_si","pi_si","do_si","property_si","crime_si","ec_si","gh_si","premium_lakh","deductible_lakh","cyber_claims_3yr","pi_claims_3yr","do_claims_3yr","property_claims_3yr","crime_claims_3yr","ec_claims_3yr","gh_loss_ratio","cyber_ncd_years","pi_ncd_years","do_ncd_years","property_ncd_years","pi_retroactive_years"],
    "client_contract": ["client_name","contract_type","liability_cap_inr","unlimited_liability_flag","liability_cap_to_revenue","data_processor_role","pii_volume_est","sla_penalty_per_day_inr","foreign_jurisdiction_flag","governing_law","retroactive_required","third_party_indemnity_flag"],
    "asset_register": ["total_replacement_cr","total_book_cr","replacement_vs_book_premium_pct","location_count","weighted_avg_age_all","weighted_avg_age_electronic","weighted_avg_age_machinery","imported_share","oem_service_contracts"],
    "vapt_report": ["critical_count","high_count","audit_date","audit_age_months","mfa_enabled","endpoint_protection_deployed","backup_rto_hours","third_party_access_count","iso27001_or_soc2_active","dpdp_audit_completed"],
}


def _call_gemini_typed(text: str, doc_type: str) -> tuple[dict | None, str | None]:
    """Call Gemini with a doc-type-specific prompt. Returns (fields_dict, error).

    Each non-financial doc type has its own prompt asking for the exact fields
    that doc contains. Returns a {field: {value, confidence, source}} dict
    matching the same schema as _call_gemini_extraction.
    """
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return None, "GEMINI_API_KEY not configured"
    prompt_template = _NON_FINANCIAL_PROMPTS.get(doc_type)
    field_list = _NON_FINANCIAL_FIELDS.get(doc_type, [])
    if not prompt_template:
        return None, f"No prompt for doc_type={doc_type}"

    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )
    prompt = prompt_template.format(text=text[:12000])
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.0,
            "maxOutputTokens": 1024,
            "responseMimeType": "application/json",
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }
    body, err = _gemini_post(url, payload)
    if err:
        return None, err

    parts = body.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    raw = "".join(p.get("text", "") for p in parts).strip()
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

    # Normalise into {field: {value, confidence, source}} schema
    src = f"Gemini ({doc_type.replace('_', ' ').title()})"
    fields: dict = {}
    for field in field_list:
        val = extracted.get(field)
        fields[field] = {
            "value": val,
            "confidence": "extracted" if val is not None else "not_found",
            "source": src,
        }
    return fields, None


_DETECT_TYPE_PROMPT = """\
You are a document classifier for an Indian insurance risk platform.

Given the text of a document, return ONLY a JSON object with one key "doc_type"
set to the single best-matching type from this list:

  pl               — Profit & Loss Statement / Income Statement
  balance_sheet    — Balance Sheet / Statement of Financial Position
  itr              — Income Tax Return (ITR filing)
  annual_report    — Full Annual Report (combines P&L + Balance Sheet + Directors' Report)
  gst_returns      — GST Returns (GSTR-1, GSTR-3B, or GST summary)
  prior_policy     — Insurance Policy Schedule / Certificate of Insurance
  client_contract  — Client Contract / Master Services Agreement / SOW / NDA
  asset_register   — Fixed Asset Register / Asset Inventory
  vapt_report      — Security Audit / VAPT / Penetration Test / ISO 27001 report
  unknown          — Cannot determine document type

Rules:
- Return exactly one type.
- If the document contains a Sum Insured, Policy Number, and Insurer name → prior_policy
- If the document mentions GSTIN, GSTR, outward supplies → gst_returns
- If it mentions vulnerability, CVSS, penetration test, MFA, RTO → vapt_report
- If it has asset descriptions, purchase dates, WDV/replacement values → asset_register
- If it has indemnity clauses, governing law, liability cap, SLA → client_contract
- Only return "unknown" if genuinely indeterminate.

Document text (first 3000 chars):
---
{text}
---

Return ONLY: {{"doc_type": "<type>"}}"""


def _gemini_detect_type(text: str) -> str:
    """Ask Gemini to classify a document when regex heuristics returned 'unknown'.

    Returns one of the canonical doc_type strings, or 'unknown' on any failure.
    """
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return "unknown"
    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )
    prompt = _DETECT_TYPE_PROMPT.format(text=text[:3000])
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.0,
            "maxOutputTokens": 32,
            "responseMimeType": "application/json",
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }
    body, err = _gemini_post(url, payload, max_retries=2)
    if err:
        return "unknown"
    try:
        parts = body.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        raw = "".join(p.get("text", "") for p in parts).strip()
        if raw.startswith("```"):
            raw = raw.split("```", 2)[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.rsplit("```", 1)[0].strip()
        result = json.loads(raw).get("doc_type", "unknown")
        _valid = {"pl", "balance_sheet", "itr", "annual_report", "gst_returns",
                  "prior_policy", "client_contract", "asset_register", "vapt_report", "unknown"}
        return result if result in _valid else "unknown"
    except Exception:
        return "unknown"


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

        if not text.strip():
            results.append({
                "filename": filename,
                "document_type": "unknown",
                "extraction_status": "error",
                "extraction_errors": ["No text — PDF may be a scanned image."],
                "fields": {},
            })
            continue

        # Annual report: extract only the financial statement sections before
        # sending to Gemini (financials are buried; first 12K chars hits the
        # cover page and directors' report, never the P&L or balance sheet).
        is_ar = declared == "annual_report" or _is_annual_report(filename, text)
        if is_ar:
            doc_type = "annual_report"
            gemini_text = _extract_financial_sections(text)
            effective_type = "annual_report (financial statements extracted)"
        else:
            _allowed = (
                "pl", "balance_sheet", "itr",
                "gst_returns", "prior_policy", "client_contract",
                "asset_register", "vapt_report",
            )
            doc_type = (
                declared if declared in _allowed
                else document_extractor.detect_type(filename, text)
            )
            # AI fallback: if both filename and content heuristics failed, ask Gemini
            gemini_text = text
            if doc_type == "unknown":
                doc_type = _gemini_detect_type(text)
                effective_type = f"{doc_type} (ai-detected)" if doc_type != "unknown" else "unknown (ai-undetected)"
            else:
                effective_type = doc_type

        # Non-financial doc types (gst, policy, contract, asset register, vapt) skip
        # the financial Gemini prompt and go straight to their dedicated extractors.
        _NON_FINANCIAL = {"gst_returns", "prior_policy", "client_contract", "asset_register", "vapt_report"}

        fields: dict = {}
        extraction_method = "none"

        if doc_type in _NON_FINANCIAL:
            # Gemini-first with a doc-type-specific prompt, regex as fallback.
            gemini_fields, gemini_err = _call_gemini_typed(text, doc_type)
            if gemini_fields:
                fields = gemini_fields
                extraction_method = "gemini"
            else:
                # Gemini unavailable (no API key, timeout) — fall back to regex
                fields = document_extractor.extract(doc_type, text)
                extraction_method = "regex"

            found = sum(1 for f in fields.values() if isinstance(f, dict) and f.get("value") is not None)

            # Non-financial docs are always success if type was identified —
            # even with 0 fields, the doc presence counts toward confidence narrowing.
            results.append({
                "filename": filename,
                "document_type": doc_type,
                "detection_method": effective_type,
                "extraction_status": "success",
                "extraction_errors": [] if not gemini_err else [f"Gemini unavailable ({gemini_err}); used regex fallback"],
                "extraction_method": extraction_method,
                "fields_found": found,
                "fields": fields,
            })
            continue

        # --- Financial docs: Gemini-first extraction ---
        gemini_fields, gemini_err = _call_gemini_extraction(gemini_text, effective_type)
        if gemini_fields:
            fields = gemini_fields
            extraction_method = "gemini"
            # Promote doc_type from "unknown" or "annual_report" based on what Gemini found.
            if doc_type in ("unknown", "annual_report"):
                if fields.get("total_assets_cr", {}).get("value") is not None:
                    doc_type = "balance_sheet"
                elif fields.get("revenue_cr", {}).get("value") is not None:
                    doc_type = "pl"

        found = sum(
            1 for k, f in fields.items()
            if not k.startswith("_") and isinstance(f, dict) and f.get("value") is not None
        )

        # --- Regex fallback if Gemini failed entirely ---
        regex_fallback_type = doc_type if doc_type not in ("unknown", "annual_report") else None
        if found == 0 and regex_fallback_type:
            regex_fields = document_extractor.extract(regex_fallback_type, text)
            regex_found = sum(1 for f in regex_fields.values() if f.get("value") is not None)
            if regex_found > 0:
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
                "detection_method": effective_type,
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
                    "Could not identify document type. Supported types: P&L Statement, "
                    "Balance Sheet, ITR, or Annual Report."
                ],
                "fields": {},
            })
        elif doc_type == "annual_report":
            results.append({
                "filename": filename,
                "document_type": "annual_report",
                "extraction_status": "error",
                "extraction_errors": [
                    "Annual report detected but financial statements not found in the document. "
                    "Ensure the PDF is text-based (not a scanned image) and contains a "
                    "Statement of Profit & Loss and Balance Sheet."
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

    # Bundle non-financial docs into a per-doc-type bucket for the modifier engine.
    # Shape: {"gst_returns": {field: {value,..}}, "prior_policy": {...}, ...}
    documents_extracted: dict[str, dict] = {}
    for entry in per_doc:
        dt = entry.get("document_type") or "unknown"
        if dt in ("gst_returns", "prior_policy", "client_contract", "asset_register", "vapt_report"):
            bucket = documents_extracted.setdefault(dt, {})
            for fname, fval in (entry.get("fields") or {}).items():
                if fname.startswith("_"):
                    continue
                if fname not in bucket or (isinstance(bucket[fname], dict) and bucket[fname].get("value") is None):
                    bucket[fname] = fval
    # Also expose financials under their canonical doc-type keys so triggers like
    # gst_pl_mismatch can cross-reference.
    if any(e.get("document_type") == "pl" for e in per_doc):
        documents_extracted.setdefault("pl", {k: v for k, v in merged.items() if k in ("revenue_cr", "net_profit_cr", "payroll_cr", "gross_profit_cr", "cogs_cr")})
    if any(e.get("document_type") == "balance_sheet" for e in per_doc):
        documents_extracted.setdefault("balance_sheet", {k: v for k, v in merged.items() if k in ("total_assets_cr", "fixed_assets_cr", "current_assets_cr", "inventory_cr", "receivables_cr", "total_liabilities_cr", "equity_cr", "debt_cr")})

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
        "documents_extracted": documents_extracted,
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
