"""Financial Ratio Risk Engine — Verified Assessment Layer.

Pure functions. Takes extracted financial figures + base 13-dim risk scores,
returns: ratio computations, modified scores, sum insured per cover, risk
loading multipliers, confidence band, data-quality warnings.

Score scale: 0-100 (matches risk_engine.compute_risk_scores output).
Currency: INR integer rupees (₹ Cr → ×1_00_00_000).
Bands: 4-tier identifiers like "q1_burn" / "q4_premium".
Modifier philosophy: insurance is risk-averse. Missing data → no modifier.
Modifiers clip at ±25 per dimension after sum; final scores clip to [0, 100].
"""

from __future__ import annotations

from typing import Optional


# Translation between internal short keys (used in this module) and the
# display-name keys returned by risk_engine.compute_risk_scores().
_KEY_TO_LABEL = {
    "cyber_technical":        "Cyber Technical Risk",
    "data_privacy":           "Data Privacy Risk",
    "liability":              "Liability Risk",
    "ip_infringement":        "IP Infringement Risk",
    "key_person":             "Key Person Risk",
    "governance_fraud":       "Governance & Fraud Risk",
    "property":               "Property Risk",
    "regulatory_compliance":  "Regulatory Compliance Risk",
    "esg_climate":            "ESG & Climate Risk",
    "geopolitical":           "Geopolitical Risk",
    "gig_labour":             "Gig & Labour Risk",
    "policy_velocity":        "Policy Velocity Risk",
    "reputation":             "Reputation Risk",
    "tax_tp":                 "Tax & TP Risk",
}
_LABEL_TO_KEY = {v: k for k, v in _KEY_TO_LABEL.items()}


def _normalise_scores_to_internal(scores: dict) -> dict:
    """Accept either internal-keyed or display-label-keyed scores → internal."""
    out: dict = {}
    for k, v in scores.items():
        if k in _LABEL_TO_KEY:
            out[_LABEL_TO_KEY[k]] = v
        else:
            out[k] = v
    return out


def _denormalise_scores_to_labels(scores: dict) -> dict:
    """Internal-keyed scores → display-label-keyed (matches engine output)."""
    return {_KEY_TO_LABEL.get(k, k): v for k, v in scores.items()}


# ────────────────────────────────────────────────────────────────────────────
# Input helpers
# ────────────────────────────────────────────────────────────────────────────

def _v(extracts: dict, field: str) -> Optional[float]:
    """Safe lookup from extraction_summary shape: {field: {value, ...}}."""
    entry = extracts.get(field) or {}
    val = entry.get("value")
    try:
        return float(val) if val is not None else None
    except (TypeError, ValueError):
        return None


def _cr_to_inr(cr: float) -> int:
    """Convert INR crore to integer rupees."""
    return int(round(cr * 1_00_00_000))


# ────────────────────────────────────────────────────────────────────────────
# Band classifiers — one per ratio
# ────────────────────────────────────────────────────────────────────────────

def _band_npm(m: float) -> str:
    if m < 0: return "burn_q1"
    if m < 0.05: return "thin_q2"
    if m < 0.15: return "healthy_q3"
    return "premium_q4"


def _band_gm(m: float) -> str:
    if m < 0.20: return "low_q1"
    if m < 0.40: return "mid_q2"
    if m < 0.70: return "high_q3"
    return "premium_q4"


def _band_de(ratio: Optional[float], equity: float) -> Optional[str]:
    if equity <= 0:
        return "distressed_negative_equity"
    if ratio is None:
        return None
    if ratio < 0.5: return "conservative_q1"
    if ratio < 1.5: return "moderate_q2"
    if ratio < 3.0: return "leveraged_q3"
    return "highly_leveraged_q4"


def _band_cr(ratio: float) -> str:
    if ratio < 1.0: return "liquidity_stress_q1"
    if ratio < 1.5: return "tight_q2"
    if ratio < 3.0: return "healthy_q3"
    return "idle_capital_q4"


def _band_dso(days: float) -> str:
    if days < 30: return "cash_business_q1"
    if days < 90: return "typical_b2b_q2"
    if days < 150: return "elevated_q3"
    return "credit_risk_q4"


def _band_ai(r: float) -> str:
    if r < 0.10: return "asset_light_q1"
    if r < 0.30: return "mixed_q2"
    if r < 0.60: return "asset_heavy_q3"
    return "infrastructure_q4"


def _band_pi(r: float) -> str:
    if r < 0.15: return "lean_q1"
    if r < 0.35: return "balanced_q2"
    if r < 0.60: return "people_heavy_q3"
    return "labour_dominated_q4"


def _band_te(r: float) -> str:
    if r < 0.15: return "aggressive_q1"
    if r < 0.25: return "low_q2"
    if r < 0.30: return "normal_q3"
    return "high_q4"


# ────────────────────────────────────────────────────────────────────────────
# Ratio computation
# ────────────────────────────────────────────────────────────────────────────

def compute_ratios(extracts: dict) -> dict:
    """Compute 8 financial ratios. Missing inputs → value=None, band=None."""
    revenue = _v(extracts, "revenue_cr") or _v(extracts, "itr_revenue_cr")
    cogs = _v(extracts, "cogs_cr")
    net_profit = _v(extracts, "net_profit_cr") or _v(extracts, "profit_cr")
    payroll = _v(extracts, "payroll_cr")
    total_assets = _v(extracts, "total_assets_cr")
    ppe = _v(extracts, "fixed_assets_cr")
    current_assets = _v(extracts, "current_assets_cr")
    receivables = _v(extracts, "receivables_cr")
    total_liab = _v(extracts, "total_liabilities_cr")
    equity = _v(extracts, "equity_cr")
    debt = _v(extracts, "debt_cr")
    tax_paid = _v(extracts, "tax_paid_cr")

    out: dict = {}

    # 1. Net profit margin
    if revenue and revenue > 0 and net_profit is not None:
        m = net_profit / revenue
        out["net_profit_margin"] = {
            "value": round(m, 4), "band": _band_npm(m),
            "formula": f"₹{net_profit} Cr / ₹{revenue} Cr",
        }
    else:
        out["net_profit_margin"] = {"value": None, "band": None, "formula": ""}

    # 2. Gross margin
    if revenue and revenue > 0 and cogs is not None:
        m = (revenue - cogs) / revenue
        out["gross_margin"] = {
            "value": round(m, 4), "band": _band_gm(m),
            "formula": f"(₹{revenue} − ₹{cogs}) / ₹{revenue} Cr",
        }
    else:
        out["gross_margin"] = {"value": None, "band": None, "formula": ""}

    # 3. Debt-to-equity
    if equity is not None and equity > 0:
        d = debt if debt is not None else (total_liab if total_liab is not None else 0)
        ratio = d / equity
        out["debt_to_equity"] = {
            "value": round(ratio, 3), "band": _band_de(ratio, equity),
            "formula": f"₹{d} Cr / ₹{equity} Cr",
        }
    elif equity is not None and equity <= 0:
        out["debt_to_equity"] = {
            "value": None, "band": "distressed_negative_equity",
            "formula": f"Equity = ₹{equity} Cr (≤ 0 → distressed)",
        }
    else:
        out["debt_to_equity"] = {"value": None, "band": None, "formula": ""}

    # 4. Current ratio (proxy: total_liab as denom, since current_liab not extracted)
    if current_assets is not None and total_liab and total_liab > 0:
        ratio = current_assets / total_liab
        out["current_ratio_proxy"] = {
            "value": round(ratio, 2), "band": _band_cr(ratio),
            "formula": f"₹{current_assets} Cr / ₹{total_liab} Cr (proxy: total liabilities)",
        }
    else:
        out["current_ratio_proxy"] = {"value": None, "band": None, "formula": ""}

    # 5. DSO (Days Sales Outstanding)
    if revenue and revenue > 0 and receivables is not None:
        d = (receivables / revenue) * 365
        out["dso_days"] = {
            "value": round(d, 1), "band": _band_dso(d),
            "formula": f"(₹{receivables} / ₹{revenue}) × 365",
        }
    else:
        out["dso_days"] = {"value": None, "band": None, "formula": ""}

    # 6. Asset intensity (PPE / Total Assets)
    if total_assets and total_assets > 0 and ppe is not None:
        r = ppe / total_assets
        out["asset_intensity"] = {
            "value": round(r, 3), "band": _band_ai(r),
            "formula": f"₹{ppe} Cr / ₹{total_assets} Cr",
        }
    else:
        out["asset_intensity"] = {"value": None, "band": None, "formula": ""}

    # 7. Payroll intensity (Payroll / Revenue)
    if revenue and revenue > 0 and payroll is not None:
        r = payroll / revenue
        out["payroll_intensity"] = {
            "value": round(r, 3), "band": _band_pi(r),
            "formula": f"₹{payroll} Cr / ₹{revenue} Cr",
        }
    else:
        out["payroll_intensity"] = {"value": None, "band": None, "formula": ""}

    # 8. Tax efficiency (Tax / PBT, where PBT = net_profit + tax_paid as proxy)
    if tax_paid is not None and net_profit is not None and (net_profit + tax_paid) > 0:
        pbt = net_profit + tax_paid
        r = tax_paid / pbt
        out["tax_efficiency"] = {
            "value": round(r, 3), "band": _band_te(r),
            "formula": f"₹{tax_paid} Cr / ₹{pbt} Cr PBT (proxy: NP + tax)",
        }
    else:
        out["tax_efficiency"] = {"value": None, "band": None, "formula": ""}

    return out


# ────────────────────────────────────────────────────────────────────────────
# Modifier table — (ratio, band) → list of (dimension, delta, template)
# Deltas on 0-100 scale. ±15 typical, ±25 for extreme distress.
# Templates use {value} and {pct_value} placeholders.
# ────────────────────────────────────────────────────────────────────────────

# Sectors where high gross margin reflects physical manufacturing value, not IP/software.
# The gross_margin → liability/ip_infringement modifier is a SaaS heuristic and must
# be skipped for these sectors.
_PHYSICAL_SECTORS = {
    "Manufacturing", "Logistics / Mobility", "D2C / Consumer Brands",
    "Agritech / Foodtech", "Cleantech / Climatetech",
}


def _dv(docs: dict, doc_type: str, field: str):
    """Safe value lookup from documents_extracted[doc_type][field]."""
    entry = (docs.get(doc_type) or {}).get(field) or {}
    return entry.get("value") if isinstance(entry, dict) else entry


_MODIFIERS: dict = {
    # net_profit_margin
    ("net_profit_margin", "burn_q1"): [
        ("key_person", +20, "Negative margin ({pct_value}) — burn/founder dependence elevates key person risk"),
        ("reputation", +10, "Loss-making — going-concern reputation drag"),
    ],
    ("net_profit_margin", "thin_q2"): [
        ("key_person", +10, "Thin margin ({pct_value}) — limited cushion against shocks"),
    ],
    ("net_profit_margin", "premium_q4"): [
        ("key_person", -10, "Strong margin ({pct_value}) — well-cushioned financial profile"),
        ("governance_fraud", -5, "Profitable — lower distress incentive for governance issues"),
    ],

    # gross_margin
    ("gross_margin", "high_q3"): [
        ("liability", +10, "High gross margin ({pct_value}) — services-heavy → PI/E&O exposure"),
        ("ip_infringement", +10, "High gross margin signals IP-dependent business model"),
    ],
    ("gross_margin", "premium_q4"): [
        ("liability", +15, "Premium gross margin ({pct_value}) — software/IP-heavy → significant PI exposure"),
        ("ip_infringement", +15, "Premium gross margin → IP is the primary value driver"),
    ],

    # debt_to_equity
    ("debt_to_equity", "leveraged_q3"): [
        ("governance_fraud", +15, "Elevated leverage (D/E={value}) — director/officer liability magnified"),
        ("tax_tp", +5, "Leveraged structure may indicate aggressive tax planning"),
    ],
    ("debt_to_equity", "highly_leveraged_q4"): [
        ("governance_fraud", +25, "High leverage (D/E={value}) — significant D&O and creditor liability"),
        ("key_person", +10, "Debt service pressure elevates founder/CEO stress"),
        ("reputation", +10, "High leverage signals stress in credit markets"),
    ],
    ("debt_to_equity", "distressed_negative_equity"): [
        ("governance_fraud", +25, "Negative equity — distressed balance sheet, extreme D&O exposure"),
        ("key_person", +15, "Negative equity puts going-concern pressure on leadership"),
        ("reputation", +15, "Negative equity is publicly visible distress signal"),
    ],

    # current_ratio_proxy
    ("current_ratio_proxy", "liquidity_stress_q1"): [
        ("governance_fraud", +10, "Current ratio {value} below 1.0 — liquidity stress, working capital strain"),
        ("key_person", +5, "Liquidity pressure elevates leadership stress"),
    ],

    # dso_days
    ("dso_days", "elevated_q3"): [
        ("governance_fraud", +10, "DSO {value} days — elevated trade credit / working capital fraud surface"),
    ],
    ("dso_days", "credit_risk_q4"): [
        ("governance_fraud", +15, "DSO {value} days — significant credit exposure, write-off risk"),
        ("reputation", +5, "Long collection cycles signal customer concentration or quality issues"),
    ],

    # asset_intensity
    ("asset_intensity", "asset_light_q1"): [
        ("property", -25, "Asset-light (PPE {pct_value} of assets) — property cover near-irrelevant"),
        ("cyber_technical", +5, "Asset-light + digital — cyber is the dominant exposure surface"),
    ],
    ("asset_intensity", "asset_heavy_q3"): [
        ("property", +15, "Asset-heavy (PPE {pct_value} of assets) — significant property exposure"),
        ("esg_climate", +10, "Physical infrastructure → climate physical risk exposure"),
    ],
    ("asset_intensity", "infrastructure_q4"): [
        ("property", +25, "Infrastructure-dense (PPE {pct_value} of assets) — major property/IAR cover required"),
        ("esg_climate", +15, "Heavy physical footprint → significant climate adaptation cost"),
    ],

    # payroll_intensity
    ("payroll_intensity", "lean_q1"): [
        ("gig_labour", +15, "Lean payroll ({pct_value} of revenue) — contractor/gig dependence likely"),
    ],
    ("payroll_intensity", "people_heavy_q3"): [
        ("cyber_technical", +10, "People-heavy ({pct_value} of revenue) — more endpoints, broader attack surface"),
    ],
    ("payroll_intensity", "labour_dominated_q4"): [
        ("cyber_technical", +15, "Labour-dominated ({pct_value} of revenue) — significant endpoint sprawl"),
        ("gig_labour", -10, "Heavy payroll → mostly W2 employees not contractors"),
    ],

    # tax_efficiency
    ("tax_efficiency", "aggressive_q1"): [
        ("tax_tp", +20, "Tax/PBT only {pct_value} — aggressive tax structuring suspected"),
        ("governance_fraud", +5, "Aggressive tax positions elevate scrutiny and director liability"),
    ],
    ("tax_efficiency", "high_q4"): [
        ("tax_tp", -5, "Tax/PBT {pct_value} — conservative tax positioning"),
    ],
}


def _scale_modifiers(extracts: dict) -> list:
    """Revenue-scale-based modifiers (special: absolute, not a ratio)."""
    rev = _v(extracts, "revenue_cr") or _v(extracts, "itr_revenue_cr")
    if rev is None:
        return []
    mods: list = []
    if rev > 500:
        mods.append(("cyber_technical", +15, f"Revenue ₹{rev:.0f} Cr — large attack surface, attractive target"))
        mods.append(("data_privacy", +10, f"Revenue ₹{rev:.0f} Cr — significant data volume"))
        mods.append(("regulatory_compliance", +10, f"Revenue ₹{rev:.0f} Cr — heightened regulatory scrutiny"))
    elif rev > 100:
        mods.append(("cyber_technical", +10, f"Revenue ₹{rev:.0f} Cr — meaningful target profile"))
        mods.append(("data_privacy", +5, f"Revenue ₹{rev:.0f} Cr — meaningful data footprint"))
        mods.append(("regulatory_compliance", +5, f"Revenue ₹{rev:.0f} Cr — elevated regulatory profile"))
    elif rev > 50:
        mods.append(("liability", +5, f"Revenue ₹{rev:.0f} Cr — moderate PI exposure"))
    return mods


def _document_modifiers(
    documents_extracted: dict,
    inferred_sector: Optional[str],
) -> list[tuple[str, int, str, str]]:
    """Derive risk-score modifiers from non-financial document signals.

    Returns list of (dim, delta, explanation, source_doc).
    All modifiers use internal dim keys.
    """
    mods: list[tuple[str, int, str, str]] = []
    if not documents_extracted:
        return mods

    # ── VAPT report → cyber_technical, data_privacy, regulatory_compliance ──
    vapt = documents_extracted.get("vapt_report") or {}

    def _vv(field):
        e = vapt.get(field) or {}
        return e.get("value") if isinstance(e, dict) else e

    critical = int(_vv("critical_count") or 0)
    high = int(_vv("high_count") or 0)
    mfa = _vv("mfa_enabled")
    edr = _vv("endpoint_protection_deployed")
    rto = _vv("backup_rto_hours")
    audit_age = _vv("audit_age_months")
    third_party = int(_vv("third_party_access_count") or 0)
    iso27001 = _vv("iso27001_or_soc2_active")

    if critical >= 4:
        mods.append(("cyber_technical", +20, f"{critical} critical CVEs — severe active exploit surface", "vapt_report"))
    elif critical >= 1:
        mods.append(("cyber_technical", +12, f"{critical} critical CVE(s) — significant unpatched vulnerabilities", "vapt_report"))
    if high >= 10:
        mods.append(("cyber_technical", +10, f"{high} high-severity CVEs — broad attack surface", "vapt_report"))
    elif high >= 5:
        mods.append(("cyber_technical", +5, f"{high} high-severity CVEs — elevated patch debt", "vapt_report"))
    if mfa is False:
        mods.append(("cyber_technical", +8, "No MFA on privileged accounts — credential theft vector", "vapt_report"))
        mods.append(("data_privacy", +5, "No MFA elevates data exfiltration risk", "vapt_report"))
    if edr is False:
        mods.append(("cyber_technical", +5, "No EDR/AV deployed — malware persistence risk", "vapt_report"))
    if rto is not None and float(rto) >= 72:
        mods.append(("cyber_technical", +5, f"Backup RTO {rto}h — slow recovery window from ransomware", "vapt_report"))
    if audit_age is not None and int(audit_age) >= 18:
        mods.append(("cyber_technical", +8, f"VAPT audit {audit_age} months old — current security posture unknown", "vapt_report"))
    if third_party >= 5:
        mods.append(("cyber_technical", +5, f"{third_party} third-party privileged access vectors", "vapt_report"))
    if iso27001 is False:
        mods.append(("regulatory_compliance", +5, "No ISO 27001/SOC 2 active — no external security assurance", "vapt_report"))

    # ── Asset register → property, esg_climate ──
    ar = documents_extracted.get("asset_register") or {}

    def _av(field):
        e = ar.get(field) or {}
        return e.get("value") if isinstance(e, dict) else e

    repl_vs_book = _av("replacement_vs_book_premium_pct")
    mach_age = _av("weighted_avg_age_machinery")
    oem = _av("oem_service_contracts")
    loc_count = _av("location_count")

    if repl_vs_book is not None and float(repl_vs_book) >= 0.30:
        pct = int(float(repl_vs_book) * 100)
        mods.append(("property", +10, f"Replacement value exceeds book by {pct}% — underinsurance risk", "asset_register"))
    if mach_age is not None:
        age = float(mach_age)
        if age >= 10:
            mods.append(("property", +8, f"Machinery avg age {age:.0f}yrs — elevated breakdown/maintenance risk", "asset_register"))
        elif age >= 5:
            mods.append(("property", +4, f"Machinery avg age {age:.0f}yrs — moderate wear risk", "asset_register"))
    if oem is False:
        mods.append(("property", +5, "No OEM service contracts — uncontracted equipment maintenance", "asset_register"))
    if loc_count is not None and int(loc_count) >= 5:
        mods.append(("esg_climate", +5, f"{loc_count} physical locations — broader climate exposure footprint", "asset_register"))

    # ── GST returns → reputation, geopolitical, governance_fraud ──
    gst = documents_extracted.get("gst_returns") or {}

    def _gv(field):
        e = gst.get(field) or {}
        return e.get("value") if isinstance(e, dict) else e

    b2b_conc = _gv("b2b_concentration_top3")
    export_share = _gv("export_share")
    has_us_uk = _gv("has_us_uk_export")
    late_filings = _gv("late_filings_4q")

    if b2b_conc is not None:
        conc = float(b2b_conc)
        if conc >= 0.80:
            mods.append(("reputation", +10, f"Top 3 customers = {conc*100:.0f}% of B2B revenue — dangerous concentration", "gst_returns"))
        elif conc >= 0.60:
            mods.append(("reputation", +5, f"Top 3 customers = {conc*100:.0f}% of B2B revenue — moderate concentration", "gst_returns"))
    if export_share is not None and float(export_share) >= 0.15:
        if has_us_uk:
            mods.append(("geopolitical", +10, f"{float(export_share)*100:.0f}% exports incl. US/UK — FX, sanctions, CBAM exposure", "gst_returns"))
        else:
            mods.append(("geopolitical", +6, f"{float(export_share)*100:.0f}% export revenue — cross-border risk", "gst_returns"))
    if late_filings is not None and int(late_filings) >= 2:
        mods.append(("governance_fraud", +10, f"{late_filings} late GST filings in 4 quarters — tax compliance weakness", "gst_returns"))
        mods.append(("regulatory_compliance", +8, f"{late_filings} late GST filings — regulatory process gaps", "gst_returns"))

    # ── Prior policy → property, cyber_technical, governance_fraud ──
    pp = documents_extracted.get("prior_policy") or {}

    def _pv(field):
        e = pp.get(field) or {}
        return e.get("value") if isinstance(e, dict) else e

    prop_claims = _pv("property_claims_3yr")
    cyber_claims = _pv("cyber_claims_3yr")
    do_claims = _pv("do_claims_3yr")
    prop_ncd = _pv("property_ncd_years")

    if prop_claims is not None and int(prop_claims) >= 1:
        mods.append(("property", +12, f"{prop_claims} property claim(s) in 3yr — confirmed loss history", "prior_policy"))
    if prop_ncd is not None and int(prop_ncd) == 0 and (prop_claims is None or int(prop_claims) == 0):
        mods.append(("property", +5, "Property NCD years = 0 — no claim-free discount earned", "prior_policy"))
    if cyber_claims is not None and int(cyber_claims) >= 1:
        mods.append(("cyber_technical", +15, f"{cyber_claims} cyber claim(s) in 3yr — breach history", "prior_policy"))
    if do_claims is not None and int(do_claims) >= 1:
        mods.append(("governance_fraud", +15, f"{do_claims} D&O claim(s) in 3yr — governance litigation history", "prior_policy"))

    return mods


def apply_modifiers(
    base_scores: dict,
    ratios: dict,
    extracts: dict,
    inferred_sector: Optional[str] = None,
    documents_extracted: Optional[dict] = None,
) -> tuple[dict, list]:
    """Apply ratio + scale + document modifiers to base scores.

    Accepts base_scores keyed either by internal name ("cyber_technical") or
    by display label ("Cyber Technical Risk"). Output preserves the input
    convention so it slots back into existing pipelines.

    Returns (modified_scores, reasons[]). Each reason: dict with dim (internal),
    modifier, ratio, ratio_value, band, explanation. Per-dim sums clip at ±25;
    final scores clip to [0, 100].
    """
    using_labels = any(k in _LABEL_TO_KEY for k in base_scores)
    internal_scores = _normalise_scores_to_internal(base_scores)
    deltas: dict[str, int] = {}
    reasons: list = []

    # Ratio-based modifiers
    for ratio_name, ratio_data in ratios.items():
        band = ratio_data.get("band")
        if not band:
            continue
        key = (ratio_name, band)
        if key not in _MODIFIERS:
            continue
        for dim, delta, template in _MODIFIERS[key]:
            # Skip gross_margin IP/liability modifiers for physical/manufacturing sectors:
            # high GM in manufacturing reflects precision margin, not software IP value.
            if (ratio_name == "gross_margin"
                    and dim in ("liability", "ip_infringement")
                    and inferred_sector in _PHYSICAL_SECTORS):
                continue
            value = ratio_data.get("value")
            try:
                pct_value = f"{value * 100:.0f}%" if value is not None and abs(value) < 10 else f"{value}"
            except (TypeError, ValueError):
                pct_value = str(value)
            explanation = template.format(value=value, pct_value=pct_value)
            deltas[dim] = deltas.get(dim, 0) + delta
            reasons.append({
                "dim": dim, "modifier": delta, "ratio": ratio_name,
                "ratio_value": value, "band": band, "explanation": explanation,
            })

    # Scale-based modifiers
    for dim, delta, explanation in _scale_modifiers(extracts):
        deltas[dim] = deltas.get(dim, 0) + delta
        reasons.append({
            "dim": dim, "modifier": delta, "ratio": "revenue_scale",
            "ratio_value": _v(extracts, "revenue_cr") or _v(extracts, "itr_revenue_cr"),
            "band": "scale", "explanation": explanation,
        })

    # Document-driven modifiers (VAPT, asset register, GST, prior policy)
    for dim, delta, explanation, source_doc in _document_modifiers(documents_extracted or {}, inferred_sector):
        deltas[dim] = deltas.get(dim, 0) + delta
        reasons.append({
            "dim": dim, "modifier": delta, "ratio": source_doc,
            "ratio_value": None, "band": "document", "explanation": explanation,
        })

    # Apply (clipped per-dim then clipped to [0,100])
    modified = dict(internal_scores)
    for dim, total_delta in deltas.items():
        if dim not in modified:
            continue
        clipped = max(-25, min(25, total_delta))
        modified[dim] = max(0, min(100, modified[dim] + clipped))

    if using_labels:
        modified = _denormalise_scores_to_labels(modified)
    return modified, reasons


# ────────────────────────────────────────────────────────────────────────────
# Sum Insured per cover (financial-derived)
# ────────────────────────────────────────────────────────────────────────────

def compute_si_from_financials(
    extracts: dict,
    documents_extracted: Optional[dict] = None,
    inferred_sector: Optional[str] = None,
) -> dict:
    """Calculate SI per cover from extracted financials + document signals. Returns INR rupees.

    Each cover entry: {si_inr, formula, triggered}. triggered=False → skip.
    Sanity guard: total SI > 3× revenue → proportional shrink + warning.

    documents_extracted: non-financial doc buckets (prior_policy, asset_register, vapt, gst).
    inferred_sector: used to pick correct Workers Comp formula for manufacturing.
    """
    rev = _v(extracts, "revenue_cr") or _v(extracts, "itr_revenue_cr") or 0
    equity = _v(extracts, "equity_cr") or 0
    total_assets = _v(extracts, "total_assets_cr") or 0
    ppe = _v(extracts, "fixed_assets_cr") or 0
    receivables = _v(extracts, "receivables_cr") or 0
    inventory = _v(extracts, "inventory_cr") or 0
    payroll = _v(extracts, "payroll_cr") or 0

    cogs = _v(extracts, "cogs_cr")
    gm = ((rev - cogs) / rev) if (rev > 0 and cogs is not None) else None
    docs = documents_extracted or {}

    out: dict = {}

    if rev > 0:
        si_cr = max(5, min(500, rev * 0.015))
        formula = f"1.5% × ₹{rev:.0f} Cr revenue, capped [₹5 Cr, ₹500 Cr]"
        # VAPT uplift: severe vulnerability posture requires higher cyber SI floor
        critical = int(_dv(docs, "vapt_report", "critical_count") or 0)
        if critical >= 3:
            new_floor = max(si_cr * 1.25, 10.0)
            if new_floor > si_cr:
                si_cr = min(500, new_floor)
                formula += f"; VAPT uplift ({critical} critical CVEs → ₹10 Cr floor)"
        out["Cyber Liability"] = {
            "si_inr": _cr_to_inr(si_cr),
            "formula": formula,
            "triggered": True,
        }

    if equity > 0:
        si_cr = max(5, min(250, equity * 0.10))
        out["D&O Liability"] = {
            "si_inr": _cr_to_inr(si_cr),
            "formula": f"10% × ₹{equity:.0f} Cr equity, capped [₹5 Cr, ₹250 Cr]",
            "triggered": True,
        }
    elif total_assets > 0:
        si_cr = max(5, min(250, total_assets * 0.05))
        out["D&O Liability"] = {
            "si_inr": _cr_to_inr(si_cr),
            "formula": f"5% × ₹{total_assets:.0f} Cr total assets (negative equity fallback)",
            "triggered": True,
        }

    if rev > 0:
        rate = 0.005 if (gm is not None and gm > 0.40) else 0.003
        si_cr = max(2, min(100, rev * rate))
        out["Professional Indemnity"] = {
            "si_inr": _cr_to_inr(si_cr),
            "formula": f"{rate*100:.1f}% × ₹{rev:.0f} Cr revenue (rate by gross margin), capped [₹2 Cr, ₹100 Cr]",
            "triggered": True,
        }

    if ppe > 0:
        # Single-insurer Property/Fire SI realistically capped at ₹500 Cr
        # (anything larger goes to reinsurance/syndicated cover).
        si_cr = min(500, max(1, ppe))
        formula = f"100% × ₹{ppe:.0f} Cr PPE (balance sheet)"
        if ppe > 500:
            formula += " (capped ₹500 Cr — larger PPE needs syndicated cover)"

        # Floor 1: asset register total replacement value (more accurate than book PPE)
        repl_cr = _dv(docs, "asset_register", "total_replacement_cr")
        if repl_cr is not None:
            try:
                repl_cr = float(repl_cr)
                if repl_cr > si_cr:
                    si_cr = min(500, repl_cr)
                    formula = f"₹{repl_cr:.1f} Cr asset register replacement value"
            except (TypeError, ValueError):
                pass

        # Floor 2: prior policy SI — prior underwriter already accepted this exposure level
        prior_si = _dv(docs, "prior_policy", "property_si")
        if prior_si is not None:
            try:
                prior_si = float(prior_si)
                if prior_si > si_cr:
                    si_cr = min(500, prior_si)
                    formula = f"₹{prior_si:.1f} Cr (prior IAR policy SI — do not underinsure)"
            except (TypeError, ValueError):
                pass

        out["Property / Fire"] = {
            "si_inr": _cr_to_inr(si_cr),
            "formula": formula,
            "triggered": True,
        }

    if receivables > 5:
        si_cr = max(5, min(500, receivables * 0.85))
        out["Trade Credit"] = {
            "si_inr": _cr_to_inr(si_cr),
            "formula": f"85% × ₹{receivables:.0f} Cr receivables, capped [₹5 Cr, ₹500 Cr]",
            "triggered": True,
        }

    if inventory > 1:
        si_cr = max(0.5, inventory * 1.2)
        formula = f"120% × ₹{inventory:.0f} Cr inventory"
        # GST export floor: annual export transit can exceed inventory held at any one time
        export_inv = _dv(docs, "gst_returns", "export_invoices_cr")
        if export_inv is not None:
            try:
                export_floor = float(export_inv) * 1.10
                if export_floor > si_cr:
                    si_cr = export_floor
                    formula += f"; raised to ₹{si_cr:.1f} Cr to cover GST export invoice volume"
            except (TypeError, ValueError):
                pass
        out["Marine Cargo"] = {
            "si_inr": _cr_to_inr(si_cr),
            "formula": formula,
            "triggered": True,
        }

    if payroll > 0:
        # Sliding per-head cost: small companies pay juniors ~₹6L, large IT
        # services pay ~₹18L average. Reflects loaded cost incl. benefits.
        if payroll < 10:
            cost_per_head_inr = 6_00_000
        elif payroll < 100:
            cost_per_head_inr = 8_00_000
        elif payroll < 1000:
            cost_per_head_inr = 12_00_000
        else:
            cost_per_head_inr = 18_00_000
        implied_headcount = max(1, int(payroll * 1_00_00_000 / cost_per_head_inr))
        # Group Health SI per single insurer typically capped at ₹500 Cr.
        si_cr = min(500, max(0.5, implied_headcount * 4_00_000 / 1_00_00_000))
        out["Group Health"] = {
            "si_inr": _cr_to_inr(si_cr),
            "formula": f"Est. {implied_headcount:,} employees × ₹4 L cover each "
                       f"(₹{cost_per_head_inr // 100000}L median per head), capped ₹500 Cr",
            "triggered": True,
            "implied_headcount": implied_headcount,
            "cost_per_head_inr": cost_per_head_inr,
        }

    if payroll > 0:
        # Workers Comp / EC SI formula depends on workforce type:
        # - Manufacturing/Physical-only: SI = 100% of payroll (employer covers full wage liability
        #   under WCA; blue-collar workers face higher accident/death risk)
        # - Digital/office: SI = 5% of payroll (actuarial statutory floor)
        is_physical_mfg = inferred_sector in _PHYSICAL_SECTORS or bool(
            _dv(docs, "asset_register", "weighted_avg_age_machinery")
        )
        if is_physical_mfg:
            si_cr = min(100, max(0.5, payroll))
            wc_formula = f"100% × ₹{payroll:.0f} Cr payroll (manufacturing/blue-collar EC floor), capped ₹100 Cr"
        else:
            si_cr = min(100, max(0.25, payroll * 0.05))
            wc_formula = f"5% × ₹{payroll:.0f} Cr payroll (statutory floor), capped ₹100 Cr"
        out["Workers Comp / WIBA"] = {
            "si_inr": _cr_to_inr(si_cr),
            "formula": wc_formula,
            "triggered": True,
        }

    if rev > 10:
        si_cr = max(1, min(50, rev * 0.001))
        out["Crime / Fidelity"] = {
            "si_inr": _cr_to_inr(si_cr),
            "formula": f"0.1% × ₹{rev:.0f} Cr revenue, capped [₹1 Cr, ₹50 Cr]",
            "triggered": True,
        }

    # Sanity: total SI should not exceed 3× revenue. Proportional shrink if so.
    if rev > 0:
        total_si_cr = sum(c["si_inr"] for c in out.values()) / 1_00_00_000
        if total_si_cr > rev * 3:
            shrink = (rev * 3) / total_si_cr
            for cover in out.values():
                cover["si_inr"] = int(cover["si_inr"] * shrink)
                cover["formula"] += f" [shrunk ×{shrink:.2f} to fit 3× revenue cap]"

    return out


# ────────────────────────────────────────────────────────────────────────────
# Risk loading per cover
# ────────────────────────────────────────────────────────────────────────────

_COVER_DIMS: dict[str, list[str]] = {
    "Cyber Liability":        ["cyber_technical", "data_privacy", "regulatory_compliance"],
    "D&O Liability":          ["governance_fraud", "regulatory_compliance", "key_person", "tax_tp"],
    "Professional Indemnity": ["liability", "ip_infringement"],
    "Property / Fire":        ["property", "esg_climate"],
    "Trade Credit":           ["governance_fraud", "reputation"],
    "Marine Cargo":           ["property", "geopolitical"],
    "Group Health":           [],  # community-rated
    "Workers Comp / WIBA":    ["gig_labour", "property", "liability"],
    "Crime / Fidelity":       ["governance_fraud"],
}


def compute_risk_loading(
    modified_scores: dict,
    documents_extracted: Optional[dict] = None,
) -> dict:
    """Per-cover loading multiplier in [0.85, 1.50].

    Accepts scores keyed by either internal name or display label.
    documents_extracted: used for VAPT-based cyber loading and prior-claims property loading.
    """
    internal = _normalise_scores_to_internal(modified_scores)
    docs = documents_extracted or {}
    out: dict = {}
    for cover, dims in _COVER_DIMS.items():
        if not dims:
            out[cover] = {"loading": 1.0, "formula": "Community-rated, no risk loading", "relevant_dims": []}
            continue
        loading = 1.0
        high = very_high = low = 0
        for d in dims:
            score = internal.get(d, 50)
            if score >= 90: very_high += 1
            elif score >= 70: high += 1
            elif score <= 30: low += 1
        loading += 0.05 * high + 0.10 * very_high - 0.05 * low
        loading = max(0.85, min(1.50, loading))

        base_formula = f"{high} dim(s)≥70 + {very_high} dim(s)≥90 − {low} dim(s)≤30, clipped [0.85, 1.50]"
        vapt_adj = 0.0
        claims_adj = 0.0

        # VAPT override for Cyber Liability — score-based loading can understate risk
        # when VAPT signals critical vulnerabilities (e.g., no MFA + 4 criticals → discount).
        if cover == "Cyber Liability" and docs:
            critical = int(_dv(docs, "vapt_report", "critical_count") or 0)
            high_vuln = int(_dv(docs, "vapt_report", "high_count") or 0)
            mfa = _dv(docs, "vapt_report", "mfa_enabled")
            edr = _dv(docs, "vapt_report", "endpoint_protection_deployed")
            if critical >= 4:
                vapt_adj += 0.20
            elif critical >= 1:
                vapt_adj += 0.10
            if high_vuln >= 10:
                vapt_adj += 0.10
            elif high_vuln >= 5:
                vapt_adj += 0.05
            if mfa is False:
                vapt_adj += 0.05
            if edr is False:
                vapt_adj += 0.05
            loading = max(0.85, min(1.50, loading + vapt_adj))

        # Prior claims override for Property / Fire
        if cover == "Property / Fire" and docs:
            prop_claims = _dv(docs, "prior_policy", "property_claims_3yr")
            if prop_claims is not None:
                claims_adj = round(0.10 * int(prop_claims), 3)
                loading = max(0.85, min(1.50, loading + claims_adj))

        out[cover] = {
            "loading": round(loading, 3),
            "formula": base_formula,
            "relevant_dims": dims,
            **({"vapt_adjustment": round(vapt_adj, 3)} if vapt_adj else {}),
            **({"claims_adjustment": claims_adj} if claims_adj else {}),
        }
    return out


# ────────────────────────────────────────────────────────────────────────────
# Confidence band
# ────────────────────────────────────────────────────────────────────────────

_VERIFY_WEIGHTS = {
    "revenue_cr": 12,
    "equity_cr": 10,
    "payroll_cr": 8,
    "fixed_assets_cr": 5,
    "receivables_cr": 5,
}


def compute_confidence_band(extracts: dict) -> dict:
    """Premium confidence band width and verification level."""
    width = 50
    verified: list = []
    for field, weight in _VERIFY_WEIGHTS.items():
        if _v(extracts, field) is not None:
            width -= weight
            verified.append(field)
    width = max(12, width)

    if width <= 15: level = "fully_verified"
    elif width <= 30: level = "well_documented"
    elif width <= 45: level = "partially_verified"
    else: level = "estimated"

    return {
        "width_pct": width,
        "plus_minus_pct": width // 2,
        "verification_level": level,
        "verified_inputs": verified,
    }


# ────────────────────────────────────────────────────────────────────────────
# Per-cover confidence (document-driven)
# ────────────────────────────────────────────────────────────────────────────

_MIN_BAND_PCT = 8
_FLOOR_FIELD_SHARE = 0.5  # need at least 50% of fields_used present to claim doc-provided


def _doc_field_completeness(extracted_docs: dict, doc_type: str, fields_used: list) -> float:
    """Return share of `fields_used` actually present (non-None) in extracted_docs[doc_type]."""
    bucket = (extracted_docs or {}).get(doc_type) or {}
    if not bucket or not fields_used:
        return 0.0
    present = 0
    for field in fields_used:
        entry = bucket.get(field)
        if isinstance(entry, dict) and entry.get("value") is not None:
            present += 1
        elif entry is not None and not isinstance(entry, dict):
            present += 1
    return present / len(fields_used)


def _mca_field_completeness(mca_snapshot: dict, fields_used: list) -> float:
    if not mca_snapshot or not fields_used:
        return 0.0
    present = 0
    for field in fields_used:
        if mca_snapshot.get(field) is not None:
            present += 1
        elif (mca_snapshot.get("latest_aoc4") or {}).get(field) is not None:
            present += 1
    return present / len(fields_used)


def _band_level(width_pct: float) -> str:
    if width_pct <= 15: return "fully_verified"
    if width_pct <= 25: return "well_documented"
    if width_pct <= 40: return "partially_verified"
    return "estimated"


def compute_per_cover_confidence(
    extracted_docs: dict,
    mca_snapshot: dict,
    affinity_matrix: dict,
) -> dict:
    """Per-cover confidence band + ordered list of documents that would narrow it most.

    affinity_matrix shape: see pricing/cover_document_affinity.json
    """
    covers_cfg = (affinity_matrix or {}).get("covers", {}) or {}
    out: dict = {}
    mca_present = bool(mca_snapshot and mca_snapshot.get("source") not in (None, "unavailable"))

    for cover_key, cfg in covers_cfg.items():
        base = float(cfg.get("base_band_pct", 50))
        width = base
        narrowed_by: list = []
        upload_next_candidates: list = []

        for doc_type, doc_cfg in (cfg.get("documents") or {}).items():
            narrow_pct = float(doc_cfg.get("narrow_pct", 0))
            fields_used = doc_cfg.get("fields_used") or []
            if doc_type == "mca_filings":
                share = _mca_field_completeness(mca_snapshot, fields_used) if mca_present else 0.0
            else:
                share = _doc_field_completeness(extracted_docs, doc_type, fields_used)
                # If doc was uploaded but fields are sparse (regex limitations),
                # give a minimum 40% presence credit so the doc counts toward narrowing.
                if share < _FLOOR_FIELD_SHARE and doc_type in (extracted_docs or {}):
                    share = _FLOOR_FIELD_SHARE  # doc uploaded → minimum pass credit

            if share >= _FLOOR_FIELD_SHARE:
                # Discount narrow_pct by share so partial extraction is honestly weighted
                effective = narrow_pct * share
                width -= effective
                narrowed_by.append({
                    "doc_type": doc_type,
                    "narrow_pct": round(effective, 2),
                    "field_completeness": round(share, 2),
                })
            else:
                upload_next_candidates.append({
                    "doc_type": doc_type,
                    "narrow_pct": narrow_pct,
                    "would_become": max(_MIN_BAND_PCT, round(width - narrow_pct, 2)),
                })

        width = max(_MIN_BAND_PCT, round(width, 2))
        upload_next = sorted(upload_next_candidates, key=lambda x: x["narrow_pct"], reverse=True)[:2]
        out[cover_key] = {
            "width_pct": width,
            "plus_minus_pct": round(width / 2, 2),
            "level": _band_level(width),
            "narrowed_by": narrowed_by,
            "upload_next": upload_next,
        }
    return out


def rank_global_upload_next(
    per_cover_confidence: dict,
    affinity_matrix: dict,
    top_n: int = 3,
) -> list[dict]:
    """Rank unprovided documents by total narrowing impact across all covers.

    Returns a list of {doc_type, covers_impacted, total_narrowing_pct, biggest_impact_cover}.
    """
    covers_cfg = (affinity_matrix or {}).get("covers", {}) or {}
    # Map: doc_type -> {covers: [(cover_key, narrow_pct)], total}
    aggregate: dict[str, dict] = {}
    for cover_key, cover_cfg in covers_cfg.items():
        per_cover = per_cover_confidence.get(cover_key) or {}
        next_docs = {d["doc_type"]: d for d in (per_cover.get("upload_next") or [])}
        # Also consider any doc not in narrowed_by even if it didn't make top-2
        narrowed_set = {n["doc_type"] for n in (per_cover.get("narrowed_by") or [])}
        for doc_type, doc_cfg in (cover_cfg.get("documents") or {}).items():
            if doc_type in narrowed_set:
                continue  # already provided
            narrow_pct = float(doc_cfg.get("narrow_pct", 0))
            ag = aggregate.setdefault(doc_type, {"covers": [], "total": 0.0})
            ag["covers"].append((cover_key, narrow_pct))
            ag["total"] += narrow_pct

    ranked: list[dict] = []
    for doc_type, info in aggregate.items():
        info["covers"].sort(key=lambda x: x[1], reverse=True)
        biggest = info["covers"][0] if info["covers"] else (None, 0)
        ranked.append({
            "doc_type": doc_type,
            "covers_impacted": len(info["covers"]),
            "total_narrowing_pct": round(info["total"], 2),
            "biggest_impact_cover": biggest[0],
            "biggest_impact_pct": round(biggest[1], 2),
        })
    ranked.sort(key=lambda x: x["total_narrowing_pct"], reverse=True)
    return ranked[:top_n]


# ────────────────────────────────────────────────────────────────────────────
# Data quality warnings
# ────────────────────────────────────────────────────────────────────────────

def detect_data_quality_warnings(
    extracts: dict,
    ratios: dict,
    inferred_sector: Optional[str] = None,
) -> list:
    """Flag inconsistencies the RM should see before trusting the assessment."""
    warnings: list = []

    # Sector vs asset intensity contradiction
    ai = ratios.get("asset_intensity", {}).get("value")
    if inferred_sector and ai is not None:
        ai_pct = ai * 100
        sl = inferred_sector.lower()
        if any(k in sl for k in ("saas", "software", "fintech")) and ai_pct > 25:
            warnings.append({
                "type": "sector_inconsistency",
                "severity": "warning",
                "message": f"Inferred sector '{inferred_sector}' but PPE/assets = {ai_pct:.0f}% — "
                           f"typical {inferred_sector} <10%. Verify sector classification.",
            })
        if any(k in sl for k in ("manufacturing", "logistics", "infrastructure")) and ai_pct < 15:
            warnings.append({
                "type": "sector_inconsistency",
                "severity": "warning",
                "message": f"Inferred sector '{inferred_sector}' but PPE/assets = {ai_pct:.0f}% — "
                           f"typical {inferred_sector} >30%. Verify sector or check for leased assets.",
            })

    # Negative equity
    eq = _v(extracts, "equity_cr")
    if eq is not None and eq <= 0:
        warnings.append({
            "type": "distressed_balance_sheet",
            "severity": "critical",
            "message": f"Negative equity (₹{eq:.0f} Cr) — distressed balance sheet. "
                       f"D&O premium and underwriting likely require referral.",
        })

    # Loss-making
    np = _v(extracts, "net_profit_cr") or _v(extracts, "profit_cr")
    if np is not None and np < 0:
        warnings.append({
            "type": "loss_making",
            "severity": "info",
            "message": f"Net loss ₹{np:.0f} Cr — going concern review recommended.",
        })

    # Pathological DSO
    dso = ratios.get("dso_days", {}).get("value")
    if dso is not None and dso > 365:
        warnings.append({
            "type": "extreme_dso",
            "severity": "warning",
            "message": f"DSO {dso:.0f} days exceeds 1 year — likely data error or "
                       f"significant collection issues. Verify receivables figure.",
        })

    # Balance sheet identity check (Assets ≈ Liabilities + Equity)
    ta = _v(extracts, "total_assets_cr")
    tl = _v(extracts, "total_liabilities_cr")
    eq2 = _v(extracts, "equity_cr")
    if ta and tl and eq2:
        gap = abs(ta - (tl + eq2))
        if gap > max(5, ta * 0.05):
            warnings.append({
                "type": "balance_sheet_imbalance",
                "severity": "warning",
                "message": f"Assets ₹{ta:.0f} Cr ≠ Liabilities ₹{tl:.0f} + Equity ₹{eq2:.0f} "
                           f"(gap ₹{gap:.0f} Cr). Extraction may have missed line items.",
            })

    return warnings


# ────────────────────────────────────────────────────────────────────────────
# Orchestrator
# ────────────────────────────────────────────────────────────────────────────

def verified_assessment(
    extracts: dict,
    base_scores: dict,
    inferred_sector: Optional[str] = None,
    documents_extracted: Optional[dict] = None,
) -> dict:
    """Full pipeline: ratios → modifiers → SI → loading → band → warnings.

    documents_extracted: non-financial doc buckets (vapt_report, asset_register,
    gst_returns, prior_policy, client_contract) — used in every sub-function.
    """
    ratios = compute_ratios(extracts)
    modified_scores, reasons = apply_modifiers(
        base_scores, ratios, extracts,
        inferred_sector=inferred_sector,
        documents_extracted=documents_extracted,
    )
    si = compute_si_from_financials(
        extracts,
        documents_extracted=documents_extracted,
        inferred_sector=inferred_sector,
    )
    loading = compute_risk_loading(modified_scores, documents_extracted=documents_extracted)
    band = compute_confidence_band(extracts)
    warnings = detect_data_quality_warnings(extracts, ratios, inferred_sector)

    scored = score(extracts, inferred_sector, funding_stage=None, documents_extracted=documents_extracted)
    composite = _composite_risk_score(modified_scores, base_scores, documents_extracted)
    return {
        "ratios": ratios,
        "base_scores": base_scores,
        "modified_scores": modified_scores,
        "modifier_reasons": reasons,
        "sum_insured_per_cover": si,
        "risk_loading_per_cover": loading,
        "confidence_band": band,
        "data_quality_warnings": warnings,
        "score_breakdown": scored,
        "composite_score": composite,
    }


# ────────────────────────────────────────────────────────────────────────────
# Composite risk score (0–100)
# ────────────────────────────────────────────────────────────────────────────

_WEIGHTS: dict[str, float] = {
    "cyber_technical":       0.15,
    "data_privacy":          0.12,
    "liability":             0.12,
    "governance_fraud":      0.12,
    "regulatory_compliance": 0.10,
    "key_person":            0.08,
    "property":              0.08,
    "ip_infringement":       0.06,
    "gig_labour":            0.06,
    "esg_climate":           0.04,
    "geopolitical":          0.04,
    "policy_velocity":       0.02,
    "reputation":            0.01,
}

_UNCERTAINTY_DOCS: dict[str, int] = {
    "vapt_report":     8,
    "client_contract": 6,
    "asset_register":  5,
    "mca":             4,
    "gst_returns":     3,
}

_LABEL_BANDS: list[tuple[int, str]] = [
    (85, "Critical"),
    (70, "High"),
    (50, "Elevated"),
    (30, "Moderate"),
    (0,  "Low"),
]


def _composite_risk_score(
    modified_scores: dict,
    base_scores: Optional[dict] = None,
    documents_extracted: Optional[dict] = None,
) -> dict:
    """Weighted composite risk score from 13 modified dimension scores.

    Returns None for value when modified_scores is empty — never defaults to 50.
    """
    internal = _normalise_scores_to_internal(modified_scores or {})
    if not internal:
        return {
            "value": None, "label": None, "drivers": [],
            "dimension_scores": {}, "base_scores": {},
            "uncertainty_pts": _uncertainty_pts(documents_extracted),
        }

    weighted_sum = 0.0
    contributions: list[tuple[str, float]] = []
    for dim, weight in _WEIGHTS.items():
        s = internal.get(dim, 0.0)
        contrib = weight * s
        weighted_sum += contrib
        contributions.append((dim, contrib))

    value = int(round(max(0.0, min(100.0, weighted_sum))))

    label = "Low"
    for threshold, lbl in _LABEL_BANDS:
        if value >= threshold:
            label = lbl
            break

    contributions.sort(key=lambda x: x[1], reverse=True)
    drivers = [dim for dim, _ in contributions[:3]]

    internal_base = _normalise_scores_to_internal(base_scores or {})

    return {
        "value": value,
        "label": label,
        "drivers": drivers,
        "dimension_scores": internal,
        "base_scores": internal_base,
        "uncertainty_pts": _uncertainty_pts(documents_extracted),
    }


def _uncertainty_pts(documents_extracted: Optional[dict]) -> int:
    docs = documents_extracted or {}
    pts = sum(v for k, v in _UNCERTAINTY_DOCS.items() if k not in docs or not docs[k])
    return min(25, pts)


# ────────────────────────────────────────────────────────────────────────────
# Two-tier scoring API
# ────────────────────────────────────────────────────────────────────────────

_RATIO_REQUIRED_FIELDS: dict[str, list[str]] = {
    "net_profit_margin":   ["revenue_cr", "net_profit_cr"],
    "gross_margin":        ["revenue_cr", "cogs_cr"],
    "debt_to_equity":      ["equity_cr"],
    "current_ratio_proxy": ["current_assets_cr", "total_liabilities_cr"],
    "dso_days":            ["revenue_cr", "receivables_cr"],
    "asset_intensity":     ["total_assets_cr", "fixed_assets_cr"],
    "payroll_intensity":   ["revenue_cr", "payroll_cr"],
    "tax_efficiency":      ["tax_paid_cr", "net_profit_cr"],
}


def _tier1_modifiers_list(
    ratios: dict,
    extracts: dict,
    sector: Optional[str],
) -> tuple[list[dict], list[str]]:
    """Return (modifiers, data_gaps) for Tier 1 (financial ratios + revenue scale).

    Each modifier: {dim, delta, explanation, source_field, confidence}
    data_gaps: human-readable strings for every skipped ratio.
    confidence per modifier = fraction of the 8 ratios that were computable.
    """
    computable = sum(1 for r in ratios.values() if r.get("value") is not None)
    total = len(_RATIO_REQUIRED_FIELDS)
    ratio_confidence = round(computable / total, 3) if total else 0.0

    mods: list[dict] = []
    data_gaps: list[str] = []

    for ratio_name, ratio_data in ratios.items():
        band = ratio_data.get("band")
        if not band:
            required = _RATIO_REQUIRED_FIELDS.get(ratio_name, [])
            missing = [f for f in required if _v(extracts, f) is None]
            if missing:
                data_gaps.append(
                    f"{ratio_name} not computable — {', '.join(missing)} missing"
                )
            continue
        key = (ratio_name, band)
        if key not in _MODIFIERS:
            continue
        for dim, delta, template in _MODIFIERS[key]:
            if (ratio_name == "gross_margin"
                    and dim in ("liability", "ip_infringement")
                    and sector in _PHYSICAL_SECTORS):
                continue
            value = ratio_data.get("value")
            try:
                pct_value = (
                    f"{value * 100:.0f}%"
                    if value is not None and abs(value) < 10
                    else f"{value}"
                )
            except (TypeError, ValueError):
                pct_value = str(value)
            mods.append({
                "dim": dim,
                "delta": delta,
                "explanation": template.format(value=value, pct_value=pct_value),
                "source_field": ratio_name,
                "confidence": ratio_confidence,
            })

    # Revenue-scale modifiers (not ratio-based, but still Tier 1)
    rev = _v(extracts, "revenue_cr") or _v(extracts, "itr_revenue_cr")
    for dim, delta, explanation in _scale_modifiers(extracts):
        mods.append({
            "dim": dim,
            "delta": delta,
            "explanation": explanation,
            "source_field": "revenue_cr" if _v(extracts, "revenue_cr") is not None else "itr_revenue_cr",
            "confidence": 1.0,
        })
    if rev is None:
        data_gaps.append("revenue_scale not computable — revenue_cr and itr_revenue_cr both missing")

    return mods, data_gaps


def _tier2_modifiers_list(
    documents_extracted: dict,
    sector: Optional[str],
) -> tuple[list[dict], float]:
    """Return (modifiers, confidence) for Tier 2 (non-financial documents).

    confidence = fraction of supplied document types that contributed at least one modifier.
    """
    if not documents_extracted:
        return [], 0.0

    raw = _document_modifiers(documents_extracted, sector)
    mods = [
        {
            "dim": dim,
            "delta": delta,
            "explanation": explanation,
            "source_field": source_doc,
            "confidence": 1.0,
        }
        for dim, delta, explanation, source_doc in raw
    ]

    supplied = {k for k, v in documents_extracted.items() if v}
    contributing = {m["source_field"] for m in mods}
    confidence = round(len(contributing & supplied) / len(supplied), 3) if supplied else 0.0
    return mods, confidence


def score(
    extraction_summary: dict,
    sector: Optional[str],
    funding_stage: Optional[str],
    documents_extracted: Optional[dict] = None,
) -> dict:
    """Two-tier financial risk scoring.

    Tier 1 — always runs when any financial data is present:
      Computes ratios from extraction_summary. Skips cleanly when fields are
      missing — never imputes defaults, never errors.

    Tier 2 — runs additionally when documents_extracted is supplied:
      VAPT, contracts, asset register, GST, prior policy modifiers.

    Returns:
      tier1_modifiers, tier2_modifiers, combined_modifiers,
      data_gaps, tier1_confidence, tier2_confidence, ratios
    """
    ratios = compute_ratios(extraction_summary)

    t1_mods, data_gaps = _tier1_modifiers_list(ratios, extraction_summary, sector)

    computable = sum(1 for r in ratios.values() if r.get("value") is not None)
    tier1_confidence = round(computable / len(_RATIO_REQUIRED_FIELDS), 3)

    t2_mods, tier2_confidence = _tier2_modifiers_list(documents_extracted or {}, sector)

    return {
        "tier1_modifiers": t1_mods,
        "tier2_modifiers": t2_mods,
        "combined_modifiers": t1_mods + t2_mods,
        "data_gaps": data_gaps,
        "tier1_confidence": tier1_confidence,
        "tier2_confidence": tier2_confidence,
        "ratios": ratios,
    }
