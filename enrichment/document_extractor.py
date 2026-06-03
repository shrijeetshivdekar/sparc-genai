"""Regex-based field extraction from PDF text.

Input is plain text already extracted in the browser by PDF.js. Output is a
dict keyed by canonical field name, with values shaped as:
    {"value": float, "confidence": "extracted"|"calculated"|"not_found", "source": str}

All amounts normalised to INR crore (Cr). Lakh-denominated values are
converted (1 Cr = 100 lakh). Currency symbols and commas tolerated.
"""

from __future__ import annotations

import re
from typing import Dict, Tuple


# Number with unit suffix (cr / lakh).
_NUM = r"[₹$Rs.\s]*([\d,]+(?:\.\d+)?)\s*(cr(?:ore)?|lakh?|lac)\b"

# Bare rupee amount — no unit suffix (e.g. ₹18,20,00,000 or Rs. 4,80,00,000).
# Groups: (digits_with_commas). Unit inferred from magnitude.
_NUM_RAW = r"[₹][ ]?([\d,]{5,}(?:\.\d+)?)"


def _to_cr(value_str: str, unit: str) -> float:
    """Normalise a captured (number, unit) to crore (INR)."""
    n = float(value_str.replace(",", ""))
    u = unit.lower()
    if u.startswith("lakh") or u.startswith("lac") or u.startswith("lak"):
        return round(n / 100.0, 2)
    return round(n, 2)


def _raw_to_cr(value_str: str) -> float:
    """Convert a bare rupee integer string to crore by magnitude."""
    n = float(value_str.replace(",", ""))
    if n >= 1_00_00_000:        # ≥ 1 Cr — already in rupees
        return round(n / 1_00_00_000, 2)
    if n >= 1_00_000:           # ≥ 1 Lakh — treat as lakh
        return round(n / 1_00_00_000, 2)
    return round(n, 2)           # small number — assume already crore


def _first_match(text: str, patterns: list[str]) -> Tuple[float | None, str | None]:
    """Try patterns in order; return (value_cr, matched_pattern) on first hit.

    Patterns may use _NUM (requires unit suffix) or _NUM_RAW (bare rupee amount).
    """
    for pat in patterns:
        m = re.search(pat, text, flags=re.IGNORECASE | re.MULTILINE)
        if m:
            if m.lastindex == 2:
                return _to_cr(m.group(1), m.group(2)), pat
            else:
                return _raw_to_cr(m.group(1)), pat
    return None, None


def detect_type(filename: str, text: str) -> str:
    """Heuristic doc-type detection from filename + first ~4000 chars of text.

    Returns one of: "pl" | "balance_sheet" | "itr" | "annual_report" |
    "gst_returns" | "prior_policy" | "client_contract" | "asset_register" |
    "vapt_report" | "unknown".
    """
    name = (filename or "").lower()
    head = (text or "")[:4000].lower()

    # Filename-first.
    if any(k in name for k in ("gstr", "gst_return", "gst-return")):
        return "gst_returns"
    if any(k in name for k in ("vapt", "pentest", "security_audit", "soc2", "iso27001")):
        return "vapt_report"
    if any(k in name for k in ("asset_register", "asset-register", "fixed_assets", "asset_list")):
        return "asset_register"
    if any(k in name for k in ("msa", "sow", "contract", "agreement")):
        return "client_contract"
    if any(k in name for k in ("policy_schedule", "insurance_policy", "policy_doc", "_policy")):
        return "prior_policy"
    if any(k in name for k in ("itr", "income_tax", "income-tax")):
        return "itr"
    if any(k in name for k in ("balance", "bs_", "_bs", "bsheet")):
        return "balance_sheet"
    if any(k in name for k in ("p&l", "pnl", "p_l", "profit", "income_statement")):
        return "pl"
    if "financial" in name and any(k in name for k in ("statement", "consolidated", "standalone")):
        return "annual_report"

    # Content fallback.
    if "gstin" in head and ("gstr-1" in head or "gstr-3b" in head or "gstr1" in head or "outward supplies" in head):
        return "gst_returns"
    if "vulnerability" in head and ("cvss" in head or "penetration test" in head or "vapt" in head):
        return "vapt_report"
    if "asset register" in head or ("fixed assets" in head and "depreciation" in head and "wdv" in head):
        return "asset_register"
    if ("master services agreement" in head or "this agreement" in head) and ("indemnify" in head or "liability" in head):
        return "client_contract"
    if "policy schedule" in head or ("sum insured" in head and "premium" in head and "policy number" in head):
        return "prior_policy"
    if "income tax return" in head or "assessment year" in head:
        return "itr"
    if "profit and loss" in head or "statement of profit" in head:
        return "pl"
    if "balance sheet" in head:
        return "balance_sheet"
    if "total assets" in head and "total liabilities" in head:
        return "balance_sheet"
    if "assets" in head and "liabilities" in head and "equity" in head:
        return "balance_sheet"

    return "unknown"


def extract_pl_fields(text: str) -> Dict[str, dict]:
    """Extract P&L line items as INR crore."""
    out: Dict[str, dict] = {}

    revenue_pats = [
        rf"(?:Revenue from operations|Total revenue|Sales|Turnover|Income from operations){_NUM}",
        rf"(?:Revenue from operations|Total revenue|Sales|Turnover|Income from operations)[:\s]+{_NUM_RAW}",
    ]
    cogs_pats = [
        rf"(?:Cost of goods sold|Cost of materials consumed|Cost of revenue|COGS){_NUM}",
        rf"(?:Cost of goods sold|Cost of materials consumed|Cost of revenue|COGS)[:\s]+{_NUM_RAW}",
    ]
    profit_pats = [
        rf"(?:Gross profit|Gross margin){_NUM}",
        rf"(?:Gross profit|Gross margin)[:\s]+{_NUM_RAW}",
    ]
    ebitda_pats = [
        rf"(?:EBITDA|Operating profit before depreciation){_NUM}",
        rf"(?:EBITDA|Operating profit before depreciation)[:\s]+{_NUM_RAW}",
    ]
    net_pats = [
        rf"(?:Net profit|Profit for the (?:year|period)|Profit after tax|PAT){_NUM}",
        rf"(?:Net profit|Profit for the (?:year|period)|Profit after tax|PAT)[:\s]+[-−]?{_NUM_RAW}",
    ]
    payroll_pats = [
        rf"(?:Employee benefit expenses?|Employee costs?|Personnel expenses?|Salaries(?: and wages)?){_NUM}",
        rf"(?:Employee benefit expenses?|Employee costs?|Personnel expenses?|Salaries(?: and wages)?)[:\s]+{_NUM_RAW}",
    ]

    for key, pats, src in [
        ("revenue_cr", revenue_pats, "P&L - Revenue"),
        ("cogs_cr", cogs_pats, "P&L - COGS"),
        ("gross_profit_cr", profit_pats, "P&L - Gross Profit"),
        ("ebitda_cr", ebitda_pats, "P&L - EBITDA"),
        ("net_profit_cr", net_pats, "P&L - Net Profit"),
        ("payroll_cr", payroll_pats, "P&L - Employee Benefit Expenses"),
    ]:
        val, _ = _first_match(text, pats)
        out[key] = (
            {"value": val, "confidence": "extracted", "source": src}
            if val is not None
            else {"value": None, "confidence": "not_found", "source": src}
        )

    # Derived: Gross Profit = Revenue - COGS, if both present and direct not found.
    if out["gross_profit_cr"]["value"] is None:
        rev = out["revenue_cr"]["value"]
        cogs = out["cogs_cr"]["value"]
        if rev is not None and cogs is not None:
            out["gross_profit_cr"] = {
                "value": round(rev - cogs, 2),
                "confidence": "calculated",
                "source": "P&L - Revenue minus COGS",
            }

    return out


def extract_bs_fields(text: str) -> Dict[str, dict]:
    """Extract Balance Sheet line items as INR crore."""
    out: Dict[str, dict] = {}

    assets_pats = [
        rf"(?:Total assets|TOTAL ASSETS){_NUM}",
        rf"(?:Total assets|TOTAL ASSETS)[:\s]+{_NUM_RAW}",
    ]
    fixed_assets_pats = [
        rf"(?:Property,? plant and equipment|Fixed assets|Tangible assets){_NUM}",
        rf"(?:Property,? plant and equipment|Fixed assets|Tangible assets)[:\s]+{_NUM_RAW}",
    ]
    current_assets_pats = [
        rf"(?:Total current assets|Current assets){_NUM}",
        rf"(?:Total current assets|Current assets)[:\s]+{_NUM_RAW}",
    ]
    inventory_pats = [
        rf"(?:Inventories|Inventory){_NUM}",
        rf"(?:Inventories|Inventory)[:\s]+{_NUM_RAW}",
    ]
    receivables_pats = [
        rf"(?:Trade receivables|Accounts receivable|Sundry debtors){_NUM}",
        rf"(?:Trade receivables|Accounts receivable|Sundry debtors)[:\s]+{_NUM_RAW}",
    ]
    liabilities_pats = [
        rf"(?:Total liabilities|TOTAL LIABILITIES){_NUM}",
        rf"(?:Total liabilities|TOTAL LIABILITIES)[:\s]+{_NUM_RAW}",
    ]
    equity_pats = [
        rf"(?:Total equity|Shareholders'? funds|Equity attributable to (?:shareholders|owners)){_NUM}",
        rf"(?:Total equity|Shareholders'? funds|Net worth|Equity)[:\s]+[-−]?{_NUM_RAW}",
    ]
    debt_pats = [
        rf"(?:Total borrowings|Long[- ]term borrowings|Total debt){_NUM}",
        rf"(?:Total borrowings|Long[- ]term borrowings|Total debt|Term loan)[:\s]+{_NUM_RAW}",
    ]

    for key, pats, src in [
        ("total_assets_cr", assets_pats, "Balance Sheet - Total Assets"),
        ("fixed_assets_cr", fixed_assets_pats, "Balance Sheet - PPE / Fixed Assets"),
        ("current_assets_cr", current_assets_pats, "Balance Sheet - Current Assets"),
        ("inventory_cr", inventory_pats, "Balance Sheet - Inventories"),
        ("receivables_cr", receivables_pats, "Balance Sheet - Trade Receivables"),
        ("total_liabilities_cr", liabilities_pats, "Balance Sheet - Total Liabilities"),
        ("equity_cr", equity_pats, "Balance Sheet - Equity"),
        ("debt_cr", debt_pats, "Balance Sheet - Borrowings"),
    ]:
        val, _ = _first_match(text, pats)
        out[key] = (
            {"value": val, "confidence": "extracted", "source": src}
            if val is not None
            else {"value": None, "confidence": "not_found", "source": src}
        )

    # Equity = Assets - Liabilities, if both present and equity not directly found.
    if out["equity_cr"]["value"] is None:
        a = out["total_assets_cr"]["value"]
        l = out["total_liabilities_cr"]["value"]
        if a is not None and l is not None:
            out["equity_cr"] = {
                "value": round(a - l, 2),
                "confidence": "calculated",
                "source": "Balance Sheet - Assets minus Liabilities",
            }

    return out


def extract_itr_fields(text: str) -> Dict[str, dict]:
    """Extract ITR line items as INR crore."""
    out: Dict[str, dict] = {}

    revenue_pats = [
        rf"(?:Gross turnover|Gross receipts|Total turnover|Revenue from operations){_NUM}",
    ]
    profit_pats = [
        rf"(?:Profit before tax|Net profit before tax|PBT){_NUM}",
    ]
    tax_pats = [
        rf"(?:Advance tax (?:paid|deposited)|Total taxes paid){_NUM}",
    ]

    for key, pats, src in [
        ("revenue_cr", revenue_pats, "ITR - Gross Turnover"),
        ("profit_cr", profit_pats, "ITR - Profit Before Tax"),
        ("tax_paid_cr", tax_pats, "ITR - Advance Tax Paid"),
    ]:
        val, _ = _first_match(text, pats)
        out[key] = (
            {"value": val, "confidence": "extracted", "source": src}
            if val is not None
            else {"value": None, "confidence": "not_found", "source": src}
        )

    return out


def _found(value, src: str) -> dict:
    return {"value": value, "confidence": "extracted" if value is not None else "not_found", "source": src}


def extract_gst_fields(text: str) -> Dict[str, dict]:
    """GSTR-1 / GSTR-3B field extraction.

    Returns aggregated counters needed by the doc-modifier triggers:
      turnover_cr, b2b_concentration_top3, state_count, export_share,
      b2c_share, top_quarter_share, late_filings_4q, has_us_uk_export.
    """
    out: Dict[str, dict] = {}
    src = "GSTR-1/3B aggregate"

    # Total turnover
    tot_m = re.search(rf"(?:total turnover|aggregate turnover|outward supplies){_NUM}", text, re.IGNORECASE | re.MULTILINE)
    turnover_cr = _to_cr(tot_m.group(1), tot_m.group(2)) if tot_m else None
    out["turnover_cr"] = _found(turnover_cr, src)

    # State presence: count distinct state GSTINs (first 2 digits of any 15-char GSTIN are state code)
    gstins = set(re.findall(r"\b(\d{2})[A-Z]{5}\d{4}[A-Z][A-Z\d]Z[A-Z\d]\b", text))
    state_count = len(gstins) if gstins else None
    out["state_count"] = _found(state_count, src + " (state codes)")

    # Export share — heuristic from labelled lines
    exp_m = re.search(rf"(?:exports? with payment of tax|zero rated supplies|export invoices){_NUM}", text, re.IGNORECASE)
    if exp_m and turnover_cr:
        exp_cr = _to_cr(exp_m.group(1), exp_m.group(2))
        out["export_share"] = _found(round(exp_cr / turnover_cr, 3) if turnover_cr > 0 else 0, src)
    else:
        out["export_share"] = _found(None, src)

    # US/UK exports — look for explicit country mentions in proximity to export lines
    has_us_uk = bool(re.search(r"\b(?:united states|usa|united kingdom|\bUK\b)\b", text, re.IGNORECASE)) and bool(exp_m)
    out["has_us_uk_export"] = _found(has_us_uk if exp_m else None, src)

    # B2B concentration: top-3 buyers by invoice value
    buyer_amounts: dict[str, float] = {}
    for line in re.finditer(rf"\b(\d{{2}}[A-Z]{{5}}\d{{4}}[A-Z][A-Z\d]Z[A-Z\d])\b.*?{_NUM}", text):
        gstin = line.group(1)
        amt = _to_cr(line.group(2), line.group(3))
        buyer_amounts[gstin] = buyer_amounts.get(gstin, 0) + amt
    if buyer_amounts and turnover_cr:
        top3 = sorted(buyer_amounts.values(), reverse=True)[:3]
        out["b2b_concentration_top3"] = _found(round(sum(top3) / turnover_cr, 3) if turnover_cr > 0 else 0, src + " (top-3 buyer GSTINs)")
    else:
        out["b2b_concentration_top3"] = _found(None, src)

    # B2C share
    b2c_m = re.search(rf"(?:b2c|business to consumer|unregistered persons){_NUM}", text, re.IGNORECASE)
    if b2c_m and turnover_cr:
        b2c_cr = _to_cr(b2c_m.group(1), b2c_m.group(2))
        out["b2c_share"] = _found(round(b2c_cr / turnover_cr, 3) if turnover_cr > 0 else 0, src)
    else:
        out["b2c_share"] = _found(None, src)

    # Top quarter share — heuristic from quarterly turnover lines if present
    quarter_amounts: list[float] = []
    for m in re.finditer(rf"Q[1-4]\s*(?:turnover|revenue|sales)?\s*[:\-]{_NUM}", text, re.IGNORECASE):
        quarter_amounts.append(_to_cr(m.group(1), m.group(2)))
    if len(quarter_amounts) >= 3:
        total = sum(quarter_amounts)
        out["top_quarter_share"] = _found(round(max(quarter_amounts) / total, 3) if total > 0 else 0, src + " (Q-wise)")
    else:
        out["top_quarter_share"] = _found(None, src)

    # Late filings: count mentions of penalty / late fee — proxy only
    late_count = len(re.findall(r"\blate fee\b|\binterest u/s 50\b|\bdelayed filing\b", text, re.IGNORECASE))
    out["late_filings_4q"] = _found(late_count if late_count > 0 else 0, src + " (late-fee mentions)")

    # HSN/SAC code distribution — list unique HSN/SAC codes
    hsn_codes = list(set(re.findall(r"\b(?:HSN|SAC)\s*[:\-]?\s*(\d{4,8})", text, re.IGNORECASE)))
    out["hsn_sac_codes"] = _found(hsn_codes if hsn_codes else None, src)
    # GST-PL mismatch: requires P&L cross-reference — emit placeholder for the engine to compute later
    out["gst_pl_mismatch_pct"] = _found(None, "cross-reference required")
    # Sector mismatch flag — same: needs declared sector to compute
    out["sector_mismatch_flag"] = _found(None, "cross-reference required")

    return out


def extract_prior_policy_fields(text: str) -> Dict[str, dict]:
    """Prior insurance policy schedule extraction.

    Per-LOB: si, premium, claims history, NCD years.
    """
    out: Dict[str, dict] = {}
    src = "Prior policy schedule"
    head = text.lower()

    # LOB detection — emit one set of fields per LOB if signals found
    lob_map = {
        "cyber":    ("cyber_si", "cyber_claims_3yr", "cyber_ncd_years"),
        "professional indemnity": ("pi_si", "pi_claims_3yr", "pi_ncd_years"),
        "directors": ("do_si", "do_claims_3yr", "do_ncd_years"),
        "d&o":      ("do_si", "do_claims_3yr", "do_ncd_years"),
        "fire":     ("property_si", "property_claims_3yr", "property_ncd_years"),
        "property": ("property_si", "property_claims_3yr", "property_ncd_years"),
        "crime":    ("crime_si", "crime_claims_3yr", "crime_ncd_years"),
        "fidelity": ("crime_si", "crime_claims_3yr", "crime_ncd_years"),
        "employees' compensation": ("ec_si", "ec_claims_3yr", "ec_ncd_years"),
        "workmen": ("ec_si", "ec_claims_3yr", "ec_ncd_years"),
        "group health": ("gh_si", "gh_claims_ratio", "gh_ncd_years"),
        "mediclaim": ("gh_si", "gh_claims_ratio", "gh_ncd_years"),
    }

    for keyword, (si_key, claims_key, ncd_key) in lob_map.items():
        if keyword not in head:
            continue
        # Find SI near the LOB keyword (within 400 chars)
        idx = head.find(keyword)
        window = text[max(0, idx-200):idx+400]
        si_m = re.search(rf"(?:sum insured|si){_NUM}", window, re.IGNORECASE)
        if si_m:
            out[si_key] = _found(_to_cr(si_m.group(1), si_m.group(2)), src)
        claims_m = re.search(r"claims?\s*(?:in\s+last\s+3\s*y(?:ears|rs)?|history)?\s*[:\-]?\s*(\d+)", window, re.IGNORECASE)
        if claims_m:
            out[claims_key] = _found(int(claims_m.group(1)), src)
        else:
            out[claims_key] = _found(0, src + " (no claims found)")
        ncd_m = re.search(r"(?:ncd|no\s*claim(?:s)?\s*discount|claims?\s*free)\s*[:\-]?\s*(\d+)\s*y(?:ears|rs)?", window, re.IGNORECASE)
        if ncd_m:
            out[ncd_key] = _found(int(ncd_m.group(1)), src)

    # PI retroactive date
    retro_m = re.search(r"retroactive\s*(?:date|period)?\s*[:\-]?\s*(\d+)\s*y(?:ears|rs)?", text, re.IGNORECASE)
    if retro_m:
        out["pi_retroactive_years"] = _found(int(retro_m.group(1)), src)

    # GH loss ratio
    lr_m = re.search(r"(?:loss\s*ratio|claims?\s*ratio)\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*%", text, re.IGNORECASE)
    if lr_m:
        out["gh_loss_ratio"] = _found(round(float(lr_m.group(1)) / 100.0, 3), src)

    return out


def extract_contract_fields(text: str) -> Dict[str, dict]:
    """Client contract / MSA / SOW extraction."""
    out: Dict[str, dict] = {}
    src = "Client contract"

    # Liability cap
    cap_m = re.search(rf"(?:liability\s*(?:shall\s*be\s*limited\s*to|cap(?:ped)?\s*at|not\s*exceed)|aggregate\s*liability){_NUM}", text, re.IGNORECASE)
    cap_inr = None
    if cap_m:
        cap_inr = _to_cr(cap_m.group(1), cap_m.group(2)) * 1_00_00_000
    out["liability_cap_inr"] = _found(cap_inr, src)

    # Unlimited liability flag
    unlimited = bool(re.search(r"unlimited\s*liability|no\s*limit\s*(?:of|on)\s*liability|liability.{0,40}shall\s*not\s*be\s*limited", text, re.IGNORECASE))
    out["unlimited_liability_flag"] = _found(unlimited, src)

    # Data processor / DPDP role
    dp_flag = bool(re.search(r"\bdata\s*processor\b|\bsub[\-\s]?processor\b|\bdpdp\s*act\b|process(?:es|ing)\s*personal\s*data\s*on\s*behalf", text, re.IGNORECASE))
    out["data_processor_role"] = _found(dp_flag, src)

    # PII volume estimate from explicit mentions
    pii_m = re.search(r"(?:approximately|around|circa|approx\.?)\s*(\d[\d,]*)\s*(?:user|customer|record|subject)s", text, re.IGNORECASE)
    pii_vol = int(pii_m.group(1).replace(",", "")) if pii_m else None
    out["pii_volume_est"] = _found(pii_vol, src)

    # SLA penalty per day
    sla_m = re.search(rf"(?:penalty|liquidated\s*damages|service\s*credit)s?[^.]{{0,80}}(?:per\s*day|/day|daily){_NUM}", text, re.IGNORECASE)
    if not sla_m:
        sla_m = re.search(rf"{_NUM}\s*per\s*day", text, re.IGNORECASE)
    sla_inr = None
    if sla_m:
        sla_inr = _to_cr(sla_m.group(1), sla_m.group(2)) * 1_00_00_000
    out["sla_penalty_per_day_inr"] = _found(sla_inr, src)

    # Foreign jurisdiction
    foreign = bool(re.search(r"governed\s*by\s*the\s*laws\s*of\s*(?:england|wales|united\s*kingdom|new\s*york|delaware|california|united\s*states|singapore|european\s*union|netherlands|germany)", text, re.IGNORECASE))
    out["foreign_jurisdiction_flag"] = _found(foreign, src)

    # Retroactive required
    retro_req = bool(re.search(r"professional\s*indemnity[^.]{0,100}retroactive|maintain\s*retroactive\s*cover|continuous\s*claims[\-\s]?made\s*cover", text, re.IGNORECASE))
    out["retroactive_required"] = _found(retro_req, src)

    # Third party indemnity
    tp_ind = bool(re.search(r"indemnif(?:y|ication)[^.]{0,80}(?:affiliates|subsidiaries|third\s*part(?:y|ies)|customers\s*of|end[\-\s]?users)", text, re.IGNORECASE))
    out["third_party_indemnity_flag"] = _found(tp_ind, src)

    # Liability cap to revenue — requires revenue cross-ref; placeholder
    out["liability_cap_to_revenue"] = _found(None, "cross-reference required")

    return out


def extract_asset_register_fields(text: str) -> Dict[str, dict]:
    """Fixed asset register extraction."""
    out: Dict[str, dict] = {}
    src = "Asset register"

    # Total replacement value
    rv_m = re.search(rf"(?:total\s*replacement\s*(?:value|cost)|reinstatement\s*value){_NUM}", text, re.IGNORECASE)
    out["total_replacement_cr"] = _found(_to_cr(rv_m.group(1), rv_m.group(2)) if rv_m else None, src)
    # Total book / WDV
    bv_m = re.search(rf"(?:total\s*(?:wdv|written\s*down\s*value|book\s*value|net\s*block)){_NUM}", text, re.IGNORECASE)
    book_cr = _to_cr(bv_m.group(1), bv_m.group(2)) if bv_m else None
    out["total_book_cr"] = _found(book_cr, src)
    if book_cr and out["total_replacement_cr"]["value"]:
        out["replacement_vs_book_premium_pct"] = _found(round((out["total_replacement_cr"]["value"] - book_cr) / book_cr, 3) if book_cr > 0 else 0, src)
    else:
        out["replacement_vs_book_premium_pct"] = _found(None, src)

    # Location count — count distinct address blocks or explicit declarations
    loc_m = re.search(r"(?:number\s*of\s*locations|locations?\s*[:\-])\s*(\d+)", text, re.IGNORECASE)
    if loc_m:
        loc_count = int(loc_m.group(1))
    else:
        # Fallback: count distinct PIN codes
        pins = set(re.findall(r"\b[1-9]\d{5}\b", text))
        loc_count = len(pins) if pins else None
    out["location_count"] = _found(loc_count, src)

    # Weighted-avg ages — extract from per-asset rows
    ages = [int(m.group(1)) for m in re.finditer(r"\b(\d{1,2})\s*y(?:ears|rs)?\s*old\b", text, re.IGNORECASE)]
    if ages:
        out["weighted_avg_age_all"] = _found(round(sum(ages) / len(ages), 1), src)
    # Specific equipment categories — same heuristic
    elec_ages = []
    mach_ages = []
    for line in text.split("\n"):
        if re.search(r"\b(?:laptop|server|router|switch|monitor|workstation|electronic)\b", line, re.IGNORECASE):
            m = re.search(r"\b(\d{1,2})\s*y(?:ears|rs)?\b", line)
            if m:
                elec_ages.append(int(m.group(1)))
        if re.search(r"\b(?:machine|machinery|cnc|lathe|press|boiler|generator|compressor|hvac|chiller)\b", line, re.IGNORECASE):
            m = re.search(r"\b(\d{1,2})\s*y(?:ears|rs)?\b", line)
            if m:
                mach_ages.append(int(m.group(1)))
    out["weighted_avg_age_electronic"] = _found(round(sum(elec_ages) / len(elec_ages), 1) if elec_ages else None, src)
    out["weighted_avg_age_machinery"] = _found(round(sum(mach_ages) / len(mach_ages), 1) if mach_ages else None, src)

    # Imported share
    imp_m = re.search(r"imported\s*(?:assets|equipment|machinery)\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*%", text, re.IGNORECASE)
    if imp_m:
        out["imported_share"] = _found(round(float(imp_m.group(1)) / 100.0, 3), src)
    else:
        # Heuristic: count "imported" mentions vs total asset row count
        imp_count = len(re.findall(r"\bimported\b|\bgermany\b|\bjapan\b|\bchina\b|\bswiss\b|\bsouth korea\b|\bitaly\b|\busa\b", text, re.IGNORECASE))
        total_rows = max(1, text.count("\n"))
        out["imported_share"] = _found(round(min(1.0, imp_count / max(10, total_rows)), 3) if imp_count else None, src + " (heuristic)")

    return out


def extract_vapt_fields(text: str) -> Dict[str, dict]:
    """VAPT / security audit summary extraction."""
    out: Dict[str, dict] = {}
    src = "VAPT report"

    # Critical / High counts
    crit_m = re.search(r"critical\s*(?:vulnerabilit(?:y|ies)|finding|severity)?\s*[:\-]?\s*(\d+)", text, re.IGNORECASE)
    out["critical_count"] = _found(int(crit_m.group(1)) if crit_m else None, src)
    high_m = re.search(r"high\s*(?:vulnerabilit(?:y|ies)|finding|severity)?\s*[:\-]?\s*(\d+)", text, re.IGNORECASE)
    out["high_count"] = _found(int(high_m.group(1)) if high_m else None, src)

    # MFA
    if re.search(r"\bmfa\b.{0,50}(?:enforc|requir|enabled|mandatory)", text, re.IGNORECASE) or re.search(r"multi[\-\s]?factor\s*authentication.{0,50}(?:enabled|required|enforced)", text, re.IGNORECASE):
        mfa = True
    elif re.search(r"\bno\s*mfa\b|mfa.{0,30}not\s*(?:enforced|enabled|deployed)", text, re.IGNORECASE):
        mfa = False
    else:
        mfa = None
    out["mfa_enabled"] = _found(mfa, src)

    # Backup RTO
    rto_m = re.search(r"\brto\b[:\s\-]*(\d+)\s*(hour|hr|day)s?", text, re.IGNORECASE)
    if rto_m:
        n = int(rto_m.group(1))
        if rto_m.group(2).lower().startswith("day"):
            n *= 24
        out["backup_rto_hours"] = _found(n, src)
    else:
        out["backup_rto_hours"] = _found(None, src)

    # Third party access count
    tp_m = re.search(r"(?:third[\-\s]?part(?:y|ies)|vendors?)\s*with\s*(?:admin|privileged)?\s*access\s*[:\-]?\s*(\d+)", text, re.IGNORECASE)
    out["third_party_access_count"] = _found(int(tp_m.group(1)) if tp_m else None, src)

    # ISO 27001 / SOC 2
    iso_active = bool(re.search(r"iso\s*27001\s*(?::|certified|valid|current|active)", text, re.IGNORECASE))
    soc2_active = bool(re.search(r"soc\s*2\s*(?:type\s*ii)?\s*(?::|certified|report|attestation)", text, re.IGNORECASE))
    out["iso27001_or_soc2_active"] = _found(iso_active or soc2_active, src)

    # Endpoint protection
    if re.search(r"\b(?:edr|endpoint\s*(?:detection|protection)|antivirus|xdr)\b.{0,50}(?:deployed|enabled|active|installed)", text, re.IGNORECASE):
        ep = True
    elif re.search(r"no\s*endpoint\s*protection|edr.{0,30}not\s*deployed", text, re.IGNORECASE):
        ep = False
    else:
        ep = None
    out["endpoint_protection_deployed"] = _found(ep, src)

    # DPDP audit
    dpdp = bool(re.search(r"dpdp\s*(?:act)?\s*(?:compliance|audit|gap\s*assessment)", text, re.IGNORECASE))
    out["dpdp_audit_completed"] = _found(dpdp, src)

    # Audit age
    age_m = re.search(r"(?:audit\s*date|report\s*date|assessment\s*date)\s*[:\-]?\s*(\d{1,2})[\-/\s]+(\w{3,9})[\-/\s]+(\d{4})", text, re.IGNORECASE)
    if age_m:
        from datetime import datetime
        try:
            d = datetime.strptime(f"{age_m.group(1)} {age_m.group(2)[:3]} {age_m.group(3)}", "%d %b %Y")
            months = (datetime.now() - d).days // 30
            out["audit_age_months"] = _found(months, src)
        except ValueError:
            out["audit_age_months"] = _found(None, src)
    else:
        out["audit_age_months"] = _found(None, src)

    return out


_EXTRACTORS = {
    "pl": extract_pl_fields,
    "balance_sheet": extract_bs_fields,
    "itr": extract_itr_fields,
    "gst_returns": extract_gst_fields,
    "prior_policy": extract_prior_policy_fields,
    "client_contract": extract_contract_fields,
    "asset_register": extract_asset_register_fields,
    "vapt_report": extract_vapt_fields,
}


def extract(doc_type: str, text: str) -> Dict[str, dict]:
    """Dispatch by doc_type. Unknown types return empty."""
    fn = _EXTRACTORS.get(doc_type)
    return fn(text) if fn else {}
