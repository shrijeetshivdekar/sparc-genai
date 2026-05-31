"""Tests for enrichment.document_extractor."""

import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from enrichment.document_extractor import (
    detect_type,
    extract_pl_fields,
    extract_bs_fields,
    extract_itr_fields,
)


# ── detect_type ─────────────────────────────────────────────────────────────

def test_detect_type_from_filename_pl():
    assert detect_type("P&L_FY2024.pdf", "") == "pl"
    assert detect_type("profit_loss.pdf", "") == "pl"
    assert detect_type("pnl_q3.pdf", "") == "pl"


def test_detect_type_from_filename_bs():
    assert detect_type("balance_sheet.pdf", "") == "balance_sheet"
    assert detect_type("BSheet_2024.pdf", "") == "balance_sheet"


def test_detect_type_from_filename_itr():
    assert detect_type("ITR_2024.pdf", "") == "itr"
    assert detect_type("income_tax_return.pdf", "") == "itr"


def test_detect_type_from_content_when_filename_neutral():
    assert detect_type("doc1.pdf", "Statement of Profit and Loss for the year") == "pl"
    assert detect_type("doc2.pdf", "Total assets and liabilities and equity ...") == "balance_sheet"


def test_detect_type_unknown():
    assert detect_type("random.pdf", "lorem ipsum") == "unknown"


# ── P&L extraction ──────────────────────────────────────────────────────────

def test_pl_revenue_simple_cr():
    text = "Revenue from operations ₹3,288.50 Cr"
    out = extract_pl_fields(text)
    assert out["revenue_cr"]["value"] == 3288.5
    assert out["revenue_cr"]["confidence"] == "extracted"


def test_pl_revenue_lakh_normalised_to_cr():
    text = "Total revenue Rs 500 lakh"
    out = extract_pl_fields(text)
    assert out["revenue_cr"]["value"] == 5.0  # 500 lakh = 5 Cr


def test_pl_gross_profit_calculated_when_missing():
    text = "Sales 100 Cr\nCost of goods sold 60 Cr"
    out = extract_pl_fields(text)
    assert out["revenue_cr"]["value"] == 100.0
    assert out["cogs_cr"]["value"] == 60.0
    assert out["gross_profit_cr"]["value"] == 40.0
    assert out["gross_profit_cr"]["confidence"] == "calculated"


def test_pl_gross_profit_extracted_overrides_calculated():
    text = "Sales 100 Cr\nCost of goods sold 60 Cr\nGross profit 41 Cr"
    out = extract_pl_fields(text)
    assert out["gross_profit_cr"]["value"] == 41.0
    assert out["gross_profit_cr"]["confidence"] == "extracted"


def test_pl_payroll_employee_benefit():
    text = "Employee benefit expenses 285 Cr"
    out = extract_pl_fields(text)
    assert out["payroll_cr"]["value"] == 285.0


def test_pl_not_found_returns_none():
    out = extract_pl_fields("absolutely no numbers here")
    assert out["revenue_cr"]["value"] is None
    assert out["revenue_cr"]["confidence"] == "not_found"


# ── Balance Sheet extraction ────────────────────────────────────────────────

def test_bs_total_assets():
    text = "TOTAL ASSETS 4,200.00 Cr"
    out = extract_bs_fields(text)
    assert out["total_assets_cr"]["value"] == 4200.0


def test_bs_equity_calculated_when_missing():
    text = "Total assets 100 Cr\nTotal liabilities 60 Cr"
    out = extract_bs_fields(text)
    assert out["equity_cr"]["value"] == 40.0
    assert out["equity_cr"]["confidence"] == "calculated"


def test_bs_fixed_assets_ppe():
    text = "Property, plant and equipment 842 Cr"
    out = extract_bs_fields(text)
    assert out["fixed_assets_cr"]["value"] == 842.0


# ── ITR extraction ──────────────────────────────────────────────────────────

def test_itr_revenue_gross_turnover():
    text = "Gross turnover Rs 3288 Cr"
    out = extract_itr_fields(text)
    assert out["revenue_cr"]["value"] == 3288.0


def test_itr_profit_before_tax():
    text = "Profit before tax 985 Cr"
    out = extract_itr_fields(text)
    assert out["profit_cr"]["value"] == 985.0
