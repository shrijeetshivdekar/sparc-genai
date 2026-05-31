"""Map extracted document numbers → categorical StartupInput hints.

The risk engine consumes categorical fields (funding_stage, team_size, etc.)
not raw rupee numbers. This module converts the extraction summary into a
prefill dict the form can hydrate.
"""

from __future__ import annotations

from typing import Dict, Optional


def _cost_per_head_inr(payroll_cr: float) -> int:
    """Sliding median cost per employee based on payroll scale."""
    if payroll_cr < 10:    return 6_00_000   # small co — ₹6L loaded
    if payroll_cr < 100:   return 8_00_000   # mid-market — ₹8L
    if payroll_cr < 1000:  return 12_00_000  # large — ₹12L
    return 18_00_000                          # enterprise IT services — ₹18L


def revenue_to_funding_stage(revenue_cr: Optional[float]) -> Optional[str]:
    """Bucket revenue (₹Cr) into the engine's funding_stage enum.

    Buckets are intentionally coarse — used only as a prefill *hint*.
    User can override on the form.
    """
    if revenue_cr is None:
        return None
    if revenue_cr < 1:
        return "Pre-seed"
    if revenue_cr < 10:
        return "Seed"
    if revenue_cr < 100:
        return "Series A"
    return "Series B+"


def payroll_to_team_size(payroll_cr: Optional[float]) -> Optional[int]:
    """Estimate team_size from annual employee benefit expense (₹Cr).

    Uses sliding per-head cost so large IT services companies get realistic
    headcounts (₹18L/head) instead of the naive ₹8L flat rate.
    """
    if payroll_cr is None or payroll_cr <= 0:
        return None
    cost = _cost_per_head_inr(payroll_cr)
    headcount = (payroll_cr * 1_00_00_000) / cost
    return max(1, int(round(headcount)))


def map_extracts_to_profile(extraction_summary: Dict[str, dict]) -> Dict[str, dict]:
    """Convert extracted fields → form prefill hints.

    Returns a dict where each key is a StartupInput field name and each value
    is {"value": X, "source": "explanation", "confidence": "extracted"|...}.
    Caller decides whether to apply each hint.
    """
    prefill: Dict[str, dict] = {}

    def _get(field: str) -> tuple[Optional[float], Optional[str]]:
        entry = extraction_summary.get(field) or {}
        return entry.get("value"), entry.get("confidence")

    # Prefer P&L revenue, fall back to ITR revenue.
    revenue_cr, rev_conf = _get("revenue_cr")
    rev_source = "P&L"
    if revenue_cr is None:
        revenue_cr, rev_conf = _get("itr_revenue_cr")
        rev_source = "ITR"

    stage = revenue_to_funding_stage(revenue_cr)
    if stage is not None:
        prefill["funding_stage"] = {
            "value": stage,
            "confidence": "calculated",
            "source": f"Inferred from {rev_source} revenue ₹{revenue_cr} Cr",
        }

    payroll_cr, _ = _get("payroll_cr")
    team = payroll_to_team_size(payroll_cr)
    if team is not None:
        prefill["team_size"] = {
            "value": team,
            "confidence": "calculated",
            "source": f"Estimated from P&L employee cost ₹{payroll_cr} Cr "
                      f"@ ₹{_cost_per_head_inr(payroll_cr) // 100000}L median per head",
        }

    return prefill


def build_evidence_packet(extraction_summary: Dict[str, dict]) -> Dict[str, Optional[float]]:
    """Display-only numbers shown alongside the assessment for the user's confidence."""
    def _v(field: str) -> Optional[float]:
        return (extraction_summary.get(field) or {}).get("value")

    return {
        "revenue_cr": _v("revenue_cr") if _v("revenue_cr") is not None else _v("itr_revenue_cr"),
        "gross_profit_cr": _v("gross_profit_cr"),
        "net_profit_cr": _v("net_profit_cr"),
        "total_assets_cr": _v("total_assets_cr"),
        "equity_cr": _v("equity_cr"),
        "total_liabilities_cr": _v("total_liabilities_cr"),
    }
