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


# Number with optional currency prefix and unit suffix.
# Captures the numeric portion + the unit (cr / crore / lakh / lac).
_NUM = r"[₹$Rs.\s]*([\d,]+(?:\.\d+)?)\s*(cr(?:ore)?|lakh?|lac)\b"


def _to_cr(value_str: str, unit: str) -> float:
    """Normalise a captured (number, unit) to crore (INR)."""
    n = float(value_str.replace(",", ""))
    u = unit.lower()
    if u.startswith("lakh") or u.startswith("lac") or u.startswith("lak"):
        return round(n / 100.0, 2)
    return round(n, 2)


def _first_match(text: str, patterns: list[str]) -> Tuple[float | None, str | None]:
    """Try patterns in order; return (value_cr, matched_pattern) on first hit."""
    for pat in patterns:
        m = re.search(pat, text, flags=re.IGNORECASE | re.MULTILINE)
        if m:
            return _to_cr(m.group(1), m.group(2)), pat
    return None, None


def detect_type(filename: str, text: str) -> str:
    """Heuristic doc-type detection from filename + first ~4000 chars of text.

    Returns one of: "pl" | "balance_sheet" | "itr" | "unknown".
    """
    name = (filename or "").lower()
    head = (text or "")[:4000].lower()

    # Filename-first: most reliable signal.
    if any(k in name for k in ("itr", "income_tax", "income-tax")):
        return "itr"
    if any(k in name for k in ("balance", "bs_", "_bs", "bsheet")):
        return "balance_sheet"
    if any(k in name for k in ("p&l", "pnl", "p_l", "profit", "income_statement")):
        return "pl"

    # Content fallback.
    if "income tax return" in head or "assessment year" in head:
        return "itr"
    if "profit and loss" in head or "statement of profit" in head:
        return "pl"
    if "balance sheet" in head:
        return "balance_sheet"
    # Strong multi-term signals even if no header label found.
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
    ]
    cogs_pats = [
        rf"(?:Cost of goods sold|Cost of materials consumed|Cost of revenue|COGS){_NUM}",
    ]
    profit_pats = [
        rf"(?:Gross profit|Gross margin){_NUM}",
    ]
    ebitda_pats = [
        rf"(?:EBITDA|Operating profit before depreciation){_NUM}",
    ]
    net_pats = [
        rf"(?:Net profit|Profit for the (?:year|period)|Profit after tax|PAT){_NUM}",
    ]
    payroll_pats = [
        rf"(?:Employee benefit expenses?|Employee costs?|Personnel expenses?|Salaries(?: and wages)?){_NUM}",
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
    ]
    fixed_assets_pats = [
        rf"(?:Property,? plant and equipment|Fixed assets|Tangible assets){_NUM}",
    ]
    current_assets_pats = [
        rf"(?:Total current assets|Current assets){_NUM}",
    ]
    inventory_pats = [
        rf"(?:Inventories|Inventory){_NUM}",
    ]
    receivables_pats = [
        rf"(?:Trade receivables|Accounts receivable|Sundry debtors){_NUM}",
    ]
    liabilities_pats = [
        rf"(?:Total liabilities|TOTAL LIABILITIES){_NUM}",
    ]
    equity_pats = [
        rf"(?:Total equity|Shareholders'? funds|Equity attributable to (?:shareholders|owners)){_NUM}",
    ]
    debt_pats = [
        rf"(?:Total borrowings|Long[- ]term borrowings|Total debt){_NUM}",
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


_EXTRACTORS = {
    "pl": extract_pl_fields,
    "balance_sheet": extract_bs_fields,
    "itr": extract_itr_fields,
}


def extract(doc_type: str, text: str) -> Dict[str, dict]:
    """Dispatch by doc_type. Unknown types return empty."""
    fn = _EXTRACTORS.get(doc_type)
    return fn(text) if fn else {}
