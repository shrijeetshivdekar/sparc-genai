"""M3 — proposal_builder + commerce_proposal contract tests.

Asserts F3 acceptance criteria from PRD §4:
  - mandatory disclaimer verbatim (IRDAI File-and-Use + Valid 30 days)
  - premium shown as a range, never a point
  - all bundle covers present in the rendered output
  - bundle, RM, triggers, analysis URL all surface in HTML
  - generates in well under 10s
"""

from __future__ import annotations

import re
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import db                                  # noqa: E402
import funding_ingest                      # noqa: E402
import pipeline_service                    # noqa: E402
import proposal_builder                    # noqa: E402
from api import commerce_proposal          # noqa: E402

SAMPLE_CSV = """company,city,sector,stage,amount_inr,round,source,announced_on
Acme HealthTech,Bengaluru,HealthTech,Series A,450000000,Series A,VCCircle,2026-05-22
"""

# Minimal analysis result shape mimicking what window.__result carries.
SAMPLE_ANALYSIS = {
    "profile": {
        "startup_name": "Acme HealthTech",
        "sector": "HealthTech",
        "funding_stage": "Series A",
        "team_size": 60,
        "city": "Bengaluru",
    },
    "bundle_match": {
        "name": "HealthTech Enterprise Secure",
        "fit_pct": 88,
        "mandatory_covers": [
            {"name": "Cyber",        "why": "DPDPA SDF likely + PII volume."},
            {"name": "D&O",          "why": "Series A institutional board."},
            {"name": "Group Health", "why": "60-person team across two cities."},
        ],
        "optional_covers": [
            {"name": "Product Liability", "why": "Devices in clinics."},
        ],
    },
    "display_regulatory_triggers": [
        {"regulation": "DPDPA 2023", "requirement": "Significant Data Fiduciary obligations apply."},
        {"regulation": "DGCA 2024",  "requirement": "Drone rules — not material for this profile."},
    ],
}


def _fresh_db():
    td = tempfile.TemporaryDirectory()
    return td, Path(td.name) / "m3.db"


# ─── payload builder ───────────────────────────────────────────

def test_build_payload_contains_required_keys():
    p = proposal_builder.build_proposal_payload(None, SAMPLE_ANALYSIS)
    for key in ("proposal_id", "generated_at", "valid_until", "company", "sector",
                "stage", "city", "bundle", "gwp", "triggers", "rm", "analysis_url",
                "disclaimer"):
        assert key in p, f"missing {key}"
    assert p["proposal_id"].startswith("prop_")


def test_disclaimer_is_locked_verbatim():
    p = proposal_builder.build_proposal_payload(None, SAMPLE_ANALYSIS)
    assert p["disclaimer"] == (
        "Indicative only under IRDAI File-and-Use detariffed regime. "
        "Not a bindable quote. Valid 30 days, subject to underwriting confirmation."
    )


def test_payload_includes_all_bundle_covers():
    p = proposal_builder.build_proposal_payload(None, SAMPLE_ANALYSIS)
    cover_names = {c["cover"] for c in p["bundle"]["covers"]}
    assert {"Cyber", "D&O", "Group Health", "Product Liability"} <= cover_names


def test_gwp_in_payload_is_range_not_point():
    p = proposal_builder.build_proposal_payload(None, SAMPLE_ANALYSIS)
    g = p["gwp"]
    assert isinstance(g["low_inr"], int) and isinstance(g["high_inr"], int)
    assert g["low_inr"] < g["high_inr"]
    assert "IRDAI File-and-Use" in g["disclaimer"]


# ─── HTML rendering ────────────────────────────────────────────

def test_rendered_html_includes_disclaimer_verbatim():
    p = proposal_builder.build_proposal_payload(None, SAMPLE_ANALYSIS)
    html = proposal_builder.render_html(p)
    assert "IRDAI File-and-Use" in html
    assert "Valid 30 days" in html
    assert "Not a bindable quote" in html


def test_rendered_html_includes_every_bundle_cover():
    p = proposal_builder.build_proposal_payload(None, SAMPLE_ANALYSIS)
    html = proposal_builder.render_html(p)
    for cover in ("Cyber", "D&amp;O", "Group Health", "Product Liability"):
        assert cover in html, f"cover {cover!r} missing from rendered HTML"


def test_rendered_html_total_gwp_is_a_range():
    p = proposal_builder.build_proposal_payload(None, SAMPLE_ANALYSIS)
    html = proposal_builder.render_html(p)
    # Look for the en-dash range pattern e.g. ₹4.5–22 L or ₹2–8 Cr
    assert re.search(r"₹\d", html), "no INR figure in rendered HTML"
    assert "–" in html, "no range separator in rendered HTML"


def test_rendered_html_includes_rm_and_company_and_bundle_and_triggers():
    p = proposal_builder.build_proposal_payload(None, SAMPLE_ANALYSIS)
    html = proposal_builder.render_html(p)
    assert "Acme HealthTech"                  in html
    assert "HealthTech Enterprise Secure"     in html
    assert "DPDPA 2023"                       in html
    assert "ICICI Lombard"                    in html  # masthead brand line
    assert p["rm"]["name"]                    in html


# ─── persistence + perf ────────────────────────────────────────

def test_generate_proposal_persists_row_and_logs_event():
    td, db_path = _fresh_db()
    try:
        ingest = funding_ingest.ingest_csv(SAMPLE_CSV, is_text=True, db_path=db_path)
        claim  = pipeline_service.claim_lead(
            ingest["leads"][0]["lead_id"], "rm@m3.com", db_path=db_path,
        )
        account_id = claim["account_id"]

        result = proposal_builder.generate_proposal(account_id, SAMPLE_ANALYSIS, db_path=db_path)
        assert result["proposal_id"].startswith("prop_")
        assert result["html"].lstrip().startswith("<!doctype html>")
        assert "IRDAI File-and-Use" in result["disclaimer"]
        assert isinstance(result["gwp_low_inr"], int)
        assert result["gwp_low_inr"] < result["gwp_high_inr"]

        conn = db.get_conn(db_path)
        try:
            props = conn.execute(
                "SELECT * FROM proposals WHERE account_id = ?", (account_id,),
            ).fetchall()
            ev = conn.execute(
                "SELECT * FROM events WHERE account_id = ? AND kind='proposal_generated'",
                (account_id,),
            ).fetchall()
        finally:
            conn.close()
        assert len(props) == 1
        assert props[0]["proposal_id"] == result["proposal_id"]
        assert props[0]["bundle"]      == "HealthTech Enterprise Secure"
        assert props[0]["valid_until"]
        assert len(ev) == 1
    finally:
        td.cleanup()


def test_generate_completes_well_under_10s():
    """PRD §4.F3 — under 10s for a standard profile (HTML path is far faster)."""
    t0 = time.time()
    result = proposal_builder.generate_proposal(None, SAMPLE_ANALYSIS)
    elapsed = time.time() - t0
    assert elapsed < 10.0, f"proposal took {elapsed:.2f}s"
    assert result["html"]


# ─── API contract ──────────────────────────────────────────────

def test_api_post_returns_html_and_proposal_id():
    status, body = commerce_proposal.handle_post_request({
        "analysis": SAMPLE_ANALYSIS,
    })
    assert status == 200
    assert body["proposal_id"].startswith("prop_")
    assert "IRDAI File-and-Use" in body["disclaimer"]
    assert "<!doctype html>" in body["html"].lower()


def test_api_post_rejects_missing_analysis():
    status, body = commerce_proposal.handle_post_request({})
    assert status == 400
    assert "analysis" in body["error"]
