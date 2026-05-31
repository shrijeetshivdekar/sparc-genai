"""Cross-document consistency checks.

Each check returns a dict with keys:
    check:    short label
    status:   "pass" | "warning" | "not_applicable"
    values:   raw inputs the check ran on
    message:  human-readable summary
"""

from __future__ import annotations

from typing import Dict, List, Optional


def check_revenue_match(
    itr_revenue: Optional[float],
    pl_revenue: Optional[float],
    tolerance_pct: float = 5.0,
) -> dict:
    """Revenue from ITR vs P&L should match within ±tolerance_pct."""
    if itr_revenue is None or pl_revenue is None:
        return {
            "check": "ITR vs P&L Revenue",
            "status": "not_applicable",
            "values": {"itr_cr": itr_revenue, "pl_cr": pl_revenue},
            "message": "Need both ITR and P&L to compare.",
        }

    denom = max(abs(itr_revenue), abs(pl_revenue))
    if denom == 0:
        variance_pct = 0.0
    else:
        variance_pct = abs(itr_revenue - pl_revenue) / denom * 100

    status = "pass" if variance_pct <= tolerance_pct else "warning"
    return {
        "check": "ITR vs P&L Revenue",
        "status": status,
        "values": {"itr_cr": itr_revenue, "pl_cr": pl_revenue, "variance_pct": round(variance_pct, 2)},
        "message": (
            f"Variance {variance_pct:.1f}% — within {tolerance_pct:.0f}% tolerance."
            if status == "pass"
            else f"Variance {variance_pct:.1f}% exceeds {tolerance_pct:.0f}% tolerance — verify."
        ),
    }


def check_balance_sheet_balance(
    assets: Optional[float],
    liabilities: Optional[float],
    equity: Optional[float],
    tolerance_cr: float = 5.0,
) -> dict:
    """Assets ≈ Liabilities + Equity within ±tolerance_cr."""
    if assets is None or liabilities is None or equity is None:
        return {
            "check": "Balance Sheet Balance",
            "status": "not_applicable",
            "values": {"assets_cr": assets, "liabilities_cr": liabilities, "equity_cr": equity},
            "message": "Need Assets, Liabilities, and Equity.",
        }

    expected = liabilities + equity
    variance = abs(assets - expected)
    status = "pass" if variance <= tolerance_cr else "warning"
    return {
        "check": "Balance Sheet Balance",
        "status": status,
        "values": {
            "assets_cr": assets,
            "liabilities_plus_equity_cr": round(expected, 2),
            "variance_cr": round(variance, 2),
        },
        "message": (
            f"Assets ₹{assets} Cr ≈ L+E ₹{expected:.2f} Cr — balanced."
            if status == "pass"
            else f"Variance ₹{variance:.2f} Cr exceeds ±₹{tolerance_cr} Cr tolerance."
        ),
    }


def run_all_checks(extraction_summary: Dict[str, dict]) -> List[dict]:
    """Run every applicable check on the merged extraction summary."""
    def _get(field: str) -> Optional[float]:
        entry = extraction_summary.get(field) or {}
        return entry.get("value")

    return [
        check_revenue_match(
            itr_revenue=_get("itr_revenue_cr"),
            pl_revenue=_get("revenue_cr"),
        ),
        check_balance_sheet_balance(
            assets=_get("total_assets_cr"),
            liabilities=_get("total_liabilities_cr"),
            equity=_get("equity_cr"),
        ),
    ]
