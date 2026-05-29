"""M0 — gwp_estimator contract tests.

Asserts the helper enforces the indicative-range invariants from the PRD
(§4.F3, §6) and Schema (§4): always a range, never a point; integer INR
rupees; IRDAI File-and-Use disclaimer present; bucket selection mirrors
premium_estimator.STARTUP_SIZE_BUCKETS.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import gwp_estimator  # noqa: E402


REQUIRED_KEYS = {"low_inr", "high_inr", "basis", "data_quality", "disclaimer", "per_cover"}


def test_returns_required_keys_and_disclaimer():
    r = gwp_estimator.estimate_gwp(
        {"funding_stage": "Series A", "team_size": 60},
        covers=["Cyber", "D&O", "Group Health"],
    )
    assert REQUIRED_KEYS.issubset(r.keys())
    assert "IRDAI File-and-Use" in r["disclaimer"]
    assert r["disclaimer"] == gwp_estimator.INDICATIVE_DISCLAIMER


def test_low_strictly_less_than_high_for_known_covers():
    r = gwp_estimator.estimate_gwp(
        {"funding_stage": "Series A", "team_size": 60},
        covers=["Cyber", "D&O"],
    )
    assert r["low_inr"] < r["high_inr"]
    assert r["low_inr"] > 0


def test_values_are_ints_not_floats():
    r = gwp_estimator.estimate_gwp(
        {"funding_stage": "Seed", "team_size": 8},
        covers=["Cyber"],
    )
    assert isinstance(r["low_inr"], int)
    assert isinstance(r["high_inr"], int)
    for entry in r["per_cover"]:
        assert isinstance(entry["low_inr"], int)
        assert isinstance(entry["high_inr"], int)


def test_micro_bucket_for_preseed_small_team():
    r = gwp_estimator.estimate_gwp(
        {"funding_stage": "Pre-seed", "team_size": 5},
        covers=["Cyber"],
    )
    assert "bucket=micro" in r["basis"]
    # micro cyber band is 0.5–2.5 lakh = 50_000–250_000 rupees
    cover = r["per_cover"][0]
    assert cover["low_inr"] == 50_000
    assert cover["high_inr"] == 250_000


def test_growth_bucket_for_seriesbplus():
    r = gwp_estimator.estimate_gwp(
        {"funding_stage": "Series B+", "team_size": 200},
        covers=["Cyber"],
    )
    assert "bucket=growth" in r["basis"]
    cover = r["per_cover"][0]
    # growth cyber band 9.0–30.0 lakh
    assert cover["low_inr"] == 900_000
    assert cover["high_inr"] == 3_000_000


def test_per_cover_includes_every_requested_cover():
    covers = ["Cyber", "D&O", "Group Health", "PROPERTY_ALL_RISK"]
    r = gwp_estimator.estimate_gwp(
        {"funding_stage": "Series A", "team_size": 50},
        covers=covers,
    )
    assert len(r["per_cover"]) == len(covers)
    assert [c["cover"] for c in r["per_cover"]] == covers
    # all four should resolve to known band_keys
    assert all(c["band_key"] is not None for c in r["per_cover"])


def test_unknown_cover_does_not_raise_and_penalises_quality():
    r = gwp_estimator.estimate_gwp(
        {"funding_stage": "Series A", "team_size": 50},
        covers=["Cyber", "TotallyMadeUpCover"],
    )
    assert len(r["per_cover"]) == 2
    unknown = next(c for c in r["per_cover"] if c["cover"] == "TotallyMadeUpCover")
    assert unknown["band_key"] is None
    assert unknown["low_inr"] == 0
    assert unknown["high_inr"] == 0
    assert r["data_quality"] == 0.5


def test_aliases_resolve_to_same_band():
    a = gwp_estimator.estimate_gwp(
        {"funding_stage": "Seed", "team_size": 10}, covers=["D&O"],
    )
    b = gwp_estimator.estimate_gwp(
        {"funding_stage": "Seed", "team_size": 10}, covers=["D_AND_O"],
    )
    assert a["low_inr"] == b["low_inr"]
    assert a["high_inr"] == b["high_inr"]


def test_no_covers_returns_zero_range_with_disclaimer():
    r = gwp_estimator.estimate_gwp({"funding_stage": "Seed", "team_size": 10})
    assert r["low_inr"] == 0
    assert r["high_inr"] == 0
    assert "IRDAI File-and-Use" in r["disclaimer"]


def test_delta_gwp_returns_range_and_carries_disclaimer():
    delta = gwp_estimator.estimate_delta_gwp(
        old_profile={"funding_stage": "Seed", "team_size": 10},
        new_profile={"funding_stage": "Series B+", "team_size": 200},
        old_covers=["Cyber"],
        new_covers=["Cyber"],
    )
    assert delta["low_inr"] > 0
    assert delta["high_inr"] > 0
    assert "IRDAI File-and-Use" in delta["disclaimer"]


def test_db_migrate_is_idempotent_and_creates_commerce_tables():
    import tempfile, db
    with tempfile.TemporaryDirectory() as td:
        db_path = Path(td) / "commerce_m0.db"
        db.migrate(db_path)
        db.migrate(db_path)  # second call must not raise
        conn = db.get_conn(db_path)
        try:
            rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).fetchall()
        finally:
            conn.close()
    names = {r["name"] for r in rows}
    expected = {
        "rms", "accounts", "analyses", "gwp_estimates", "pipeline_events",
        "alerts", "proposals", "funding_leads", "events",
    }
    assert expected.issubset(names)


def test_seed_rms_from_contacts_writes_rm_row():
    import tempfile, db
    with tempfile.TemporaryDirectory() as td:
        db_path = Path(td) / "commerce_seed.db"
        db.migrate(db_path)
        written = db.seed_rms_from_contacts(db_path=db_path)
        # contacts.json at repo root has at least one RM record
        assert written >= 1
        conn = db.get_conn(db_path)
        try:
            rms = conn.execute("SELECT rm_email, name FROM rms").fetchall()
        finally:
            conn.close()
        assert len(rms) >= 1
        # second seed must be idempotent (upsert, no duplicate row)
        again = db.seed_rms_from_contacts(db_path=db_path)
        assert again == written
        conn = db.get_conn(db_path)
        try:
            count = conn.execute("SELECT COUNT(*) AS n FROM rms").fetchone()["n"]
        finally:
            conn.close()
        assert count == len(rms)
