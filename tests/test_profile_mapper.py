"""Tests for enrichment.profile_mapper."""

import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from enrichment.profile_mapper import (
    revenue_to_funding_stage,
    payroll_to_team_size,
    map_extracts_to_profile,
    build_evidence_packet,
)


# ── revenue bucket boundaries ───────────────────────────────────────────────

def test_revenue_buckets():
    assert revenue_to_funding_stage(0.5) == "Pre-seed"
    assert revenue_to_funding_stage(0.99) == "Pre-seed"
    assert revenue_to_funding_stage(1) == "Seed"
    assert revenue_to_funding_stage(9.99) == "Seed"
    assert revenue_to_funding_stage(10) == "Series A"
    assert revenue_to_funding_stage(99.99) == "Series A"
    assert revenue_to_funding_stage(100) == "Series B+"
    assert revenue_to_funding_stage(3288) == "Series B+"
    assert revenue_to_funding_stage(None) is None


# ── payroll → team_size ─────────────────────────────────────────────────────

def test_payroll_to_team_size_typical():
    # ₹8 Cr is in the <₹10 Cr bucket → ₹6L/head → 133 people
    assert payroll_to_team_size(8) == 133


def test_payroll_to_team_size_small_company():
    # ₹1 Cr ÷ ₹6L ≈ 17 people
    n = payroll_to_team_size(1)
    assert 15 <= n <= 20


def test_payroll_to_team_size_none_or_zero():
    assert payroll_to_team_size(None) is None
    assert payroll_to_team_size(0) is None


# ── full mapping ────────────────────────────────────────────────────────────

def test_map_full_extraction():
    summary = {
        "revenue_cr": {"value": 50, "confidence": "extracted"},
        "payroll_cr": {"value": 8, "confidence": "extracted"},
    }
    pre = map_extracts_to_profile(summary)
    assert pre["funding_stage"]["value"] == "Series A"
    # ₹8 Cr payroll in <₹10 Cr bucket → ₹6L/head → 133
    assert pre["team_size"]["value"] == 133


def test_map_falls_back_to_itr_revenue_when_no_pl():
    summary = {
        "itr_revenue_cr": {"value": 200, "confidence": "extracted"},
    }
    pre = map_extracts_to_profile(summary)
    assert pre["funding_stage"]["value"] == "Series B+"
    assert "ITR" in pre["funding_stage"]["source"]


def test_map_empty_returns_empty():
    assert map_extracts_to_profile({}) == {}


# ── evidence packet ─────────────────────────────────────────────────────────

def test_evidence_packet_assembles_display_numbers():
    summary = {
        "revenue_cr": {"value": 100},
        "gross_profit_cr": {"value": 30},
        "total_assets_cr": {"value": 500},
    }
    ev = build_evidence_packet(summary)
    assert ev["revenue_cr"] == 100
    assert ev["gross_profit_cr"] == 30
    assert ev["total_assets_cr"] == 500
    assert ev["equity_cr"] is None
