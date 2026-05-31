"""Tests for enrichment.consistency_checker."""

import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from enrichment.consistency_checker import (
    check_revenue_match,
    check_balance_sheet_balance,
    run_all_checks,
)


def test_revenue_match_within_tolerance():
    r = check_revenue_match(itr_revenue=100, pl_revenue=103)
    assert r["status"] == "pass"
    assert r["values"]["variance_pct"] < 5


def test_revenue_match_exceeds_tolerance():
    r = check_revenue_match(itr_revenue=100, pl_revenue=80)
    assert r["status"] == "warning"
    assert r["values"]["variance_pct"] >= 5


def test_revenue_match_not_applicable_when_missing():
    assert check_revenue_match(None, 100)["status"] == "not_applicable"
    assert check_revenue_match(100, None)["status"] == "not_applicable"


def test_balance_sheet_balanced():
    r = check_balance_sheet_balance(assets=100, liabilities=60, equity=40)
    assert r["status"] == "pass"


def test_balance_sheet_within_tolerance():
    r = check_balance_sheet_balance(assets=100, liabilities=60, equity=44, tolerance_cr=5.0)
    assert r["status"] == "pass"  # variance 4 ≤ 5


def test_balance_sheet_warning():
    r = check_balance_sheet_balance(assets=100, liabilities=60, equity=20, tolerance_cr=5.0)
    assert r["status"] == "warning"
    assert r["values"]["variance_cr"] == 20.0


def test_run_all_checks_with_merged_summary():
    merged = {
        "revenue_cr": {"value": 100, "confidence": "extracted"},
        "itr_revenue_cr": {"value": 99, "confidence": "extracted"},
        "total_assets_cr": {"value": 200, "confidence": "extracted"},
        "total_liabilities_cr": {"value": 120, "confidence": "extracted"},
        "equity_cr": {"value": 80, "confidence": "extracted"},
    }
    checks = run_all_checks(merged)
    statuses = [c["status"] for c in checks]
    assert "pass" in statuses
    assert all(s in ("pass", "warning", "not_applicable") for s in statuses)


def test_run_all_checks_with_missing_data():
    merged = {"revenue_cr": {"value": 100, "confidence": "extracted"}}
    checks = run_all_checks(merged)
    assert all(c["status"] == "not_applicable" for c in checks)
