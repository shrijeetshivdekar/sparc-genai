"""Integration test for api.extract_documents._build_response()."""

import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

# Import the underlying builder, not the HTTP handler — that's enough for
# verifying the pipeline end to end without standing up a server.
import importlib

_module = importlib.import_module("api.extract_documents")
_build_response = _module._build_response


_PL_TEXT = """
Statement of Profit and Loss for the year ended 31 March 2024

Revenue from operations 3,288 Cr
Cost of goods sold 2,467 Cr
Employee benefit expenses 285 Cr
Profit before tax 821 Cr
"""

_BS_TEXT = """
Balance Sheet as at 31 March 2024

Total assets 4,200 Cr
Property, plant and equipment 842 Cr
Total liabilities 2,100 Cr
Shareholders funds 2,100 Cr
"""

_ITR_TEXT = """
Income Tax Return — Assessment Year 2024-25

Gross turnover 3,288 Cr
Profit before tax 985 Cr
"""


def test_pipeline_pl_only():
    docs = [{"filename": "P&L_FY24.pdf", "text": _PL_TEXT}]
    r = _build_response(docs)

    assert r["status"] == "success"
    assert r["documents_processed"] == 1
    assert r["extraction_summary"]["revenue_cr"]["value"] == 3288.0
    assert r["extraction_summary"]["payroll_cr"]["value"] == 285.0

    assert r["prefill_profile"]["funding_stage"]["value"] == "Series B+"
    # ₹285Cr payroll in ₹100-1000Cr bucket → ₹12L/head → ~2375 employees
    assert r["prefill_profile"]["team_size"]["value"] >= 2000

    assert r["evidence_packet"]["revenue_cr"] == 3288.0


def test_pipeline_pl_plus_bs_plus_itr():
    docs = [
        {"filename": "P&L_FY24.pdf", "text": _PL_TEXT},
        {"filename": "BS_FY24.pdf", "text": _BS_TEXT},
        {"filename": "ITR_2024.pdf", "text": _ITR_TEXT},
    ]
    r = _build_response(docs)

    assert r["status"] == "success"
    assert r["documents_processed"] == 3
    # ITR revenue is stored separately so consistency check can compare
    assert r["extraction_summary"]["itr_revenue_cr"]["value"] == 3288.0
    assert r["extraction_summary"]["total_assets_cr"]["value"] == 4200.0

    statuses = [c["status"] for c in r["consistency_checks"]]
    assert "pass" in statuses  # P&L vs ITR revenue match


def test_pipeline_scanned_image_no_text():
    docs = [{"filename": "scan.pdf", "text": ""}]
    r = _build_response(docs)
    assert r["status"] == "error"
    assert r["documents_processed"] == 1
    assert "scanned image" in r["documents"][0]["extraction_errors"][0].lower()


def test_pipeline_unknown_doc_type():
    docs = [{"filename": "random.pdf", "text": "lorem ipsum dolor"}]
    r = _build_response(docs)
    assert r["status"] == "error"
    assert r["documents"][0]["document_type"] == "unknown"


def test_pipeline_declared_type_overrides_detection():
    # Filename is ambiguous but we declare the type
    docs = [{"filename": "doc.pdf", "text": _PL_TEXT, "detected_type": "pl"}]
    r = _build_response(docs)
    assert r["status"] == "success"
    assert r["documents"][0]["document_type"] == "pl"
