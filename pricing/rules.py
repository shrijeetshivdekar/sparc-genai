"""Decline / Refer rules. Each cites an Indian regulatory or carrier document.

Inputs come from the same set the model.quote() receives.
Output: list of {rule_id, reason, citation, url} for any rule that fires.
"""
from __future__ import annotations
from typing import Any, Optional


def _nic_division(nic_code: str) -> str:
    s = "".join(c for c in str(nic_code or "") if c.isdigit())
    return s[:2] if len(s) >= 2 else ""


def evaluate_decline(
    revenue_current_inr: float,
    nic_code: str,
    params: dict,
) -> list[dict]:
    """Hard-decline rules. Return [] if none fire."""
    fires: list[dict] = []

    # R-D1. Minimum revenue (MSME appetite floor)
    th = params["decision_thresholds"]["decline_min_revenue_inr"]
    if revenue_current_inr < float(th["value"]):
        fires.append({
            "rule_id": "min_revenue",
            "reason": f"Revenue ₹{revenue_current_inr/1_00_000:.1f}L below MSME appetite floor "
                      f"₹{float(th['value'])/1_00_000:.0f}L.",
            "citation": th["source"]["citation"],
            "url": th["source"].get("url", ""),
        })

    # R-D2. Excluded NIC codes
    nic_div = _nic_division(nic_code)
    for excl in params.get("excluded_nic", []) or []:
        if str(excl["code"]) == nic_div:
            fires.append({
                "rule_id": f"excluded_nic_{nic_div}",
                "reason": f"NIC {nic_div} on carrier-excluded list: {excl['reason']}",
                "citation": excl["source"]["citation"],
                "url": excl["source"].get("url", ""),
            })

    return fires


def evaluate_refer(
    revenue_current_inr: float,
    nic_code: str,
    stage: str,
    cin: Optional[str],
    data_quality_score: float,
    params: dict,
) -> list[dict]:
    """Soft-refer rules. Return [] if none fire. Quote still computed."""
    fires: list[dict] = []

    # R-R1. Listed company (SEBI LODR exposure → human review)
    # We infer listed status from CIN prefix 'L' (Listed) per MCA conventions.
    if cin and cin.upper().startswith("L"):
        fires.append({
            "rule_id": "listed_company",
            "reason": "Listed company (CIN prefix 'L'). SEBI LODR Reg 17 board/audit "
                      "obligations require underwriter D&O review.",
            "citation": "SEBI LODR Regulations 2015 (last amended 2024)",
            "url": "https://www.sebi.gov.in/legal/regulations/jul-2024/securities-and-exchange-board-of-india-listing-obligations-and-disclosure-requirements-regulations-2015-last-amended-on-july-10-2024-_85291.html",
        })

    # R-R2. Pre-IPO stage → S1/DRHP disclosure liability uplift
    if stage == "pre_ipo":
        fires.append({
            "rule_id": "pre_ipo_review",
            "reason": "Pre-IPO stage: DRHP/S1 disclosure liability under SEBI ICDR 2018 "
                      "requires senior D&O / PI underwriter sign-off.",
            "citation": "SEBI (Issue of Capital and Disclosure Requirements) Regulations 2018",
            "url": "https://www.sebi.gov.in",
        })

    # R-R3. Data quality below threshold
    th = float(params["decision_thresholds"]["refer_below_data_quality"]["value"])
    if data_quality_score < th:
        # not duplicated here (the model.py refer block also catches it) — listed for completeness
        pass

    # R-R4. Director disqualification (placeholder for MCA21 integration)
    # Real implementation: fetch MCA21 director-disqualification list; refer if any
    # current director appears. Citation: Companies Act 2013, Sec 164.
    # Currently a stub — no fire without external lookup.

    return fires
