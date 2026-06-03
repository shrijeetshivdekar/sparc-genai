"""AI-driven bundle + top-5 standalone product recommender.

Calls Gemini with all extracted document signals (financials, ratios, VAPT,
client contract, prior policy, GST, asset register) and returns the best-fit
ICICI Lombard bundle plus 5 ranked standalone products with citations.

Group Safeguard is intentionally excluded from the primary bundle list — it is
always attached as the baseline companion by the existing engine, so the AI
picks the *risk* bundle only.

Cost: ~$0.0005 per call (gemini-2.5-flash, ~1300 in / 550 out tokens).
"""

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))


def _bundle_lines() -> str:
    """Compact catalog: 'key: cover1, cover2, ...' — group_safeguard excluded."""
    from bundle_catalog import BUNDLE_CATALOG
    lines = []
    for key, b in BUNDLE_CATALOG.items():
        if key == "group_safeguard":
            continue
        covers = ", ".join(b.get("mandatory_covers", []))
        lines.append(f"  {key}: {covers}")
    return "\n".join(lines)


def _product_line() -> str:
    """Comma-separated list of valid standalone product keys."""
    try:
        sys.path.insert(0, str(_root / "startup_shield_web"))
        from premium_estimator import PREMIUM_RANGES
        return ", ".join(PREMIUM_RANGES.keys())
    except Exception:
        return ""


def _compact_company(extracts: dict, inferences: dict, verified: dict,
                     documents_extracted: dict) -> dict:
    """Pull only the fields that drive bundle/cover decisions."""
    def v(d, key):
        e = (d or {}).get(key) or {}
        return e.get("value") if isinstance(e, dict) else e

    classification = {
        "sector": (inferences or {}).get("sector"),
        "operations": (inferences or {}).get("operations"),
        "data_sensitivity": (inferences or {}).get("data_sensitivity"),
        "ai_in_product": bool((inferences or {}).get("ai_in_product")),
        "regulatory_flags": (inferences or {}).get("regulatory_flags") or [],
    }
    financials = {
        "revenue_cr":       v(extracts, "revenue_cr") or v(extracts, "itr_revenue_cr"),
        "net_profit_cr":    v(extracts, "net_profit_cr"),
        "ebitda_cr":        v(extracts, "ebitda_cr"),
        "equity_cr":        v(extracts, "equity_cr"),
        "debt_cr":          v(extracts, "debt_cr"),
        "payroll_cr":       v(extracts, "employee_benefit_cr") or v(extracts, "payroll_cr"),
        "fixed_assets_cr":  v(extracts, "fixed_assets_cr"),
        "receivables_cr":   v(extracts, "trade_receivables_cr"),
    }
    ratios = (verified or {}).get("financial_ratios") or {}
    # ratios may be a dict of {ratio_name: {value, band, ...}} — compact to value only
    flat_ratios = {}
    for k, val in ratios.items():
        if isinstance(val, dict) and "value" in val:
            flat_ratios[k] = val["value"]
        else:
            flat_ratios[k] = val

    docs = documents_extracted or {}
    return {
        "classification": classification,
        "financials_cr": {k: val for k, val in financials.items() if val is not None},
        "ratios": flat_ratios,
        "vapt":         docs.get("vapt_report") or {},
        "msa":          docs.get("client_contract") or {},
        "prior_policy": docs.get("prior_policy") or {},
        "gst":          docs.get("gst_returns") or {},
        "assets":       docs.get("asset_register") or {},
    }


_PROMPT_TEMPLATE = """You are an ICICI Lombard commercial underwriter. All inputs were extracted
from the company's uploaded financial + operational documents (verified, not estimated).

# Company
{company_json}

# ICICI Lombard bundles (key: mandatory_covers)
{bundle_lines}

# Standalone products (additional recommendations MUST use a key from this list)
{product_line}

# Signal -> cover heuristics
- VAPT critical CVEs >=3 OR no MFA OR no EDR -> cyber_liability Critical
- B2B top-3 concentration >=70% -> trade_credit candidate (counterparty risk)
- Foreign-jurisdiction MSA + data processor role + retroactive required -> professional_indemnity contractually mandated
- Payroll >=1 Cr + multi-state -> employees_comp statutory must-have
- Prior policy lapsed -> urgent renewal + SI uplift
- Negative net margin / loss-making -> dno_liability elevated (investor scrutiny risk)
- High data_sensitivity + Fintech/SaaS -> crime_fidelity elevated (insider fraud)
- Indemnify third parties contract clause -> public_liability or product_liability uplift
- Digital-only operations + PPE <5 Cr -> prefer financial-lines bundles over property-inclusive bundles
- Multi-state operations (states >=5) -> public_liability if customer touchpoints

# Task
1. Pick the single best-fit bundle (Group Safeguard is auto-added as baseline companion; do NOT pick it).
2. Rank top 5 ADDITIONAL standalone products:
   - MUST be a key from the standalone product list above
   - MUST NOT already be in the chosen bundle's mandatory_covers
3. List critical gaps (lapsed, underinsured, uninsured-but-statutory).

Return ONLY this JSON:
{{
 "bundle": {{"key":"...","fit_pct":0,"why":"1-2 sentences citing specific signals"}},
 "additional": [
   {{"rank":1,"product":"<key>","urgency":"Critical|High|Medium","why":"1 sentence citing signals"}}
 ],
 "critical_gaps": [
   {{"cover":"<key>","issue":"lapsed|underinsured|uninsured","evidence":"<signal: value>"}}
 ]
}}"""


def recommend(extracts: dict, inferences: dict, verified: dict,
              documents_extracted: dict) -> dict | None:
    """Returns AI recommendation dict or None on any failure.

    Output shape:
      {
        "bundle": {"key": str, "fit_pct": int, "why": str},
        "additional": [{"rank": int, "product": str, "urgency": str, "why": str}, ...],
        "critical_gaps": [{"cover": str, "issue": str, "evidence": str}, ...],
        "_usage": {"input_tokens": int, "output_tokens": int, "cost_usd": float},
      }
    """
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return None

    company = _compact_company(extracts, inferences, verified, documents_extracted)
    prompt = _PROMPT_TEMPLATE.format(
        company_json=json.dumps(company, separators=(",", ":"), default=str),
        bundle_lines=_bundle_lines(),
        product_line=_product_line(),
    )

    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 2048,
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
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
        return None

    parts = body.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    raw = "".join(p.get("text", "") for p in parts).strip()
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.rsplit("```", 1)[0].strip()
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(result, dict):
        return None

    usage = body.get("usageMetadata", {}) or {}
    in_t = usage.get("promptTokenCount", 0)
    out_t = usage.get("candidatesTokenCount", 0)
    result["_usage"] = {
        "input_tokens": in_t,
        "output_tokens": out_t,
        "cost_usd": round((in_t * 0.15 + out_t * 0.60) / 1_000_000, 6),
    }
    return result
