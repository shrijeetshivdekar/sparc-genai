"""AI-driven bundle + top-5 standalone product recommender.

Calls Gemini with all extracted document signals and returns the best-fit
ICICI Lombard bundle plus 5 ranked standalone products with citations.

Group Safeguard is excluded from bundle picks — auto-attached as companion.
Cost: ~$0.0005–0.0008 per call (gemini-2.5-flash).
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


# ─── Bundle catalog with descriptions ────────────────────────────────────────

def _bundle_catalog_summary() -> str:
    from bundle_catalog import BUNDLE_CATALOG
    lines = []
    DESCRIPTIONS = {
        "industrial_all_risk":      "For factories, manufacturers, EV/hardware OEMs — covers plant, machinery, EEI, BI, PI, D&O",
        "corporate_cover_ii":       "For mid-size B2B/hybrid companies — covers property, BI, public liability, EC, cyber, D&O, PI",
        "business_shield_sme":      "For digital-first startups (Fintech, SaaS, D2C) — covers cyber, D&O, PI, crime",
        "msme_suraksha_kavach":     "For micro/small physical businesses (shops, small offices) — covers property/fire only",
        "enterprise_secure":        "For larger enterprises with physical + digital ops — covers property, BI, public liability, EC, cyber, D&O",
        "business_edge":            "Comprehensive SME package: fire, burglary, money, machinery, public liability",
        "group_safeguard":          "SKIP — auto-added as baseline companion (health, PA, EC)",
        "bharat_sookshma_udyam":    "For very small businesses only (SI < 5 Cr) — fire/property only",
        "contractor_all_risk":      "For construction/infra projects — engineering, public liability",
        "entertainment_production": "For events/media — event production, public liability",
        "i_select_liability":       "Liability-only bundle — PI, D&O, cyber, crime (no property) — for pure service companies",
    }
    for key, b in BUNDLE_CATALOG.items():
        if key == "group_safeguard":
            continue
        mandatory = ", ".join(b.get("mandatory_covers", []))
        desc = DESCRIPTIONS.get(key, "")
        lines.append(f"  {key}: [{mandatory}] — {desc}")
    return "\n".join(lines)


def _product_line() -> str:
    try:
        sys.path.insert(0, str(_root / "startup_shield_web"))
        from premium_estimator import PREMIUM_RANGES
        return ", ".join(PREMIUM_RANGES.keys())
    except Exception:
        return ""


# ─── Flatten extracted doc fields from {value:..., source:...} to raw values ─

def _flat(doc: dict) -> dict:
    """Flatten extraction envelope: {field: {value: X, source: Y}} → {field: X}"""
    if not isinstance(doc, dict):
        return {}
    out = {}
    for k, v in doc.items():
        if isinstance(v, dict) and "value" in v:
            out[k] = v["value"]
        elif v is not None:
            out[k] = v
    return out


def _infer_prior_bundle(prior: dict) -> str:
    """Derive the prior ICICI Lombard bundle key from policy number + lob."""
    pnum = str(prior.get("policy_number") or prior.get("lob") or "").upper()
    lob  = str(prior.get("lob") or "").upper()
    if "IAR" in pnum or "INDUSTRIAL ALL RISK" in lob or "INDUSTRIAL ALL RISK" in pnum:
        return "industrial_all_risk"
    if "BHARAT" in pnum or "SOOKSHMA" in pnum or "LAGHU" in pnum or "UDYAM" in pnum:
        return "msme_suraksha_kavach"
    if "BSM" in pnum or "BUSINESS SHIELD" in lob:
        return "business_shield_sme"
    if "CORPORATE" in pnum or "CORP" in pnum:
        return "corporate_cover_ii"
    if "ENTERPRISE" in pnum:
        return "enterprise_secure"
    if "CAR" in pnum or "CONTRACTOR" in lob:
        return "contractor_all_risk"
    # Generic fire/property lob with no clear bundle name — do NOT infer;
    # let sector archetype (Rule 2) decide the right bundle.
    return ""


def _compact_company(extracts: dict, inferences: dict, verified: dict,
                     documents_extracted: dict) -> dict:
    def v(d, key):
        e = (d or {}).get(key) or {}
        return e.get("value") if isinstance(e, dict) else e

    docs = documents_extracted or {}
    prior_raw  = _flat(docs.get("prior_policy") or {})
    vapt_raw   = _flat(docs.get("vapt_report") or {})
    msa_raw    = _flat(docs.get("client_contract") or {})
    gst_raw    = _flat(docs.get("gst_returns") or {})
    assets_raw = _flat(docs.get("asset_register") or {})

    prior_bundle = _infer_prior_bundle(prior_raw)

    ratios = (verified or {}).get("financial_ratios") or {}
    flat_ratios = {
        k: (val["value"] if isinstance(val, dict) and "value" in val else val)
        for k, val in ratios.items()
    }

    financials = {
        "revenue_cr":      v(extracts, "revenue_cr") or v(extracts, "itr_revenue_cr"),
        "net_profit_cr":   v(extracts, "net_profit_cr"),
        "ebitda_cr":       v(extracts, "ebitda_cr"),
        "equity_cr":       v(extracts, "equity_cr"),
        "debt_cr":         v(extracts, "debt_cr"),
        "payroll_cr":      v(extracts, "employee_benefit_cr") or v(extracts, "payroll_cr"),
        "ppe_cr":          assets_raw.get("total_replacement_cr") or v(extracts, "fixed_assets_cr"),
        "inventory_cr":    v(extracts, "inventory_cr"),
        "receivables_cr":  v(extracts, "trade_receivables_cr"),
    }

    return {
        "classification": {
            "sector":            (inferences or {}).get("sector"),
            "operations":        (inferences or {}).get("operations"),
            "data_sensitivity":  (inferences or {}).get("data_sensitivity"),
            "ai_in_product":     bool((inferences or {}).get("ai_in_product")),
            "regulatory_flags":  (inferences or {}).get("regulatory_flags") or [],
        },
        "financials_cr":  {k: val for k, val in financials.items() if val is not None},
        "ratios":         flat_ratios,
        "prior_policy":   prior_raw,
        "prior_bundle_inferred": prior_bundle,
        "vapt":           vapt_raw,
        "msa":            msa_raw,
        "gst":            gst_raw,
        "assets":         assets_raw,
    }


# ─── Prompt ───────────────────────────────────────────────────────────────────

_PROMPT_TEMPLATE = """\
You are a senior ICICI Lombard commercial underwriter. All data below was extracted
from the company's uploaded documents — treat it as verified ground truth.

# Company data
{company_json}

# ICICI Lombard bundle catalog (key: [mandatory_covers] — description)
{bundle_lines}

# Valid standalone product keys (additional picks MUST use keys from this list only)
{product_line}

# BUNDLE SELECTION RULES — follow in strict priority order

## Rule 1: Prior policy is the strongest signal
If prior_bundle_inferred is set, start from that bundle UNLESS the company's
risk profile has clearly changed. Reasons to stay: same sector, same operations,
similar asset value. A company that had industrial_all_risk last year almost
certainly needs industrial_all_risk this year.
  - prior_bundle_inferred="industrial_all_risk" → pick industrial_all_risk
  - prior_bundle_inferred="corporate_cover_ii"  → pick corporate_cover_ii
  - prior_bundle_inferred="business_shield_sme" → pick business_shield_sme
  - prior_bundle_inferred="property_fire_generic" AND ppe_cr>=5 → pick industrial_all_risk or corporate_cover_ii
  - prior_bundle_inferred="property_fire_generic" AND ppe_cr<5 → pick msme_suraksha_kavach

## Rule 2: Sector + operations archetype
If prior_bundle_inferred is empty, use this:
  - Manufacturing / Hardware OEM + Physical-only        → industrial_all_risk
  - Manufacturing / Hardware OEM + Hybrid               → corporate_cover_ii
  - Fintech / SaaS / Deeptech + Digital-only            → business_shield_sme
  - D2C / Consumer Brands + Hybrid or Physical-only     → corporate_cover_ii (ALWAYS — has property + liability + BI; never msme)
  - Logistics / Supply Chain + any                      → corporate_cover_ii
  - Healthtech + any                                    → business_shield_sme or corporate_cover_ii
  - Pure service company (no physical assets, ppe<1 Cr) → i_select_liability or business_shield_sme
  - Small physical shop / micro-SME (revenue<5 Cr)      → msme_suraksha_kavach

## Rule 3: Asset size check
  - ppe_cr >= 10 Cr → must include property_all_risk or equivalent; industrial_all_risk preferred
  - ppe_cr 5–10 Cr  → corporate_cover_ii or industrial_all_risk
  - ppe_cr < 5 Cr   → financial-lines bundle acceptable (business_shield_sme)
  - NEVER pick msme_suraksha_kavach if ppe_cr > 5 Cr or revenue > 10 Cr

## Rule 4: HARD exclusions — violating these is always wrong
  - msme_suraksha_kavach: FORBIDDEN if revenue_cr > 8 OR ppe_cr > 3 OR team_size > 20. This is a micro-shop bundle only. A D2C brand with ₹30 Cr revenue must NEVER get this.
  - contractor_all_risk: only for active construction / infra projects
  - entertainment_production: only for events / media companies
  - i_select_liability: only for pure service firms with no physical assets and revenue < 20 Cr

# ADDITIONAL PRODUCTS — mandatory cover rules by sector

## Manufacturing (any)
  - product_liability: CRITICAL mandatory (product defects can injure/kill)
  - employees_comp: CRITICAL mandatory (factory floor statutory requirement)
  - marine_transit: CRITICAL if inventory_cr >= 2 (goods in transit)
  - machinery_breakdown: HIGH if assets.oem_service_contracts=false
  - electronic_equipment: HIGH if sector involves hardware/EV/IoT

## Fintech / SaaS / Deeptech / AI
  - cyber_liability: CRITICAL (data breach, DPDP, regulatory fines)
  - dno_liability: CRITICAL if loss-making or investor-backed
  - professional_indemnity: CRITICAL if msa.retroactive_required=true OR msa.foreign_jurisdiction=true
  - crime_fidelity: HIGH (insider fraud, data sensitivity)
  - employees_comp: HIGH if payroll_cr >= 1 and multi-state

## D2C / Consumer Brands
  - product_liability: CRITICAL (consumer product defects)
  - marine_transit: HIGH if inventory_cr >= 2 (goods in transit)
  - trade_credit: HIGH if gst.b2b_concentration_top3 >= 0.7
  - employees_comp: CRITICAL if payroll_cr >= 1 and multi-state

## ALL sectors
  - employees_comp: CRITICAL if payroll_cr >= 1 Cr AND gst.state_count >= 3 (statutory)
  - dno_liability: CRITICAL if ratios.current_ratio < 1.0 OR ratios.debt_equity > 1.5 OR net_profit_cr < -5
  - trade_credit: HIGH if gst.b2b_concentration_top3 >= 0.7 (counterparty concentration risk)
  - cyber_liability: HIGH if vapt.critical_count >= 3 OR vapt.mfa_enabled=false
  - professional_indemnity: CRITICAL if msa.retroactive_required=true AND msa.foreign_jurisdiction=true

# CRITICAL GAP RULES
  - prior_policy.lapsed=true → cover is lapsed (urgent)
  - prior_policy.property_si < assets.total_replacement_cr → property underinsured
  - prior_policy.cyber_si < 5 AND vapt.critical_count >= 3 → cyber underinsured
  - payroll_cr >= 1 AND no employees_comp in prior policy → employees_comp uninsured

# Task
1. Pick the single best-fit bundle following the rules above. Do NOT pick group_safeguard.
2. Rank top 5 ADDITIONAL standalone products:
   - Key MUST be from the valid standalone product list
   - MUST NOT already be in the chosen bundle's mandatory_covers
   - Order by urgency: Critical first
3. List critical gaps.

Return ONLY this JSON (no markdown, no explanation).
Write ALL text fields in plain English for a business reader (RM or founder).
Use real numbers from the data. Never write field paths like "msa.foreign_jurisdiction_flag".

{{
 "bundle": {{
   "key": "...",
   "fit_pct": 0,
   "why": "2-3 sentences in plain English. Name WHY this bundle fits — reference actual numbers (revenue, sector, operations, prior policy LOB, PPE value). Example good output: 'Business Shield SME is the right choice because NeuralPay is a digital-only Fintech with no physical assets and high cyber exposure. Their previous Cyber policy (₹2 Cr SI) lapsed in March 2025 and they already had one claim — renewing with upgraded cover is the immediate priority. The bundle covers Cyber, D&O, PI and Crime, which directly address all four of their top-scoring risk areas.'"
 }},
 "additional": [
   {{
     "rank": 1,
     "product": "<key from standalone list>",
     "urgency": "Critical|High|Medium",
     "why": "1-2 sentences in plain English with actual numbers. Example good output: 'With ₹7.4 Cr in payroll across 8 states, Employees Compensation is a statutory requirement — the company is currently uninsured for every workplace injury across its entire workforce.'"
   }}
 ],
 "critical_gaps": [
   {{
     "cover": "<key>",
     "issue": "lapsed|underinsured|uninsured",
     "evidence": "Plain English with numbers. Example good output: 'Prior Cyber policy covered only ₹2 Cr SI but the company has 4 unpatched critical CVEs, no MFA, and had one claim last year — real exposure is at least ₹5 Cr.'"
   }}
 ]
}}"""


def recommend(extracts: dict, inferences: dict, verified: dict,
              documents_extracted: dict) -> dict | None:
    """Returns AI recommendation dict or None on any failure."""
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return None

    company  = _compact_company(extracts, inferences, verified, documents_extracted)
    prompt   = _PROMPT_TEMPLATE.format(
        company_json=json.dumps(company, separators=(",", ":"), default=str),
        bundle_lines=_bundle_catalog_summary(),
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
    req  = urllib.request.Request(
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
    in_t  = usage.get("promptTokenCount", 0)
    out_t = usage.get("candidatesTokenCount", 0)
    result["_usage"] = {
        "input_tokens":  in_t,
        "output_tokens": out_t,
        "cost_usd":      round((in_t * 0.15 + out_t * 0.60) / 1_000_000, 6),
    }
    return result
