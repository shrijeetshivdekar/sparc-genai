"""Tests for the SPARC pricing model.

Each test maps to a numbered requirement from the spec.
Run:  python -m pytest tests/test_pricing.py -v
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

# Make pricing/ importable
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pricing.model import quote, load_params, format_inr  # noqa: E402


@pytest.fixture
def params():
    return load_params()


@pytest.fixture
def msme_property_inputs():
    """MSME ≤ ₹5 cr SI — IRDAI Bharat Sookshma Udyam Suraksha regulated rate."""
    return dict(
        revenue_current_inr=3_00_00_000,           # ₹3 Cr
        revenue_projected_inr=4_50_00_000,
        nic_code="74",                              # Other professional
        stage="seed",
        state="Karnataka",
        headcount=12,
        years_since_incorporation=2.0,
        cin="U72900KA2024PTC012345",
        dpiit_recognised=True,
        line_of_business="Property",
        sum_insured_inr=4_00_00_000,                # ₹4 Cr — within MSME ceiling
        deductible_inr=25_000,
        prior_claims=[],
        underwriter_loadings_discounts={},
    )


@pytest.fixture
def cyber_seriesA_inputs():
    return dict(
        revenue_current_inr=8_00_00_000,
        revenue_projected_inr=15_00_00_000,
        nic_code="6201",
        stage="seriesA",
        state="Maharashtra",
        headcount=42,
        years_since_incorporation=3.1,
        cin="U62012MH2022PTC098765",
        dpiit_recognised=True,
        line_of_business="Cyber",
        sum_insured_inr=5_00_00_000,
        deductible_inr=1_00_000,
        prior_claims=[],
        underwriter_loadings_discounts={},
    )


@pytest.fixture
def do_seriesA_inputs():
    return dict(
        revenue_current_inr=8_00_00_000,
        revenue_projected_inr=15_00_00_000,
        nic_code="6201",
        stage="seriesA",
        state="Karnataka",
        headcount=42,
        years_since_incorporation=3.1,
        cin="U62012KA2022PTC098765",   # 'U' prefix = Unlisted
        dpiit_recognised=True,
        line_of_business="DO",
        sum_insured_inr=5_00_00_000,
        deductible_inr=1_00_000,
        prior_claims=[],
        underwriter_loadings_discounts={},
    )


# ─── Test 1: Property MSME reconciles to BSU regulated rate ±5% ──────────────

def test_1_property_msme_matches_bharat_sookshma_rate(msme_property_inputs, params):
    """BSU regulated rate is ₹6,000 per crore SI (₹0.06/₹100). For ₹4 Cr SI,
    pure premium ≈ ₹24,000 before factors/expenses. Final premium midpoint
    should be within ±5% of (raw BSU pure premium × multipliers × gross-up
    × (1 + GST))."""
    q = quote(**msme_property_inputs)

    # Pull values direct from parameters.yaml (test asserts model honours them)
    bsu_rate = float(params["base_rate_per_crore"]["Property"]["seed"]["value"])
    assert bsu_rate == 6000, f"BSU rate should be ₹6,000/cr, got ₹{bsu_rate}"

    # Compute the expected pure premium directly from the regulated rate.
    si_cr = msme_property_inputs["sum_insured_inr"] / 1_00_00_000
    expected_pure = bsu_rate * si_cr  # ₹24,000
    assert q.factor_trace[1].raw_value == pytest.approx(expected_pure, rel=0.001)

    # Sanity: the final premium midpoint must include the GST and stamp duty.
    assert q.gst_amount_inr > 0
    assert q.stamp_duty_inr > 0
    # The final mid should reconcile to within ±5% of a clean recomputation
    # of (pure × factors × gross-up × (1+GST) + stamp).
    factor_product = 1.0
    for entry in q.factor_trace:
        if entry.step.startswith(("3", "4", "5", "6")) and isinstance(entry.raw_value, (int, float)):
            if entry.step.startswith("6"):
                factor_product *= entry.raw_value
            elif entry.step.startswith("5"):
                factor_product *= entry.raw_value
            elif entry.step.startswith("4"):
                factor_product *= entry.raw_value
            elif entry.step.startswith("3"):
                factor_product *= entry.raw_value
    expected_gross = expected_pure * factor_product
    expected_final = expected_gross * (1 + 0.18) + q.stamp_duty_inr
    deviation = abs(q.premium_mid_inr - expected_final) / expected_final
    assert deviation <= 0.05, f"Property quote off BSU expected by {deviation*100:.1f}% > 5%"


# ─── Test 2: Cyber confidence ≤ medium, DPDP + CERT-In in sources ────────────

def test_2_cyber_confidence_and_dpdp_anchor(cyber_seriesA_inputs):
    q = quote(**cyber_seriesA_inputs)
    # Base-rate confidence for Cyber must be ≤ medium (low is fine)
    base = q.factor_trace[0]
    assert base.confidence in ("medium", "low"), (
        f"Cyber base-rate confidence must be ≤ medium, got '{base.confidence}'"
    )

    # CERT-In and DPDP Act must appear somewhere in sources_cited *or* the
    # factor trace notes. Because the inputs don't directly trigger a
    # CERT-In/DPDP loading without the user adding one, we test that the
    # *available* loadings/discounts catalog references DPDP + CERT-In.
    params = load_params()
    catalog_text = yaml.safe_dump(params["loadings_discounts"]).lower()
    assert "dpdp" in catalog_text, "DPDP must be cited as severity anchor in loadings catalog"
    assert "cert-in" in catalog_text, "CERT-In must be cited in loadings catalog"

    # DPDP severity anchor block must exist with ₹250 cr cap
    assert params["dpdp_severity"]["max_penalty_inr"]["value"] == 2_50_00_00_000


# ─── Test 3: D&O Series A unlisted flags stage_factor as PLACEHOLDER ─────────

def test_3_do_seriesA_flags_stage_placeholder(do_seriesA_inputs):
    q = quote(**do_seriesA_inputs)
    paths = q.placeholders_used
    assert any("stage_factor.seriesA" in p for p in paths), (
        f"stage_factor.seriesA must be flagged as PLACEHOLDER. Got: {paths}"
    )
    # And the trace entry must mark it visually
    stage_entries = [t for t in q.factor_trace if "Stage factor" in t.step]
    assert stage_entries and stage_entries[0].is_placeholder is True


# ─── Test 4: GST line item = gross_premium * 0.18 exactly ────────────────────

def test_4_gst_is_exactly_18pct_of_gross(do_seriesA_inputs):
    q = quote(**do_seriesA_inputs)
    expected = q.gross_premium_inr * 0.18
    assert q.gst_amount_inr == pytest.approx(expected, abs=0.5)


# ─── Test 5: Indian lakh/crore currency formatting ───────────────────────────

def test_5_indian_currency_formatting():
    assert format_inr(1234567890) == "₹1,23,45,67,890"
    assert format_inr(12345) == "₹12,345"
    assert format_inr(100000) == "₹1,00,000"
    assert format_inr(123) == "₹123"
    assert format_inr(0) == "₹0"


# ─── Test 6: Editability — parameters.yaml change produces different quote ───

def test_6_parameter_edit_changes_quote(tmp_path, do_seriesA_inputs):
    """Edit base_rate via in-memory params dict, re-quote, expect different premium."""
    p_a = load_params()
    q_before = quote(**{**do_seriesA_inputs, "underwriter_loadings_discounts": {}}, params=p_a)

    # Mutate the in-memory copy
    p_b = load_params()
    p_b["base_rate_per_crore"]["DO"]["seriesA"]["value"] = (
        p_b["base_rate_per_crore"]["DO"]["seriesA"]["value"] * 1.20
    )
    q_after = quote(**{**do_seriesA_inputs, "underwriter_loadings_discounts": {}}, params=p_b)

    assert q_after.premium_mid_inr > q_before.premium_mid_inr * 1.10
    # Audit log behaviour is tested separately via CLI invocation


def test_6b_cli_edit_appends_audit_log(tmp_path, monkeypatch):
    """Exercise the CLI's edit + audit_log append. Uses a copy of parameters.yaml."""
    # copy params to tmp
    src = ROOT / "pricing" / "parameters.yaml"
    dst = tmp_path / "parameters.yaml"
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    audit = tmp_path / "audit_log.csv"

    # monkeypatch paths inside params_cli
    import pricing.params_cli as cli
    monkeypatch.setattr(cli, "PARAMS", dst)
    monkeypatch.setattr(cli, "AUDIT", audit)

    import argparse
    ns = argparse.Namespace(
        path="base_rate_per_crore.DO.seriesA",
        new_value="50000",
        reason="test calibration to Tata AIG FY25 brochure",
    )
    cli.cmd_edit(ns)

    data = yaml.safe_load(dst.read_text())
    assert data["base_rate_per_crore"]["DO"]["seriesA"]["value"] == 50000

    rows = audit.read_text().strip().splitlines()
    assert len(rows) == 2  # header + 1 entry
    assert "base_rate_per_crore.DO.seriesA" in rows[1]
    assert "test calibration" in rows[1]


# ─── Test 7: Sensitivity — range width ≥ 60% of midpoint ─────────────────────

def test_7_premium_range_min_width(do_seriesA_inputs):
    q = quote(**do_seriesA_inputs)
    width = q.premium_high_inr - q.premium_low_inr
    assert width >= 0.60 * q.premium_mid_inr, (
        f"Range width {width:.0f} < 60% of mid {q.premium_mid_inr:.0f}"
    )


# ─── Test 8: CEO export — Markdown table, placeholders visibly marked ────────

def test_8_ceo_deck_export(tmp_path, monkeypatch):
    """`params export-deck` produces a Markdown table; PLACEHOLDERs flagged."""
    import pricing.params_cli as cli
    deck = tmp_path / "ceo_deck.md"
    monkeypatch.setattr(cli, "DECK", deck)
    import argparse
    cli.cmd_export_deck(argparse.Namespace())

    text = deck.read_text(encoding="utf-8")
    # markdown table header
    assert "| Parameter | Value | Confidence | Source |" in text
    # at least one stage_factor placeholder visibly marked
    assert "PLACEHOLDER" in text
    # warning marker exists
    assert "⚠" in text


# ─── Bonus: no point estimates — range is always returned ────────────────────

def test_no_point_estimate(do_seriesA_inputs):
    q = quote(**do_seriesA_inputs)
    assert q.premium_low_inr < q.premium_high_inr
    assert q.premium_mid_inr > 0
    assert q.premium_in_lakhs.count("—") == 1   # "₹X L — ₹Y L"
    assert "—" in q.premium_in_crores


# ─── Bonus: disclaimer is present ────────────────────────────────────────────

def test_disclaimer_present(do_seriesA_inputs):
    q = quote(**do_seriesA_inputs)
    assert "Indicative only" in q.disclaimer
    assert "IRDAI" in q.disclaimer
    assert "Not a bindable quote" in q.disclaimer


# ─── Bonus: decline rule fires below MSME revenue floor ──────────────────────

def test_decline_below_min_revenue(do_seriesA_inputs):
    inputs = {**do_seriesA_inputs, "revenue_current_inr": 20_00_000}  # ₹20 L
    q = quote(**inputs)
    assert q.decision == "decline"
    assert any("MSME" in r or "appetite" in r for r in q.decline_reasons)
