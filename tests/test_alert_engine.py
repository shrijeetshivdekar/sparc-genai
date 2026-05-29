"""M5 — alert_engine + commerce_alerts contract tests.

Asserts F4 acceptance criteria from PRD §4:
  - alert fires on the correct threshold (renewal ≤60d, upsell on stage,
    coverage_gap on new triggers)
  - each alert carries a typed reason + delta-GWP range
  - at_risk = renewal due ≤60d AND no engagement ≤90d
  - alerts dismissible
  - re-running evaluate doesn't create duplicate open alerts
"""

from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import db                                  # noqa: E402
import alert_engine                        # noqa: E402
import funding_ingest                      # noqa: E402
import pipeline_service                    # noqa: E402
from api import commerce_alerts            # noqa: E402

SAMPLE_CSV = """company,city,sector,stage,amount_inr,round,source,announced_on
Acme HealthTech,Bengaluru,HealthTech,Series A,450000000,Series A,VCCircle,2026-05-22
"""


def _fresh_db():
    td = tempfile.TemporaryDirectory()
    return td, Path(td.name) / "m5.db"


def _seed_one_account(db_path):
    ingest = funding_ingest.ingest_csv(SAMPLE_CSV, is_text=True, db_path=db_path)
    claim = pipeline_service.claim_lead(
        ingest["leads"][0]["lead_id"], "rm@m5.com", db_path=db_path,
    )
    return claim["account_id"]


def _set_account_field(db_path, account_id: str, field: str, value):
    conn = db.get_conn(db_path)
    try:
        with conn:
            conn.execute(f"UPDATE accounts SET {field} = ? WHERE account_id = ?",
                         (value, account_id))
    finally:
        conn.close()


# ─── renewal ──────────────────────────────────────────────────

def test_renewal_alert_fires_within_60d_window():
    td, db_path = _fresh_db()
    try:
        acct_id = _seed_one_account(db_path)
        due = (datetime.utcnow().date() + timedelta(days=30)).isoformat()
        _set_account_field(db_path, acct_id, "renewal_due_on", due)
        new = alert_engine.evaluate_account(acct_id, db_path=db_path)
        kinds = [a["type"] for a in new]
        assert "renewal" in kinds
        a = next(a for a in new if a["type"] == "renewal")
        assert "Renewal due" in a["reason"]
        assert a["delta_gwp_high_inr"] >= a["delta_gwp_low_inr"]
        assert a["trigger_detail"]["days_to_renewal"] == 30
    finally:
        td.cleanup()


def test_renewal_alert_does_not_fire_outside_window():
    td, db_path = _fresh_db()
    try:
        acct_id = _seed_one_account(db_path)
        due = (datetime.utcnow().date() + timedelta(days=120)).isoformat()
        _set_account_field(db_path, acct_id, "renewal_due_on", due)
        new = alert_engine.evaluate_account(acct_id, db_path=db_path)
        assert not any(a["type"] == "renewal" for a in new)
    finally:
        td.cleanup()


# ─── at-risk ──────────────────────────────────────────────────

def test_at_risk_requires_both_renewal_and_no_engagement():
    """PRD: at_risk = renewal due ≤60d AND no engagement ≤90d."""
    td, db_path = _fresh_db()
    try:
        acct_id = _seed_one_account(db_path)
        due = (datetime.utcnow().date() + timedelta(days=20)).isoformat()
        # last_engaged 120 days ago — well past the 90d at-risk threshold
        engaged = (datetime.utcnow().date() - timedelta(days=120)).isoformat()
        _set_account_field(db_path, acct_id, "renewal_due_on", due)
        _set_account_field(db_path, acct_id, "last_engaged_on", engaged)
        new = alert_engine.evaluate_account(acct_id, db_path=db_path)
        kinds = [a["type"] for a in new]
        assert "at_risk" in kinds
        a = next(a for a in new if a["type"] == "at_risk")
        # at-risk delta is negative (potential loss)
        assert a["delta_gwp_low_inr"]  <= 0
        assert a["delta_gwp_high_inr"] <= 0
        assert a["trigger_detail"]["days_since_engagement"] >= 90
    finally:
        td.cleanup()


def test_at_risk_does_not_fire_if_recently_engaged():
    td, db_path = _fresh_db()
    try:
        acct_id = _seed_one_account(db_path)
        due = (datetime.utcnow().date() + timedelta(days=20)).isoformat()
        engaged = (datetime.utcnow().date() - timedelta(days=10)).isoformat()
        _set_account_field(db_path, acct_id, "renewal_due_on", due)
        _set_account_field(db_path, acct_id, "last_engaged_on", engaged)
        new = alert_engine.evaluate_account(acct_id, db_path=db_path)
        # renewal fires (window match), at_risk does NOT (recent engagement)
        assert any(a["type"] == "renewal"  for a in new)
        assert not any(a["type"] == "at_risk" for a in new)
    finally:
        td.cleanup()


# ─── upsell ──────────────────────────────────────────────────

def test_upsell_alert_carries_positive_delta_gwp_range():
    td, db_path = _fresh_db()
    try:
        acct_id = _seed_one_account(db_path)   # Series A claimed via lead
        new = alert_engine.evaluate_account(acct_id, db_path=db_path)
        ups = [a for a in new if a["type"] == "upsell"]
        assert ups, "Series A account should suggest upsell to Series B+"
        a = ups[0]
        assert a["delta_gwp_low_inr"]  > 0
        assert a["delta_gwp_high_inr"] > a["delta_gwp_low_inr"]
        assert a["trigger_detail"]["old"] == "Series A"
        assert a["trigger_detail"]["new"] == "Series B+"
    finally:
        td.cleanup()


# ─── coverage gap ─────────────────────────────────────────────

def test_coverage_gap_alert_fires_when_new_triggers_supplied():
    td, db_path = _fresh_db()
    try:
        acct_id = _seed_one_account(db_path)
        new = alert_engine.evaluate_account(
            acct_id, new_triggers=["Cyber", "D&O"], db_path=db_path,
        )
        gaps = [a for a in new if a["type"] == "coverage_gap"]
        assert gaps
        a = gaps[0]
        assert "Cyber" in a["reason"] or "D&O" in a["reason"]
        assert a["delta_gwp_high_inr"] >= a["delta_gwp_low_inr"]
        assert a["delta_gwp_low_inr"] > 0
    finally:
        td.cleanup()


# ─── idempotency + dismiss ───────────────────────────────────

def test_evaluate_is_idempotent_for_same_open_alert():
    td, db_path = _fresh_db()
    try:
        acct_id = _seed_one_account(db_path)
        due = (datetime.utcnow().date() + timedelta(days=30)).isoformat()
        _set_account_field(db_path, acct_id, "renewal_due_on", due)
        first  = alert_engine.evaluate_account(acct_id, db_path=db_path)
        second = alert_engine.evaluate_account(acct_id, db_path=db_path)
        renewals_first = [a for a in first  if a["type"] == "renewal"]
        renewals_second= [a for a in second if a["type"] == "renewal"]
        assert len(renewals_first)  == 1
        assert len(renewals_second) == 0  # not re-inserted
    finally:
        td.cleanup()


def test_dismiss_alert_marks_status_dismissed_and_is_idempotent():
    td, db_path = _fresh_db()
    try:
        acct_id = _seed_one_account(db_path)
        new = alert_engine.evaluate_account(acct_id, db_path=db_path)
        target = new[0]
        res = alert_engine.dismiss_alert(target["alert_id"], rm_email="rm@m5.com", db_path=db_path)
        assert res["ok"] is True
        assert res["status"] == "dismissed"
        again = alert_engine.dismiss_alert(target["alert_id"], db_path=db_path)
        assert again["ok"] is True
        assert again.get("idempotent") is True
    finally:
        td.cleanup()


# ─── sweep + summary ─────────────────────────────────────────

def test_evaluate_all_walks_every_tracked_account():
    td, db_path = _fresh_db()
    try:
        _seed_one_account(db_path)
        res = alert_engine.evaluate_all(db_path=db_path)
        assert res["swept"] >= 1
        # Series A account should at minimum get an upsell alert.
        assert res["created"] >= 1
    finally:
        td.cleanup()


def test_at_risk_summary_aggregates_open_renewals():
    td, db_path = _fresh_db()
    try:
        acct_id = _seed_one_account(db_path)
        due = (datetime.utcnow().date() + timedelta(days=10)).isoformat()
        engaged = (datetime.utcnow().date() - timedelta(days=120)).isoformat()
        _set_account_field(db_path, acct_id, "renewal_due_on", due)
        _set_account_field(db_path, acct_id, "last_engaged_on", engaged)
        alert_engine.evaluate_account(acct_id, db_path=db_path)
        s = alert_engine.at_risk_summary(db_path=db_path)
        assert s["renewal_count"]  >= 1
        assert s["at_risk_count"]  >= 1
        assert s["renewal_gwp_high_inr"] > 0
    finally:
        td.cleanup()


# ─── API contract ────────────────────────────────────────────

def test_api_get_alerts_returns_summary_and_disclaimer(monkeypatch):
    td, db_path = _fresh_db()
    try:
        acct_id = _seed_one_account(db_path)
        alert_engine.evaluate_account(acct_id, db_path=db_path)
        monkeypatch.setenv("SPARC_DB_PATH", str(db_path))
        import importlib
        importlib.reload(db); importlib.reload(alert_engine); importlib.reload(commerce_alerts)
        status, body = commerce_alerts.handle_get_request({})
        assert status == 200
        assert "alerts"  in body
        assert "summary" in body
        assert "IRDAI File-and-Use" in body["disclaimer"]
        # Sort: highest delta first
        alerts = body["alerts"]
        if len(alerts) >= 2:
            assert alerts[0]["delta_gwp_high_inr"] >= alerts[1]["delta_gwp_high_inr"]
    finally:
        td.cleanup()


def test_api_post_dismiss_updates_alert(monkeypatch):
    td, db_path = _fresh_db()
    try:
        acct_id = _seed_one_account(db_path)
        new = alert_engine.evaluate_account(acct_id, db_path=db_path)
        target = new[0]
        monkeypatch.setenv("SPARC_DB_PATH", str(db_path))
        import importlib
        importlib.reload(db); importlib.reload(alert_engine); importlib.reload(commerce_alerts)
        status, body = commerce_alerts.handle_post_request({
            "action": "dismiss", "alert_id": target["alert_id"], "rm_email": "rm@m5.com",
        })
        assert status == 200
        assert body["ok"] is True
    finally:
        td.cleanup()


def test_api_post_unknown_action_returns_400():
    status, body = commerce_alerts.handle_post_request({"action": "frobnicate"})
    assert status == 400
    assert "unknown action" in body["error"]
