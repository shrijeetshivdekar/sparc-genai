"""M2 — metrics_service + commerce_dashboard contract tests.

Asserts F1 acceptance criteria from PRD §4:
  - territory_gwp is a range (low/high), never a point
  - funnel includes count + GWP per stage (all 5 stages present)
  - top_leads is sortable by gwp_high (default)
  - every aggregate carries the IRDAI File-and-Use disclaimer
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import db                                    # noqa: E402
import funding_ingest                        # noqa: E402
import metrics_service                       # noqa: E402
import pipeline_service                      # noqa: E402
from api import commerce_dashboard           # noqa: E402

SAMPLE_CSV = """company,city,sector,stage,amount_inr,round,source,announced_on
Acme HealthTech,Bengaluru,HealthTech,Series A,450000000,Series A,VCCircle,2026-05-22
Northstar Pay,Mumbai,FinTech,Seed,80000000,Seed,Tracxn,2026-05-18
GreenLogix,Bengaluru,Logistics,Series B+,1200000000,Series B,VCCircle,2026-05-20
"""


def _fresh_db():
    td = tempfile.TemporaryDirectory()
    return td, Path(td.name) / "m2.db"


def _seed(db_path):
    """Ingest 3 leads, claim 2 of them so accounts populate."""
    ingest = funding_ingest.ingest_csv(SAMPLE_CSV, is_text=True, db_path=db_path)
    pipeline_service.claim_lead(ingest["leads"][0]["lead_id"], "rm@a.com", db_path=db_path)
    pipeline_service.claim_lead(ingest["leads"][1]["lead_id"], "rm@a.com", db_path=db_path)
    return ingest


# ---------- territory_gwp ----------

def test_territory_gwp_is_range_with_disclaimer():
    td, db_path = _fresh_db()
    try:
        _seed(db_path)
        t = metrics_service.territory_gwp(db_path=db_path)
        assert isinstance(t["low_inr"], int) and isinstance(t["high_inr"], int)
        assert t["low_inr"] <= t["high_inr"]
        assert t["low_inr"] > 0  # we seeded real leads
        assert "IRDAI File-and-Use" in t["disclaimer"]
        assert t["account_count"] == 2          # claimed
        assert t["open_lead_count"] == 1        # one un-claimed lead remains
    finally:
        td.cleanup()


def test_territory_gwp_filters_by_city():
    td, db_path = _fresh_db()
    try:
        _seed(db_path)
        blr = metrics_service.territory_gwp(city="Bengaluru", db_path=db_path)
        mum = metrics_service.territory_gwp(city="Mumbai",    db_path=db_path)
        # Bengaluru has Acme (claimed) + GreenLogix (open lead) = 2 contributors
        assert blr["account_count"] + blr["open_lead_count"] == 2
        # Mumbai has Northstar (claimed) only
        assert mum["account_count"] == 1
        assert mum["open_lead_count"] == 0
    finally:
        td.cleanup()


# ---------- funnel ----------

def test_funnel_returns_all_five_stages():
    td, db_path = _fresh_db()
    try:
        _seed(db_path)
        f = metrics_service.funnel(db_path=db_path)
        stages = [r["stage"] for r in f]
        assert stages == ["prospect", "analysed", "quoted", "converted", "lost"]
    finally:
        td.cleanup()


def test_funnel_prospect_row_has_count_and_gwp_range():
    td, db_path = _fresh_db()
    try:
        _seed(db_path)
        f = metrics_service.funnel(db_path=db_path)
        prospect = next(r for r in f if r["stage"] == "prospect")
        # Both claimed accounts land in prospect stage with GWP snapshots.
        assert prospect["count"] == 2
        assert prospect["gwp_low_inr"]  > 0
        assert prospect["gwp_high_inr"] >= prospect["gwp_low_inr"]
        # Stages with no accounts are zero (not missing)
        analysed = next(r for r in f if r["stage"] == "analysed")
        assert analysed["count"] == 0
        assert analysed["gwp_low_inr"] == 0
    finally:
        td.cleanup()


# ---------- top_leads ----------

def test_top_leads_sorted_by_gwp_high_desc_by_default():
    td, db_path = _fresh_db()
    try:
        _seed(db_path)
        leads = metrics_service.top_leads(db_path=db_path, limit=10)
        assert len(leads) >= 1
        gwps = [l["gwp_high_inr"] for l in leads]
        assert gwps == sorted(gwps, reverse=True)
        for l in leads:
            assert l["account_id"].startswith("acc_")
            assert isinstance(l["gwp_low_inr"], int)
            assert isinstance(l["gwp_high_inr"], int)
            assert l["gwp_low_inr"] <= l["gwp_high_inr"]
    finally:
        td.cleanup()


def test_top_leads_respects_limit_and_city_filter():
    td, db_path = _fresh_db()
    try:
        _seed(db_path)
        only_blr = metrics_service.top_leads(city="Bengaluru", db_path=db_path)
        assert all(l["city"] == "Bengaluru" for l in only_blr)
        capped = metrics_service.top_leads(limit=1, db_path=db_path)
        assert len(capped) <= 1
    finally:
        td.cleanup()


# ---------- dashboard payload ----------

def test_dashboard_payload_has_all_keys_and_disclaimer():
    td, db_path = _fresh_db()
    try:
        _seed(db_path)
        d = metrics_service.dashboard(db_path=db_path)
        assert {"territory_gwp", "funnel", "top_leads", "scope", "disclaimer"} <= set(d.keys())
        assert "IRDAI File-and-Use" in d["disclaimer"]
        assert "IRDAI File-and-Use" in d["territory_gwp"]["disclaimer"]
        # Funnel always has 5 stages; top_leads has at least one entry given seed.
        assert len(d["funnel"]) == 5
        assert len(d["top_leads"]) >= 1
    finally:
        td.cleanup()


def test_api_get_dashboard_returns_200_with_payload(monkeypatch):
    td, db_path = _fresh_db()
    try:
        _seed(db_path)
        monkeypatch.setenv("SPARC_DB_PATH", str(db_path))
        import importlib
        importlib.reload(db); importlib.reload(metrics_service); importlib.reload(commerce_dashboard)
        status, body = commerce_dashboard.handle_get_request({})
        assert status == 200
        assert "territory_gwp" in body
        assert "funnel" in body
        assert "top_leads" in body
        assert "IRDAI File-and-Use" in body["disclaimer"]
    finally:
        td.cleanup()


# ─── M4: RM Performance ────────────────────────────────────────

import json as _json                                # noqa: E402
import proposal_builder                             # noqa: E402
from api import commerce_metrics                    # noqa: E402

_ANALYSIS = {
    "profile": {"startup_name": "Acme HealthTech", "sector": "HealthTech",
                "funding_stage": "Series A", "team_size": 60, "city": "Bengaluru"},
    "bundle_match": {"name": "HealthTech Enterprise Secure", "fit_pct": 88,
                     "mandatory_covers": [{"name": "Cyber", "why": "DPDPA"}]},
}


def _seed_with_events(db_path):
    """Seed a richer activity history so leaderboard / digest have real shape:
    claims by two RMs, one proposal generated, one converted event.
    """
    ingest = funding_ingest.ingest_csv(SAMPLE_CSV, is_text=True, db_path=db_path)
    claim_a = pipeline_service.claim_lead(ingest["leads"][0]["lead_id"], "rm.a@x.com", db_path=db_path)
    pipeline_service.claim_lead(ingest["leads"][1]["lead_id"],         "rm.a@x.com", db_path=db_path)
    pipeline_service.claim_lead(ingest["leads"][2]["lead_id"],         "rm.b@x.com", db_path=db_path)
    proposal_builder.generate_proposal(claim_a["account_id"], _ANALYSIS, db_path=db_path)
    # Manually log a 'converted' event so conversion metrics have signal.
    conn = db.get_conn(db_path)
    try:
        with conn:
            conn.execute(
                "INSERT INTO events (kind, rm_email, account_id, gwp_low_inr, gwp_high_inr, meta_json) "
                "VALUES ('quoted', 'rm.a@x.com', ?, 1500000, 4500000, ?)",
                (claim_a["account_id"], _json.dumps({"note": "test quote"})),
            )
            conn.execute(
                "INSERT INTO events (kind, rm_email, account_id, gwp_low_inr, gwp_high_inr, meta_json) "
                "VALUES ('converted', 'rm.a@x.com', ?, 1500000, 4500000, ?)",
                (claim_a["account_id"], _json.dumps({"note": "test convert"})),
            )
    finally:
        conn.close()
    return ingest, claim_a


def test_leaderboard_returns_one_row_per_rm_with_pipeline_gwp():
    td, db_path = _fresh_db()
    try:
        _seed_with_events(db_path)
        lb = metrics_service.rm_leaderboard(db_path=db_path)
        emails = {r["rm_email"] for r in lb}
        assert "rm.a@x.com" in emails
        assert "rm.b@x.com" in emails
        rm_a = next(r for r in lb if r["rm_email"] == "rm.a@x.com")
        assert rm_a["claimed"]    == 2
        assert rm_a["proposals"]  == 1
        assert rm_a["quoted"]     == 1
        assert rm_a["converted"]  == 1
        assert rm_a["pipeline_gwp_high"] > 0
        assert rm_a["conversion_rate"] == 1.0   # 1 converted / 1 quoted
    finally:
        td.cleanup()


def test_conversion_by_sector_returns_rate():
    td, db_path = _fresh_db()
    try:
        _seed_with_events(db_path)
        conv = metrics_service.conversion_by_sector(db_path=db_path)
        assert any(r["sector"] == "HealthTech" for r in conv)
        ht = next(r for r in conv if r["sector"] == "HealthTech")
        assert ht["quoted"] == 1
        assert ht["converted"] == 1
        assert ht["conv_rate"] == 1.0
    finally:
        td.cleanup()


def test_weekly_digest_has_headline_totals_top_rm():
    td, db_path = _fresh_db()
    try:
        _seed_with_events(db_path)
        digest = metrics_service.weekly_digest(db_path=db_path)
        assert digest["headline"]
        assert digest["totals"]["proposals"] == 1
        assert digest["totals"]["claimed"]   == 3
        assert digest["totals"]["converted"] == 1
        assert digest["top_rm"]["rm_email"]  == "rm.a@x.com"
        assert "IRDAI File-and-Use" in digest["disclaimer"]
    finally:
        td.cleanup()


def test_metrics_payload_has_all_keys_and_disclaimer():
    td, db_path = _fresh_db()
    try:
        _seed_with_events(db_path)
        m = metrics_service.metrics(db_path=db_path)
        for k in ("leaderboard", "conversion_by_sector", "speed", "digest", "disclaimer"):
            assert k in m
        assert "IRDAI File-and-Use" in m["disclaimer"]
        assert "prospect_to_analysed" in m["speed"]
    finally:
        td.cleanup()


def test_api_get_metrics_returns_200(monkeypatch):
    td, db_path = _fresh_db()
    try:
        _seed_with_events(db_path)
        monkeypatch.setenv("SPARC_DB_PATH", str(db_path))
        import importlib
        importlib.reload(db); importlib.reload(metrics_service); importlib.reload(commerce_metrics)
        status, body = commerce_metrics.handle_get_request({})
        assert status == 200
        assert any(r["rm_email"] == "rm.a@x.com" for r in body["leaderboard"])
    finally:
        td.cleanup()


def test_api_post_send_digest_returns_payload(monkeypatch):
    td, db_path = _fresh_db()
    try:
        _seed_with_events(db_path)
        monkeypatch.setenv("SPARC_DB_PATH", str(db_path))
        import importlib
        importlib.reload(db); importlib.reload(metrics_service); importlib.reload(commerce_metrics)
        status, body = commerce_metrics.handle_post_request({"action": "send_digest"})
        assert status == 200
        assert body["ok"] is True
        assert body["dispatched"] is True
        assert body["digest"]["totals"]["proposals"] == 1
    finally:
        td.cleanup()


def test_api_post_metrics_unknown_action_400():
    status, body = commerce_metrics.handle_post_request({"action": "frobnicate"})
    assert status == 400
    assert "unknown action" in body["error"]
