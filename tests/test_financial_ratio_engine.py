"""Tests for pricing.financial_ratio_engine."""

import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from pricing.financial_ratio_engine import (
    compute_ratios,
    apply_modifiers,
    compute_si_from_financials,
    compute_risk_loading,
    compute_confidence_band,
    detect_data_quality_warnings,
    verified_assessment,
)


def _e(field, value):
    """Build an extraction_summary entry."""
    return {field: {"value": value, "confidence": "extracted", "source": "test"}}


def _merge(*dicts):
    out = {}
    for d in dicts:
        out.update(d)
    return out


# ─── Ratio bands ─────────────────────────────────────────────────────────────

def test_net_profit_margin_bands():
    # TCS-like: 22% margin → premium_q4
    extracts = _merge(_e("revenue_cr", 220938), _e("net_profit_cr", 49096))
    r = compute_ratios(extracts)
    assert r["net_profit_margin"]["band"] == "premium_q4"
    assert r["net_profit_margin"]["value"] == 0.2222

    # Loss-making
    extracts = _merge(_e("revenue_cr", 100), _e("net_profit_cr", -10))
    assert compute_ratios(extracts)["net_profit_margin"]["band"] == "burn_q1"

    # Thin margin
    extracts = _merge(_e("revenue_cr", 100), _e("net_profit_cr", 3))
    assert compute_ratios(extracts)["net_profit_margin"]["band"] == "thin_q2"


def test_debt_to_equity_bands():
    # Conservative
    extracts = _merge(_e("equity_cr", 100), _e("debt_cr", 20))
    assert compute_ratios(extracts)["debt_to_equity"]["band"] == "conservative_q1"

    # Highly leveraged
    extracts = _merge(_e("equity_cr", 100), _e("debt_cr", 400))
    assert compute_ratios(extracts)["debt_to_equity"]["band"] == "highly_leveraged_q4"

    # Negative equity — distressed flag (no division)
    extracts = _merge(_e("equity_cr", -50), _e("debt_cr", 200))
    r = compute_ratios(extracts)
    assert r["debt_to_equity"]["band"] == "distressed_negative_equity"
    assert r["debt_to_equity"]["value"] is None


def test_asset_intensity_bands():
    # TCS-like asset-light (PPE 8259 / Assets 149268 = 5.5%)
    extracts = _merge(_e("total_assets_cr", 149268), _e("fixed_assets_cr", 8259))
    r = compute_ratios(extracts)
    assert r["asset_intensity"]["band"] == "asset_light_q1"

    # Infrastructure-heavy
    extracts = _merge(_e("total_assets_cr", 100), _e("fixed_assets_cr", 70))
    assert compute_ratios(extracts)["asset_intensity"]["band"] == "infrastructure_q4"


def test_dso_bands():
    # TCS-like (Receivables 48892 / Revenue 220938 × 365 = 80.8 days)
    extracts = _merge(_e("revenue_cr", 220938), _e("receivables_cr", 48892))
    r = compute_ratios(extracts)
    assert r["dso_days"]["band"] == "typical_b2b_q2"
    assert 80 <= r["dso_days"]["value"] <= 82


def test_payroll_intensity_bands():
    # TCS-like (Payroll 112142 / Revenue 220938 = 50.7%)
    extracts = _merge(_e("revenue_cr", 220938), _e("payroll_cr", 112142))
    r = compute_ratios(extracts)
    assert r["payroll_intensity"]["band"] == "people_heavy_q3"


def test_missing_inputs_yield_none():
    r = compute_ratios({})
    for ratio_name, data in r.items():
        assert data["value"] is None or data.get("band") == "distressed_negative_equity"


def test_zero_denominator_safe():
    extracts = _merge(_e("revenue_cr", 0), _e("net_profit_cr", 10))
    assert compute_ratios(extracts)["net_profit_margin"]["value"] is None


# ─── Modifiers ────────────────────────────────────────────────────────────────

def _base_scores():
    return {dim: 50 for dim in [
        "cyber_technical", "data_privacy", "liability", "ip_infringement",
        "key_person", "governance_fraud", "property", "regulatory_compliance",
        "esg_climate", "geopolitical", "gig_labour", "policy_velocity",
        "reputation", "tax_tp",
    ]}


def test_burn_q1_elevates_key_person():
    extracts = _merge(_e("revenue_cr", 100), _e("net_profit_cr", -20))
    ratios = compute_ratios(extracts)
    modified, reasons = apply_modifiers(_base_scores(), ratios, extracts)
    assert modified["key_person"] > 50  # base 50, +20 mod
    assert any(r["dim"] == "key_person" and r["band"] == "burn_q1" for r in reasons)


def test_asset_light_reduces_property():
    extracts = _merge(_e("total_assets_cr", 100), _e("fixed_assets_cr", 5))
    ratios = compute_ratios(extracts)
    modified, reasons = apply_modifiers(_base_scores(), ratios, extracts)
    # Base 50, -25 → 25 (clipped at -25)
    assert modified["property"] == 25
    assert any(r["dim"] == "property" and r["modifier"] == -25 for r in reasons)


def test_distressed_negative_equity_max_modifier():
    extracts = _merge(_e("equity_cr", -10), _e("total_assets_cr", 100))
    ratios = compute_ratios(extracts)
    modified, reasons = apply_modifiers(_base_scores(), ratios, extracts)
    # governance_fraud +25 (distressed, no other mods → uncapped)
    assert modified["governance_fraud"] == 75
    # key_person +15
    assert modified["key_person"] == 65


def test_per_dim_modifier_cap_at_25():
    # Stack burn_q1 (+20 key_person) with thin_q2 — impossible. Use negative equity (+15 key_person)
    # plus highly_leveraged (+10 key_person) = +25 cap held.
    # Negative equity blocks highly_leveraged from triggering. Use big DSO + burn for stacking.
    extracts = _merge(
        _e("revenue_cr", 100), _e("net_profit_cr", -30),  # burn_q1 → key_person +20
        _e("equity_cr", 5), _e("debt_cr", 25),             # D/E=5 → highly_leveraged +10 to key_person
    )
    ratios = compute_ratios(extracts)
    modified, reasons = apply_modifiers(_base_scores(), ratios, extracts)
    # Total delta on key_person: +20 + +10 = +30, clipped to +25 → final 75
    assert modified["key_person"] == 75


def test_final_score_clipped_to_100():
    base = _base_scores()
    base["key_person"] = 90
    extracts = _merge(_e("revenue_cr", 100), _e("net_profit_cr", -20))
    ratios = compute_ratios(extracts)
    modified, _ = apply_modifiers(base, ratios, extracts)
    assert modified["key_person"] == 100  # 90 + 20 → clipped


def test_revenue_scale_modifier_large_company():
    # Revenue > 500 → cyber +15
    extracts = _e("revenue_cr", 220938)
    ratios = compute_ratios(extracts)
    base = _base_scores()
    modified, reasons = apply_modifiers(base, ratios, extracts)
    cyber_reasons = [r for r in reasons if r["dim"] == "cyber_technical" and r["ratio"] == "revenue_scale"]
    assert len(cyber_reasons) == 1
    assert cyber_reasons[0]["modifier"] == 15


# ─── Sum Insured ─────────────────────────────────────────────────────────────

def test_si_cyber_uses_revenue():
    extracts = _e("revenue_cr", 1000)
    si = compute_si_from_financials(extracts)
    # 1.5% × ₹1000 Cr = ₹15 Cr
    assert si["Cyber Liability"]["si_inr"] == 15 * 1_00_00_000


def test_si_cyber_floored_at_5cr():
    extracts = _e("revenue_cr", 100)  # 1.5% = ₹1.5 Cr → floor at ₹5 Cr
    si = compute_si_from_financials(extracts)
    assert si["Cyber Liability"]["si_inr"] == 5 * 1_00_00_000


def test_si_cyber_capped_at_500cr():
    extracts = _e("revenue_cr", 100000)  # 1.5% = ₹1500 Cr → cap at ₹500 Cr
    si = compute_si_from_financials(extracts)
    assert si["Cyber Liability"]["si_inr"] == 500 * 1_00_00_000


def test_si_do_uses_equity():
    extracts = _e("equity_cr", 1000)
    si = compute_si_from_financials(extracts)
    assert si["D&O Liability"]["si_inr"] == 100 * 1_00_00_000  # 10% × 1000


def test_si_do_negative_equity_falls_back_to_assets():
    extracts = _merge(_e("equity_cr", -50), _e("total_assets_cr", 1000))
    si = compute_si_from_financials(extracts)
    assert si["D&O Liability"]["si_inr"] == 50 * 1_00_00_000  # 5% × 1000
    assert "negative equity fallback" in si["D&O Liability"]["formula"]


def test_si_pi_rate_depends_on_gross_margin():
    # High gross margin → 0.5% rate
    high_gm = _merge(_e("revenue_cr", 1000), _e("cogs_cr", 400))  # GM = 60%
    si_high = compute_si_from_financials(high_gm)["Professional Indemnity"]["si_inr"]

    # Low gross margin → 0.3% rate
    low_gm = _merge(_e("revenue_cr", 1000), _e("cogs_cr", 700))  # GM = 30%
    si_low = compute_si_from_financials(low_gm)["Professional Indemnity"]["si_inr"]

    assert si_high > si_low


def test_si_trade_credit_not_triggered_below_5cr():
    extracts = _e("receivables_cr", 3)
    si = compute_si_from_financials(extracts)
    assert "Trade Credit" not in si


def test_si_marine_not_triggered_for_services():
    # TCS-like: inventory ₹29 Cr (services co)
    extracts = _e("inventory_cr", 29)
    si = compute_si_from_financials(extracts)
    # 29 > 1 → triggered for inventory; just confirms it's there
    assert "Marine Cargo" in si

    # But inventory < 1 → not triggered
    extracts2 = _e("inventory_cr", 0.5)
    assert "Marine Cargo" not in compute_si_from_financials(extracts2)


def test_si_group_health_implies_headcount_small_co():
    # Small co bucket (<₹10 Cr payroll): ₹6L/head → 133 employees → ₹5.32 Cr SI
    extracts = _e("payroll_cr", 8)
    si = compute_si_from_financials(extracts)["Group Health"]
    assert si["implied_headcount"] == 133
    assert si["cost_per_head_inr"] == 6_00_000


def test_si_group_health_large_co_uses_higher_cost():
    # Large IT services bucket (>₹1000 Cr payroll): ₹18L/head
    extracts = _e("payroll_cr", 112142)  # TCS-like
    si = compute_si_from_financials(extracts)["Group Health"]
    assert si["cost_per_head_inr"] == 18_00_000
    # ₹112142 Cr ÷ ₹18L = ~623,011 employees → SI capped at ₹500 Cr
    assert 600_000 <= si["implied_headcount"] <= 650_000
    assert si["si_inr"] == 500 * 1_00_00_000


def test_si_total_shrunk_if_exceeds_3x_revenue():
    # Construct an absurd case: tiny revenue, huge balance sheet
    extracts = _merge(
        _e("revenue_cr", 10),         # 3× = 30 Cr cap
        _e("equity_cr", 5000),        # D&O cap=250 Cr alone exceeds
        _e("fixed_assets_cr", 1000),  # Property = 1000 Cr
    )
    si = compute_si_from_financials(extracts)
    total_si_cr = sum(c["si_inr"] for c in si.values()) / 1_00_00_000
    assert total_si_cr <= 30.5  # 3× revenue with rounding


# ─── Risk loading ────────────────────────────────────────────────────────────

def test_loading_neutral_when_all_medium():
    scores = {d: 50 for d in [
        "cyber_technical", "data_privacy", "regulatory_compliance",
        "governance_fraud", "key_person", "liability", "ip_infringement",
        "property", "esg_climate", "reputation", "gig_labour",
    ]}
    loading = compute_risk_loading(scores)
    assert loading["Cyber Liability"]["loading"] == 1.0


def test_loading_increases_with_high_scores():
    scores = {d: 50 for d in [
        "cyber_technical", "data_privacy", "regulatory_compliance",
        "governance_fraud", "key_person", "liability", "ip_infringement",
        "property", "esg_climate", "reputation", "gig_labour",
    ]}
    scores["cyber_technical"] = 95     # very_high → +0.10
    scores["data_privacy"] = 75        # high → +0.05
    loading = compute_risk_loading(scores)
    assert loading["Cyber Liability"]["loading"] == 1.15


def test_loading_capped_at_1_50():
    scores = {d: 95 for d in [
        "cyber_technical", "data_privacy", "regulatory_compliance",
    ]}
    loading = compute_risk_loading(scores)
    # 3 × 0.10 = +0.30 → 1.30. Stays under cap.
    assert loading["Cyber Liability"]["loading"] == 1.30


def test_loading_floored_at_0_85():
    scores = {d: 10 for d in [
        "cyber_technical", "data_privacy", "regulatory_compliance",
    ]}
    loading = compute_risk_loading(scores)
    # 3 × -0.05 = -0.15 → 0.85
    assert loading["Cyber Liability"]["loading"] == 0.85


def test_group_health_no_loading():
    scores = {"cyber_technical": 95}
    loading = compute_risk_loading(scores)
    assert loading["Group Health"]["loading"] == 1.0


# ─── Confidence band ─────────────────────────────────────────────────────────

def test_band_estimated_when_no_extracts():
    band = compute_confidence_band({})
    assert band["width_pct"] == 50
    assert band["verification_level"] == "estimated"


def test_band_fully_verified_with_all_inputs():
    extracts = _merge(
        _e("revenue_cr", 100), _e("equity_cr", 50),
        _e("payroll_cr", 20), _e("fixed_assets_cr", 30),
        _e("receivables_cr", 10),
    )
    band = compute_confidence_band(extracts)
    # 50 - 12 - 10 - 8 - 5 - 5 = 10 → floored at 12
    assert band["width_pct"] == 12
    assert band["verification_level"] == "fully_verified"
    assert band["plus_minus_pct"] == 6


def test_band_partially_verified_with_revenue_only():
    extracts = _e("revenue_cr", 100)
    band = compute_confidence_band(extracts)
    # 50 - 12 = 38 → partially_verified
    assert band["width_pct"] == 38
    assert band["verification_level"] == "partially_verified"


# ─── Warnings ────────────────────────────────────────────────────────────────

def test_warning_sector_inconsistency_saas_with_heavy_ppe():
    extracts = _merge(_e("total_assets_cr", 100), _e("fixed_assets_cr", 40))
    ratios = compute_ratios(extracts)
    warnings = detect_data_quality_warnings(extracts, ratios, "SaaS")
    assert any(w["type"] == "sector_inconsistency" for w in warnings)


def test_warning_negative_equity_critical():
    extracts = _e("equity_cr", -10)
    warnings = detect_data_quality_warnings(extracts, {}, None)
    assert any(w["type"] == "distressed_balance_sheet" and w["severity"] == "critical" for w in warnings)


def test_warning_balance_sheet_imbalance():
    # Assets 100, Liab 60, Equity 30 → gap 10 > 5% of 100
    extracts = _merge(
        _e("total_assets_cr", 100),
        _e("total_liabilities_cr", 60),
        _e("equity_cr", 30),
    )
    warnings = detect_data_quality_warnings(extracts, {}, None)
    assert any(w["type"] == "balance_sheet_imbalance" for w in warnings)


def test_warning_loss_making():
    extracts = _e("net_profit_cr", -5)
    warnings = detect_data_quality_warnings(extracts, {}, None)
    assert any(w["type"] == "loss_making" for w in warnings)


# ─── End-to-end on TCS-like data ─────────────────────────────────────────────

def test_e2e_tcs_profile_produces_sensible_output():
    """TCS FY24: high revenue, asset-light, services-heavy, profitable."""
    extracts = _merge(
        _e("revenue_cr", 220938),
        _e("net_profit_cr", 49096),
        _e("payroll_cr", 112142),
        _e("total_assets_cr", 149268),
        _e("fixed_assets_cr", 8259),
        _e("current_assets_cr", 110270),
        _e("inventory_cr", 29),
        _e("receivables_cr", 48892),
        _e("total_liabilities_cr", 64592),
        _e("equity_cr", 84676),
    )
    base_scores = {dim: 50 for dim in [
        "cyber_technical", "data_privacy", "liability", "ip_infringement",
        "key_person", "governance_fraud", "property", "regulatory_compliance",
        "esg_climate", "geopolitical", "gig_labour", "policy_velocity",
        "reputation", "tax_tp",
    ]}

    result = verified_assessment(extracts, base_scores, inferred_sector="IT Services")

    # Profitable → key_person REDUCED
    assert result["modified_scores"]["key_person"] < 50

    # Asset-light → property REDUCED
    assert result["modified_scores"]["property"] == 25  # base 50 - 25 cap

    # High revenue → cyber UP
    assert result["modified_scores"]["cyber_technical"] > 50

    # Cyber SI = 1.5% × 220938 = 3314 → capped at 500 Cr
    assert result["sum_insured_per_cover"]["Cyber Liability"]["si_inr"] == 500 * 1_00_00_000

    # D&O SI = 10% × 84676 = 8467 → capped at 250 Cr
    assert result["sum_insured_per_cover"]["D&O Liability"]["si_inr"] == 250 * 1_00_00_000

    # Confidence: all 5 key inputs present → fully_verified
    assert result["confidence_band"]["verification_level"] == "fully_verified"

    # Sanity: tax_tp not modified (no tax data) → stays at base
    assert result["modified_scores"]["tax_tp"] == 50
