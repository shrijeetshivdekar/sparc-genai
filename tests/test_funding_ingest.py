"""M1 — funding_ingest + pipeline_service + commerce_funding contract tests.

Asserts the F5 acceptance criteria from PRD §4:
  - each lead is auto-analysed and valued with bundle + GWP range
  - leads are filterable
  - claim creates an account in Prospect stage and writes events
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import db                                    # noqa: E402
import funding_ingest                        # noqa: E402
import pipeline_service                      # noqa: E402
from api import commerce_funding             # noqa: E402

SAMPLE_CSV = """company,city,sector,stage,amount_inr,round,source,announced_on
Acme HealthTech,Bengaluru,HealthTech,Series A,450000000,Series A,VCCircle,2026-05-22
Northstar Pay,Mumbai,FinTech,Seed,80000000,Seed,Tracxn,2026-05-18
"""


def _fresh_db():
    """Return a (TemporaryDirectory, db_path) tuple. Caller manages cleanup."""
    td = tempfile.TemporaryDirectory()
    return td, Path(td.name) / "m1.db"


# ---------- ingest ----------

def test_ingest_csv_creates_one_lead_per_row():
    td, db_path = _fresh_db()
    try:
        result = funding_ingest.ingest_csv(SAMPLE_CSV, is_text=True, db_path=db_path)
        assert result["ingested"] == 2
        assert len(result["leads"]) == 2
        for lead in result["leads"]:
            assert lead["lead_id"].startswith("lead_")
            assert lead["company"]
    finally:
        td.cleanup()


def test_ingest_csv_values_each_lead_with_gwp_range():
    td, db_path = _fresh_db()
    try:
        result = funding_ingest.ingest_csv(SAMPLE_CSV, is_text=True, db_path=db_path)
        for lead in result["leads"]:
            # Every lead has a non-negative GWP range; low <= high (range, not point).
            assert isinstance(lead["est_gwp_low_inr"], int)
            assert isinstance(lead["est_gwp_high_inr"], int)
            assert lead["est_gwp_low_inr"] >= 0
            assert lead["est_gwp_high_inr"] >= lead["est_gwp_low_inr"]
    finally:
        td.cleanup()


def test_ingest_csv_persists_to_funding_leads_table():
    td, db_path = _fresh_db()
    try:
        funding_ingest.ingest_csv(SAMPLE_CSV, is_text=True, db_path=db_path)
        conn = db.get_conn(db_path)
        try:
            rows = conn.execute("SELECT * FROM funding_leads").fetchall()
        finally:
            conn.close()
        assert len(rows) == 2
        names = {r["company"] for r in rows}
        assert {"Acme HealthTech", "Northstar Pay"} == names
        for r in rows:
            assert r["status"] == "open"
            assert r["source"]   # source attribution required (PRD F5 ACs)
    finally:
        td.cleanup()


def test_list_leads_filters_by_city_and_sector():
    td, db_path = _fresh_db()
    try:
        funding_ingest.ingest_csv(SAMPLE_CSV, is_text=True, db_path=db_path)
        by_blr = funding_ingest.list_leads(city="Bengaluru", db_path=db_path)
        assert len(by_blr) == 1
        assert by_blr[0]["company"] == "Acme HealthTech"
        by_fin = funding_ingest.list_leads(sector="FinTech", db_path=db_path)
        assert len(by_fin) == 1
        assert by_fin[0]["company"] == "Northstar Pay"
    finally:
        td.cleanup()


# ---------- claim ----------

def test_claim_lead_creates_account_in_prospect_stage_and_logs_event():
    td, db_path = _fresh_db()
    try:
        ingested = funding_ingest.ingest_csv(SAMPLE_CSV, is_text=True, db_path=db_path)
        lead_id = ingested["leads"][0]["lead_id"]

        res = pipeline_service.claim_lead(lead_id, "rm@icicilombard.com", db_path=db_path)
        assert res["ok"] is True
        assert res["stage"] == "prospect"
        assert res["account_id"].startswith("acc_")

        conn = db.get_conn(db_path)
        try:
            acct = conn.execute(
                "SELECT * FROM accounts WHERE account_id = ?", (res["account_id"],),
            ).fetchone()
            lead = conn.execute(
                "SELECT * FROM funding_leads WHERE lead_id = ?", (lead_id,),
            ).fetchone()
            pe = conn.execute(
                "SELECT * FROM pipeline_events WHERE account_id = ?", (res["account_id"],),
            ).fetchall()
            ev = conn.execute(
                "SELECT * FROM events WHERE account_id = ?", (res["account_id"],),
            ).fetchall()
        finally:
            conn.close()

        assert acct is not None
        assert acct["stage"] == "prospect"
        assert acct["source"] == "funding_feed"
        assert lead["status"] == "claimed"
        assert lead["claimed_by"] == "rm@icicilombard.com"
        assert lead["account_id"] == res["account_id"]
        assert len(pe) == 1 and pe[0]["to_stage"] == "prospect"
        assert any(e["kind"] == "lead_claimed" for e in ev)
    finally:
        td.cleanup()


def test_claim_is_idempotent_for_same_rm():
    td, db_path = _fresh_db()
    try:
        ingested = funding_ingest.ingest_csv(SAMPLE_CSV, is_text=True, db_path=db_path)
        lead_id = ingested["leads"][0]["lead_id"]
        first  = pipeline_service.claim_lead(lead_id, "rm@x.com", db_path=db_path)
        second = pipeline_service.claim_lead(lead_id, "rm@x.com", db_path=db_path)
        assert second["ok"] is True
        assert second.get("idempotent") is True
        assert second["account_id"] == first["account_id"]
    finally:
        td.cleanup()


def test_claim_blocks_different_rm_on_already_claimed_lead():
    td, db_path = _fresh_db()
    try:
        ingested = funding_ingest.ingest_csv(SAMPLE_CSV, is_text=True, db_path=db_path)
        lead_id = ingested["leads"][0]["lead_id"]
        pipeline_service.claim_lead(lead_id, "rm1@x.com", db_path=db_path)
        blocked = pipeline_service.claim_lead(lead_id, "rm2@x.com", db_path=db_path)
        assert blocked["ok"] is False
        assert "already claimed" in blocked["error"]
    finally:
        td.cleanup()


# ---------- API contract ----------

def test_api_get_returns_leads_and_disclaimer(monkeypatch):
    td, db_path = _fresh_db()
    try:
        funding_ingest.ingest_csv(SAMPLE_CSV, is_text=True, db_path=db_path)
        # The api module's handlers call funding_ingest.list_leads() with the
        # default DB_PATH; point that at our temp DB for the duration.
        monkeypatch.setenv("SPARC_DB_PATH", str(db_path))
        # Reload the affected modules so DB_PATH is re-evaluated.
        import importlib
        importlib.reload(db); importlib.reload(funding_ingest)
        importlib.reload(commerce_funding)

        status, body = commerce_funding.handle_get_request({})
        assert status == 200
        assert body["count"] >= 2
        assert "IRDAI File-and-Use" in body["disclaimer"]
    finally:
        td.cleanup()


def test_api_post_claim_routes_through_pipeline_service(monkeypatch):
    td, db_path = _fresh_db()
    try:
        ingested = funding_ingest.ingest_csv(SAMPLE_CSV, is_text=True, db_path=db_path)
        lead_id = ingested["leads"][0]["lead_id"]

        monkeypatch.setenv("SPARC_DB_PATH", str(db_path))
        import importlib
        importlib.reload(db); importlib.reload(funding_ingest)
        importlib.reload(pipeline_service); importlib.reload(commerce_funding)

        status, body = commerce_funding.handle_post_request({
            "action": "claim", "lead_id": lead_id, "rm_email": "rm@y.com",
        })
        assert status == 200
        assert body["ok"] is True
        assert body["stage"] == "prospect"
    finally:
        td.cleanup()


def test_api_post_unknown_action_returns_400():
    status, body = commerce_funding.handle_post_request({"action": "frobnicate"})
    assert status == 400
    assert "unknown action" in body["error"]
