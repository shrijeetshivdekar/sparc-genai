"""POST /api/verified-analyze

Takes the output of /api/extract-documents (extraction + Gemini inferences +
verified financial-ratio assessment) and runs the FULL analysis pipeline:

  1. Builds a SPARC profile dict from inferences + extracted financials
  2. Calls the existing analyze() engine → bundle, recommendations, premium
  3. Augments per-cover premiums with financial-derived SI × loading
  4. Optionally calls Gemini for company contact_email + product_description
  5. Generates outreach via existing outreach_prompts()
  6. Returns a slim payload tailored for the Verified Assessment UI

Cost: ~3 Gemini calls total (extraction already done; analyze itself does not
call Gemini; +1 contact lookup, +1 outreach generation). ~$0.001 per request.
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


# ─── Inference → Profile mapping ─────────────────────────────────────────────

_REGULATORY_FLAG_MAP = {
    "RBI":     "RBI / SEBI / IRDAI licensed",
    "SEBI":    "RBI / SEBI / IRDAI licensed",
    "IRDAI":   "RBI / SEBI / IRDAI licensed",
    "DPDP":    "DPDP Act obligations",
    "CDSCO":   "CDSCO / medical devices",
    "FSSAI":   "FSSAI / food safety",
    "DGCA":    "DGCA / drone operations",
    "MeitY":   "IT Act / CERT-In obligations",
    "CERT-In": "IT Act / CERT-In obligations",
    "GST":     None,   # Universal — don't add as a regulatory cover flag
    "PF/ESI":  "Labour Codes / gig worker regulations",
}

_DATA_BY_SENSITIVITY = {
    "High":   ["Personal identity data (KYC / Aadhaar)", "Sensitive personal data (DPDP Act)"],
    "Medium": ["Customer behavioural / usage data"],
    "Low":    [],
}

_ASSETS_BY_OPERATIONS = {
    "Digital-only":  ["None - fully cloud"],
    "Hybrid":        ["Office / coworking space"],
    "Physical-only": ["Office / coworking space", "Warehouse / fulfilment centre"],
}

# Bundle cover key (UPPERCASE engine keys) → premium_estimator.PREMIUM_RANGES key.
# Used so we can fetch a base premium estimate for any bundle cover.
_BUNDLE_KEY_TO_PREMIUM_KEY = {
    "CYBER":                   "cyber_liability",
    "CYBER_LIABILITY":          "cyber_liability",
    "D_AND_O":                  "dno_liability",
    "DNO_LIABILITY":            "dno_liability",
    "DIRECTORS_OFFICERS":       "dno_liability",
    "PI_TECH_EO":               "professional_indemnity",
    "PI":                       "professional_indemnity",
    "PROFESSIONAL_INDEMNITY":   "professional_indemnity",
    "HEALTHCARE_PI":            "healthcare_pi",
    "FINANCIAL_SERVICES_PI":    "financial_services_pi",
    "CGL":                      "comprehensive_general_liability",
    "COMMERCIAL_GENERAL_LIABILITY": "comprehensive_general_liability",
    "PUBLIC_LIABILITY":         "public_liability",
    "PRODUCT_LIABILITY":        "product_liability",
    "CRIME_FIDELITY":           "crime_fidelity",
    "EMPLOYMENT_PRACTICES":     "employment_practices",
    "EPLI":                     "employment_practices",
    "EMPLOYEE_HEALTH":          "employee_health",
    "GROUP_HEALTH":             "employee_health",
    "GMC":                      "employee_health",
    "EMPLOYEES_COMP":           "employees_comp",
    "WIBA":                     "employees_comp",
    "WORKMENS_COMPENSATION":    "employees_comp",
    "PROPERTY_FIRE":            "property_fire",
    "PROPERTY_ALL_RISK":        "property_all_risk",
    "FIRE":                     "property_fire",
    "IAR":                      "property_all_risk",
    "BUSINESS_EDGE":            "business_edge",
    "MSME_SURAKSHA":            "msme_suraksha",
    "BHARAT_SOOKSHMA":          "msme_suraksha",
    "BHARAT_LAGHU":             "msme_suraksha",
    "BHARAT_UDYAM":             "property_all_risk",
    "SURAKSHA_KAVACH":          "msme_suraksha",
    "ENTERPRISE_SECURE":        "enterprise_secure",
    "BUSINESS_INTERRUPTION":    "business_interruption",
    "TRADE_CREDIT":             "trade_credit",
    "MARINE_TRANSIT":           "marine_transit",
    "MARINE_CARGO":             "marine_transit",
    "KEY_PERSON":               "key_person",
    "GROUP_PA":                 "group_pa",
    "PAYMENT_PROTECTION":       "payment_protection",
    "PRODUCT_RECALL":           "product_recall",
    "DRONE_INSURANCE":          "drone_insurance",
    "MONEY_INSURANCE":          "money_insurance",
    "GADGET_EQUIPMENT":         "gadget_equipment",
    "ELECTRONIC_EQUIPMENT":     "electronic_equipment",
    "CLINICAL_TRIALS":          "clinical_trials",
    "CONTRACTORS_ALL_RISK":     "contractors_all_risk",
    "MACHINERY_BREAKDOWN":      "machinery_breakdown",
    "MOTOR_FLEET":              "motor_fleet",
    "EVENT_PRODUCTION":         "event_production",
    "SURETY":                   "surety",
    "GROUP_CRITI_SHIELD":       "group_criti_shield",
    "GROUP_HOSPISHIELD":        "group_hospishield",
}

# Cover (premium_estimator key) → ratio-engine SI cover name.
# Used to compute verified premium = base × loading.
_COVER_TO_SI_NAME = {
    "cyber_liability":         "Cyber Liability",
    "dno_liability":           "D&O Liability",
    "professional_indemnity":  "Professional Indemnity",
    "healthcare_pi":           "Professional Indemnity",
    "financial_services_pi":   "Professional Indemnity",
    "property_fire":           "Property / Fire",
    "property_all_risk":       "Property / Fire",
    "business_edge":           "Property / Fire",
    "msme_suraksha":           "Property / Fire",
    "enterprise_secure":       "Property / Fire",
    "trade_credit":            "Trade Credit",
    "payment_protection":      "Trade Credit",
    "marine_transit":          "Marine Cargo",
    "employee_health":         "Group Health",
    "group_pa":                "Group Health",
    "group_criti_shield":      "Group Health",
    "group_hospishield":       "Group Health",
    "employees_comp":          "Workers Comp / WIBA",
    "crime_fidelity":          "Crime / Fidelity",
    # employment_practices, key_person — no direct financial SI mapping
}


def _v(extracts: dict, field: str):
    """Safe lookup from extraction_summary."""
    entry = extracts.get(field) or {}
    val = entry.get("value")
    try:
        return float(val) if val is not None else None
    except (TypeError, ValueError):
        return None


def _build_profile(extracts: dict, inferences: dict, prefill: dict) -> dict:
    """Build a SPARC profile from extracted financials + Gemini inferences."""
    from startup_shield_web.server import DEFAULT_PROFILE, SECTOR_PROFILES

    profile = dict(DEFAULT_PROFILE)

    # Company name
    company = (inferences or {}).get("company_name") or "Verified Lead"
    profile["startup_name"] = str(company).strip()

    # Sector (validated against engine taxonomy)
    sector = (inferences or {}).get("sector")
    if sector:
        if sector in SECTOR_PROFILES:
            profile["sector"] = sector
        else:
            mapping = {
                "IT Services":            "SaaS / Enterprise Software",
                "Manufacturing":          "Manufacturing",
                "Agritech / Foodtech":    "Foodtech / Cloud Kitchen",
                "Foodtech":               "Foodtech / Cloud Kitchen",
                "Insurtech":              "Fintech",
                "Proptech":               "D2C / Consumer Brands",
                "Spacetech":              "Deeptech / AI / Robotics",
                "Other":                  "SaaS / Enterprise Software",
            }
            mapped = mapping.get(sector)
            if mapped and mapped in SECTOR_PROFILES:
                profile["sector"] = mapped

    # Stage + headcount come from prefill_profile (financial inference)
    if (pf := prefill.get("funding_stage")) and pf.get("value"):
        profile["funding_stage"] = pf["value"]
    if (pt := prefill.get("team_size")) and pt.get("value"):
        profile["team_size"] = int(pt["value"])

    # Operations
    ops = (inferences or {}).get("operations")
    if ops in ("Digital-only", "Physical-only", "Hybrid"):
        profile["operations"] = ops

    # Data sensitivity + derived data_handled list
    ds = (inferences or {}).get("data_sensitivity")
    if ds in ("Low", "Medium", "High"):
        profile["data_sensitivity"] = ds
        profile["data_handled"] = list(_DATA_BY_SENSITIVITY.get(ds, []))

    # AI in product
    profile["ai_in_product"] = bool((inferences or {}).get("ai_in_product"))
    profile["ai_tier"] = "Applied" if profile["ai_in_product"] else "None"

    # Regulatory list from Gemini flags
    reg: list[str] = []
    for flag in (inferences or {}).get("regulatory_flags", []) or []:
        mapped = _REGULATORY_FLAG_MAP.get(flag)
        if mapped and mapped not in reg:
            reg.append(mapped)
    if reg:
        profile["regulatory"] = reg

    # Physical assets — derive from operations + sector
    assets = list(_ASSETS_BY_OPERATIONS.get(profile["operations"], []))
    if profile.get("sector") == "Manufacturing" and "Manufacturing plant / factory" not in assets:
        assets.append("Manufacturing plant / factory")
    profile["physical_assets"] = assets

    # Financial fields the engine consumes
    rev_cr = _v(extracts, "revenue_cr") or _v(extracts, "itr_revenue_cr")
    if rev_cr is not None:
        profile["annual_revenue_cr"] = round(rev_cr, 2)
    ppe_cr = _v(extracts, "fixed_assets_cr")
    if ppe_cr is not None:
        profile["total_insurable_asset_value_cr"] = round(ppe_cr, 2)
    gp_cr = _v(extracts, "gross_profit_cr")
    if gp_cr is None:
        cogs = _v(extracts, "cogs_cr")
        if rev_cr is not None and cogs is not None:
            gp_cr = rev_cr - cogs
    if gp_cr is not None:
        profile["gross_profit_cr"] = round(gp_cr, 2)

    profile["has_investors"] = "Yes" if profile["funding_stage"] in ("Seed", "Series A", "Series B+") else "No"
    return profile


# ─── Gemini mini-call for outreach context (email + product description) ────

_CONTEXT_PROMPT = """\
You are an Indian startup analyst. Return ONLY a JSON object for "{company}"
(a {sector} company) using public knowledge. No markdown, no explanation.

{{
  "contact_email": <best-guess public business email — try in order: (1) official
                    contact like contact@ / info@ / hello@ at the company domain,
                    (2) founder if publicly listed, (3) construct from known
                    pattern like firstname@domain.com. Return null if no
                    reasonable inference possible.>,
  "product_description": <one sentence, max 160 chars — what they do, scale>,
  "biggest_fear": <max 120 chars — 2-3 top risk concerns, comma-separated>
}}
"""


def _fetch_outreach_context(company: str, sector: str) -> dict:
    """Mini Gemini call for contact_email + product_description + biggest_fear.

    Returns {} on any failure — outreach generator falls back gracefully.
    """
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key or not company or company == "Verified Lead":
        return {}

    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )
    prompt = _CONTEXT_PROMPT.format(company=company, sector=sector or "Indian startup")
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 256,
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
        with urllib.request.urlopen(req, timeout=12) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
        return {}

    parts = body.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    raw = "".join(p.get("text", "") for p in parts).strip()
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.rsplit("```", 1)[0].strip()
    try:
        out = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return out if isinstance(out, dict) else {}


# ─── Premium overlay (financial SI × loading) ────────────────────────────────

def _slug(s: str) -> str:
    """Normalise a cover label/key to a lookup slug."""
    import re
    s = re.sub(r"[^a-z0-9]+", "_", str(s or "").lower()).strip("_")
    return s


def _resolve_premium_key(bundle_key: str) -> str | None:
    """Bundle cover key (e.g. CYBER, PI_TECH_EO) → premium_estimator key."""
    if not bundle_key:
        return None
    upper = str(bundle_key).upper()
    if upper in _BUNDLE_KEY_TO_PREMIUM_KEY:
        return _BUNDLE_KEY_TO_PREMIUM_KEY[upper]
    lower = str(bundle_key).lower()
    if lower in _COVER_TO_SI_NAME or lower in _BUNDLE_KEY_TO_PREMIUM_KEY.values():
        return lower
    return None


def _find_si_cover(cover_key: str, cover_name: str, si_dict: dict) -> tuple[dict | None, str | None]:
    """Match an engine cover to one of the ratio-engine SI covers.

    Returns (si_entry, si_cover_name) so caller knows which loading to look up.
    """
    candidates: list[str] = []
    prem_key = _resolve_premium_key(cover_key)
    if prem_key:
        candidates.append(prem_key)
    candidates.extend([_slug(cover_key), _slug(cover_name)])

    for c in candidates:
        if c in _COVER_TO_SI_NAME:
            name = _COVER_TO_SI_NAME[c]
            if name in si_dict:
                return si_dict[name], name

    # Substring fuzzy fallback
    for cand_slug, si_name in _COVER_TO_SI_NAME.items():
        for c in candidates:
            if c and (cand_slug in c or c in cand_slug):
                if si_name in si_dict:
                    return si_dict[si_name], si_name
    return None, None


def _augment_with_verified_premium(
    items: list,
    si_dict: dict,
    loading_dict: dict,
    size_bucket: str | None = None,
    per_cover_doc_modifiers: dict | None = None,
    per_cover_confidence: dict | None = None,
) -> list:
    """For each product/cover, add verified_si_inr, verified_loading, and a
    verified_premium computed as base × loading.

    If item.premium isn't populated but the cover maps to a known
    premium_estimator key, fall back to estimate_premium(key, size_bucket).

    When per_cover_doc_modifiers is supplied, doc-driven multipliers and
    SI-floor overrides are merged into each item.
    """
    from premium_estimator import estimate_premium
    per_cover_doc_modifiers = per_cover_doc_modifiers or {}
    per_cover_confidence = per_cover_confidence or {}
    out = []
    for item in items or []:
        new_item = dict(item)
        key = item.get("key", "")
        name = item.get("name") or item.get("il_product_name", "")

        # Resolve / fetch base premium
        base_prem = item.get("premium")
        if not isinstance(base_prem, dict) or not (base_prem.get("min_lakh") or base_prem.get("max_lakh")):
            prem_key = _resolve_premium_key(key)
            if prem_key and size_bucket:
                est = estimate_premium(prem_key, size_bucket)
                if isinstance(est, dict):
                    base_prem = est
                    new_item["premium"] = est

        # Find ratio-engine SI counterpart
        si_entry, si_cover_name = _find_si_cover(key, name, si_dict)
        # Doc-modifier lookup: try item key first, then the uppercase cover key if known
        doc_agg = per_cover_doc_modifiers.get(key) or per_cover_doc_modifiers.get(key.upper()) or {}
        doc_multiplier = float(doc_agg.get("multiplier", 1.0))
        si_floor_inr = doc_agg.get("si_floor_inr")
        conf = per_cover_confidence.get(key) or per_cover_confidence.get(key.upper())

        if si_entry or si_floor_inr:
            risk_loading = (loading_dict.get(si_cover_name) or {}).get("loading", 1.0) if si_cover_name else 1.0
            loading = round(risk_loading * doc_multiplier, 4)
            base_si = (si_entry or {}).get("si_inr", 0)
            if si_floor_inr and si_floor_inr > base_si:
                base_si = si_floor_inr
            new_item["verified_si_inr"] = base_si
            new_item["verified_si_cr"] = round(base_si / 1_00_00_000, 2) if base_si else None
            new_item["verified_loading"] = loading
            new_item["risk_loading"] = round(risk_loading, 4)
            new_item["doc_multiplier"] = round(doc_multiplier, 4)
            new_item["si_floor_inr"] = si_floor_inr
            new_item["verified_si_cover"] = si_cover_name
            new_item["doc_modifiers_applied"] = doc_agg.get("applied", [])
            if conf:
                new_item["confidence"] = conf
            if isinstance(base_prem, dict):
                lo = float(base_prem.get("min_lakh", 0.0) or 0)
                hi = float(base_prem.get("max_lakh", 0.0) or 0)
                new_item["verified_premium"] = {
                    "min_lakh": round(lo * loading, 2),
                    "max_lakh": round(hi * loading, 2),
                    "loading_applied": loading,
                }
        out.append(new_item)
    return out


# ─── Main orchestrator ──────────────────────────────────────────────────────

def _load_affinity_matrix() -> dict:
    try:
        with open(_root / "pricing" / "cover_document_affinity.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {"covers": {}}


def _build_response(payload: dict) -> dict:
    """Main pipeline. Returns slim payload for the Verified Assessment UI."""
    extracts = payload.get("extraction_summary") or {}
    inferences = payload.get("categorical_inferences") or {}
    verified = payload.get("verified_assessment") or {}
    prefill = payload.get("prefill_profile") or {}
    evidence = payload.get("evidence_packet") or {}
    # Doc-driven inputs (new):
    documents_extracted = payload.get("documents_extracted") or {}
    mca_snapshot = payload.get("mca_snapshot") or {}

    # If caller did not pre-extract docs but supplied a CIN, auto-fetch MCA (best-effort).
    if not mca_snapshot:
        cin = (prefill.get("cin") or inferences.get("cin") or "").strip().upper()
        if cin:
            try:
                from enrichment.mca_lookup import lookup_company
                mca_snapshot = lookup_company(cin)
            except Exception:
                mca_snapshot = {}

    profile = _build_profile(extracts, inferences, prefill)

    # Optional Gemini context for outreach (best-effort)
    ctx = _fetch_outreach_context(profile["startup_name"], profile.get("sector", ""))
    if ctx.get("contact_email"):
        profile["contact_email"] = ctx["contact_email"]
    if ctx.get("product_description"):
        profile["product_description"] = ctx["product_description"]
    if ctx.get("biggest_fear"):
        profile["biggest_fear"] = ctx["biggest_fear"]

    # Run the existing analysis pipeline.
    from startup_shield_web.server import (
        analyze, outreach_prompts, fallback_outreach_prompts, gemini_enabled,
    )
    analysis = analyze(profile)
    if "decline" in analysis:
        return {
            "ok": False,
            "decline": analysis["decline"],
            "profile": profile,
        }

    bundle = analysis.get("bundle_match") or {}
    bundle_alternatives = analysis.get("bundle_alternatives") or []
    recommendations = analysis.get("recommendations") or []
    global_products = analysis.get("global_products") or []
    size_bucket = analysis.get("size_bucket")
    scores = analysis.get("scores") or {}

    # ─── AI override: bundle pick + top-5 ranking ──────────────────────────
    # Calls Gemini with all extracted document signals. On any failure, the
    # existing engine output is kept unchanged.
    ai_reco = None
    try:
        from api.ai_recommender import recommend as _ai_recommend
        ai_reco = _ai_recommend(extracts, inferences, verified, documents_extracted)
    except Exception:
        ai_reco = None

    if ai_reco and isinstance(ai_reco.get("bundle"), dict):
        from bundle_catalog import BUNDLE_CATALOG
        from startup_shield_web.server import attach_group_safeguard_companion

        ai_bundle_key = ai_reco["bundle"].get("key")
        ai_bundle_def = BUNDLE_CATALOG.get(ai_bundle_key)
        if ai_bundle_def and ai_bundle_key != "group_safeguard":
            target_name = ai_bundle_def.get("name")
            pool = [bundle] + list(bundle_alternatives)
            picked = next(
                (b for b in pool if (b or {}).get("name") == target_name),
                None,
            )
            if picked is None:
                # AI picked a bundle the deterministic engine excluded —
                # keep the deterministic result unchanged.
                picked = bundle
            if picked is not bundle:
                new_alternatives = [b for b in pool if b is not picked]
                bundle = dict(picked)
                bundle_alternatives = new_alternatives
                bundle, bundle_alternatives, _ = attach_group_safeguard_companion(
                    bundle, bundle_alternatives,
                )
            # Overlay AI fit % and reasoning
            try:
                bundle["fit_pct"] = int(ai_reco["bundle"].get("fit_pct") or bundle.get("fit_pct", 0))
            except (TypeError, ValueError):
                pass
            why = ai_reco["bundle"].get("why")
            if why:
                bundle["ai_why"] = why

        # Reorder recommendations so AI's top-5 picks come first (preserving
        # the engine's full list — premium overlay code below still works).
        ai_picks = ai_reco.get("additional") or []
        ai_order = [p.get("product") for p in ai_picks if isinstance(p, dict) and p.get("product")]
        if ai_order:
            ai_why_by_key = {p["product"]: p.get("why") for p in ai_picks if p.get("product")}
            ai_urgency_by_key = {p["product"]: p.get("urgency") for p in ai_picks if p.get("product")}
            rec_by_key = {r.get("key"): r for r in recommendations if r.get("key")}
            reordered, used = [], set()
            for key in ai_order:
                rec = rec_by_key.get(key)
                if rec and key not in used:
                    r = dict(rec)
                    if ai_why_by_key.get(key):
                        r["ai_why"] = ai_why_by_key[key]
                    if ai_urgency_by_key.get(key):
                        r["ai_urgency"] = ai_urgency_by_key[key]
                    reordered.append(r)
                    used.add(key)
            for rec in recommendations:
                if rec.get("key") not in used:
                    reordered.append(rec)
            recommendations = reordered

    # Premium overlay with financial-derived SI × loading
    si_dict = verified.get("sum_insured_per_cover") or {}
    loading_dict = verified.get("risk_loading_per_cover") or {}

    # ─── Doc-modifier engine (NEW): evaluates trigger-based catalog entries ──
    from pricing.document_modifier_engine import evaluate_and_aggregate
    from pricing.model import load_params as _load_params
    try:
        _params = _load_params()
        _catalog = _params.get("loadings_discounts") or {}
        applied_doc_modifiers, per_cover_doc_modifiers = evaluate_and_aggregate(
            documents_extracted, mca_snapshot, _catalog,
        )
    except Exception:
        applied_doc_modifiers, per_cover_doc_modifiers = [], {}

    # ─── Per-cover confidence (NEW): cover-document affinity matrix ─────────
    from pricing.financial_ratio_engine import (
        compute_per_cover_confidence, rank_global_upload_next,
    )
    affinity = _load_affinity_matrix()
    per_cover_confidence = compute_per_cover_confidence(
        documents_extracted, mca_snapshot, affinity,
    )
    upload_next_global = rank_global_upload_next(per_cover_confidence, affinity, top_n=3)

    bundle_with_premium = dict(bundle)
    bundle_covers = bundle.get("mandatory_covers") or []
    from premium_estimator import estimate_premium as _est
    bundle_verified_lo = bundle_verified_hi = 0.0
    bundle_base_lo = bundle_base_hi = 0.0
    bundle_cover_breakdown = []
    _COVER_DISPLAY_NAMES = {
        "BHARAT_SOOKSHMA":  "Bharat Sookshma Udyam Suraksha (Property / Fire / BI)",
        "BHARAT_LAGHU":     "Bharat Laghu Udyam Suraksha (Property / BI)",
        "BHARAT_UDYAM":     "Bharat Udyam Suraksha (Property All Risk)",
        "SURAKSHA_KAVACH":  "MSME Suraksha Kavach (Property / Liability / BI)",
        "MSME_SURAKSHA":    "MSME Suraksha (Property / Fire)",
    }

    for cover_key in bundle_covers:
        rec = next((r for r in recommendations if r.get("key") == cover_key), None)
        cover_name = rec.get("name") if rec else _COVER_DISPLAY_NAMES.get(cover_key, cover_key)
        # Resolve base premium via translation map → premium_estimator
        prem_key = _resolve_premium_key(cover_key)
        base = (rec.get("premium") if rec else None) or {}
        if (not base.get("min_lakh") and not base.get("max_lakh")) and prem_key and size_bucket:
            est = _est(prem_key, size_bucket)
            if isinstance(est, dict):
                base = est
        si_entry, si_cover_name = _find_si_cover(cover_key, cover_name or "", si_dict)
        risk_loading = (loading_dict.get(si_cover_name) or {}).get("loading", 1.0) if si_cover_name else 1.0
        # NEW: per-cover doc-modifier multiplier (1.0 if none fired)
        doc_agg = per_cover_doc_modifiers.get(cover_key) or {}
        doc_multiplier = float(doc_agg.get("multiplier", 1.0))
        si_floor_inr = doc_agg.get("si_floor_inr")
        loading = round(risk_loading * doc_multiplier, 4)
        # Apply SI floor override from doc-driven loadings (e.g., unlimited liability contract)
        si_cr = None
        if si_entry:
            base_si = si_entry["si_inr"]
            if si_floor_inr and si_floor_inr > base_si:
                base_si = si_floor_inr
            si_cr = round(base_si / 1_00_00_000, 2)
        elif si_floor_inr:
            si_cr = round(si_floor_inr / 1_00_00_000, 2)
        lo = float(base.get("min_lakh", 0.0) or 0)
        hi = float(base.get("max_lakh", 0.0) or 0)
        v_lo = round(lo * loading, 2)
        v_hi = round(hi * loading, 2)
        bundle_base_lo += lo
        bundle_base_hi += hi
        bundle_verified_lo += v_lo
        bundle_verified_hi += v_hi
        bundle_cover_breakdown.append({
            "cover": cover_name or cover_key,
            "key": cover_key,
            "verified_si_cr": si_cr,
            "verified_si_cover": si_cover_name,
            "loading": loading,
            "risk_loading": round(risk_loading, 4),
            "doc_multiplier": round(doc_multiplier, 4),
            "si_floor_inr": si_floor_inr,
            "premium_lakh": {"min": round(lo, 2), "max": round(hi, 2)},
            "verified_premium_lakh": {"min": v_lo, "max": v_hi},
            "doc_modifiers_applied": doc_agg.get("applied", []),
            "confidence": per_cover_confidence.get(cover_key),
        })

    bundle_with_premium["base_premium_lakh"]     = {"min": round(bundle_base_lo, 2),  "max": round(bundle_base_hi, 2)}
    bundle_with_premium["verified_premium_lakh"] = {"min": round(bundle_verified_lo, 2), "max": round(bundle_verified_hi, 2)}
    bundle_with_premium["cover_breakdown"]       = bundle_cover_breakdown

    # Additional standalone products: top 5 ICICI products from `recommendations`
    # (NOT from global_products — that's the competitor benchmark list).
    # Exclude covers that are already in the bundle.
    bundle_premium_keys = set()
    for bc in bundle_covers:
        pk = _resolve_premium_key(bc)
        if pk:
            bundle_premium_keys.add(pk)
    # AI picks (if any) come first in rank order; remaining sorted by score desc.
    eligible = [r for r in recommendations if r.get("key") and r.get("key") not in bundle_premium_keys]
    icici_pool = sorted(
        eligible,
        key=lambda r: (0, 0) if r.get("ai_urgency") else (1, -float(r.get("score") or 0)),
    )
    additional = []
    for p in icici_pool[:5]:
        item = dict(p)
        additional.append(item)
    additional = _augment_with_verified_premium(
        additional, si_dict, loading_dict, size_bucket,
        per_cover_doc_modifiers=per_cover_doc_modifiers,
        per_cover_confidence=per_cover_confidence,
    )

    # Outreach generation — produces bundle + per-product drafts keyed by premium key
    if gemini_enabled():
        outreach, outreach_source, outreach_err = outreach_prompts(
            profile, scores, recommendations, bundle, size_bucket, None,
        )
    else:
        outreach = fallback_outreach_prompts(profile, scores, recommendations, bundle, None)
        outreach_source = "fallback"
        outreach_err = None

    # Attach per-product outreach to each additional product item
    if isinstance(outreach, dict):
        for item in additional:
            prod_key = item.get("key", "")
            prem_key = _resolve_premium_key(prod_key) or prod_key
            draft = outreach.get(prem_key) or outreach.get(prod_key)
            if draft:
                item["outreach"] = draft

    # Total expected premium (verified)
    total_verified_lo = bundle_verified_lo + sum(
        (item.get("verified_premium") or {}).get("min_lakh", 0.0) for item in additional
    )
    total_verified_hi = bundle_verified_hi + sum(
        (item.get("verified_premium") or {}).get("max_lakh", 0.0) for item in additional
    )

    return {
        "ok": True,
        "company_name": profile["startup_name"],
        "profile": {
            "startup_name": profile["startup_name"],
            "sector": profile.get("sector"),
            "funding_stage": profile.get("funding_stage"),
            "team_size": profile.get("team_size"),
            "operations": profile.get("operations"),
            "data_sensitivity": profile.get("data_sensitivity"),
            "contact_email": profile.get("contact_email"),
            "product_description": profile.get("product_description"),
            "annual_revenue_cr": profile.get("annual_revenue_cr"),
        },
        "scores": scores,
        "top_risks": analysis.get("top_risks") or [],
        "bundle": {
            "name": bundle_with_premium.get("name"),
            "il_product_name": bundle_with_premium.get("il_product_name"),
            "fit_pct": bundle_with_premium.get("fit_pct"),
            "match_strength": bundle_with_premium.get("match_strength"),
            "mandatory_covers": bundle_with_premium.get("mandatory_covers", []),
            "description": bundle_with_premium.get("description"),
            "base_premium_lakh": bundle_with_premium.get("base_premium_lakh"),
            "verified_premium_lakh": bundle_with_premium.get("verified_premium_lakh"),
            "cover_breakdown": bundle_with_premium.get("cover_breakdown", []),
            "ai_why": bundle_with_premium.get("ai_why"),
            "companion_bundle": bundle_with_premium.get("companion_bundle"),
        },
        "additional_products": additional,
        "outreach": {
            "source": outreach_source,
            "error": outreach_err,
            "prompts": outreach,
        },
        "premium_total_verified_lakh": {
            "min": round(total_verified_lo, 2),
            "max": round(total_verified_hi, 2),
        },
        "confidence_band": verified.get("confidence_band"),
        "per_cover_confidence": per_cover_confidence,
        "upload_next": upload_next_global,
        "documents_extracted_summary": {
            doc_type: {"field_count": sum(1 for v in fields.values() if isinstance(v, dict) and v.get("value") is not None)}
            for doc_type, fields in (documents_extracted or {}).items()
            if isinstance(fields, dict)
        },
        "mca_snapshot_summary": {
            "fetched": bool(mca_snapshot and mca_snapshot.get("source") not in (None, "unavailable")),
            "source": (mca_snapshot or {}).get("source"),
            "cin": (mca_snapshot or {}).get("cin"),
            "directors_count": len((mca_snapshot or {}).get("directors") or []),
            "charges_unsatisfied_count": (mca_snapshot or {}).get("charges_unsatisfied_count"),
        },
        "doc_modifiers_applied": applied_doc_modifiers,
        "evidence_packet": evidence,
        "ai_recommendation": (
            {
                "bundle_why": (ai_reco.get("bundle") or {}).get("why") if ai_reco else None,
                "critical_gaps": (ai_reco.get("critical_gaps") or []) if ai_reco else [],
                "usage": (ai_reco.get("_usage") or {}) if ai_reco else {},
            }
            if ai_reco else None
        ),
    }


# ─── HTTP handler (Vercel + local) ──────────────────────────────────────────

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
            "endpoint": "/api/verified-analyze",
            "message": "POST the JSON returned by /api/extract-documents (extraction_summary, categorical_inferences, verified_assessment, prefill_profile, evidence_packet) to receive bundle + standalone products + verified premium + outreach.",
        }).encode())

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        except Exception:
            self._send(400, json.dumps({"error": "Invalid JSON body."}).encode())
            return

        try:
            result = _build_response(payload)
        except Exception as exc:
            self._send(500, json.dumps({
                "error": f"verified-analyze failed: {type(exc).__name__}: {exc}",
            }).encode())
            return

        self._send(200, json.dumps(result, ensure_ascii=False, default=str).encode("utf-8"))
