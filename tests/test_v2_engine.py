import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from bundle_recommender_v2 import compliance_flags, rank
from bundle_scoring_utils import load_config
from product_catalogue_v2 import PRODUCTS
from startup_shield_web import server


BASE_SCORES = {
    "Cyber Technical Risk": 78,
    "Data Privacy Risk": 76,
    "Liability Risk": 62,
    "IP Infringement Risk": 58,
    "Key Person Risk": 54,
    "Governance & Fraud Risk": 70,
    "Property Risk": 35,
    "Regulatory Compliance Risk": 74,
    "ESG & Climate Risk": 28,
    "Geopolitical Risk": 42,
    "Gig & Labour Risk": 30,
    "Policy Velocity Risk": 65,
    "Reputation Risk": 60,
}


def _profile(**overrides):
    profile = {
        "startup_name": "V2 Test",
        "sector": "Fintech",
        "funding_stage": "Series A",
        "team_size": 55,
        "operations": "Digital-only",
        "data_sensitivity": "High",
        "data_handled": [
            "Payments / financial transactions",
            "Personal identity data (KYC / Aadhaar)",
        ],
        "regulatory": ["RBI / SEBI / IRDAI licensed", "DPDP Act obligations"],
        "physical_assets": ["Office / coworking space"],
        "hardware_software_split": 0.0,
        "gig_headcount_pct": 0.0,
        "scores": dict(BASE_SCORES),
    }
    profile.update(overrides)
    return profile


def test_load_config_validates_and_exposes_typed_values():
    cfg = load_config()
    assert cfg.config_version == "2026.05"
    assert abs(sum(cfg.risk_weights.as_dict().values()) - 1.0) < 1e-6
    assert len(cfg.bundle_meta) == 13


def test_product_registry_life_products_are_routed_outside_lombard_bundles():
    cfg = load_config()
    life_uins = {p.uin for p in PRODUCTS.values() if p.route_to_life_insurer}
    assert {"GROUP_TERM_LIFE", "KEY_PERSON_LIFE"} <= life_uins
    for bm in cfg.bundle_meta.values():
        assert not (set(bm.components) & life_uins)


def test_series_a_fintech_v2_ranks_startup_shield():
    recs = rank(_profile())
    assert recs
    assert recs[0].bundle == "Business Shield SME"
    assert recs[0].config_version == "2026.05"
    assert {"coverage", "revenue", "risk_multiplier"} <= set(recs[0].rationale)


def test_deeptech_drone_profile_is_blocked_when_no_bundle_contains_drone_cover():
    recs = rank(_profile(
        sector="Deeptech / AI / Robotics",
        funding_stage="Series A",
        physical_assets=["Lab / R&D equipment", "Drones / UAV equipment"],
        hardware_software_split=0.55,
        regulatory=["DGCA / drone operations"],
        drone_ops=True,
        total_insurable_asset_value_cr=60,
        asset_value_inr=600_000_000,
        scores={**BASE_SCORES, "IP Infringement Risk": 85, "Property Risk": 78},
    ))
    assert recs == []


def test_series_b_d2c_v2_ranks_corporate_cover():
    recs = rank(_profile(
        sector="D2C / Consumer Brands",
        funding_stage="Series B+",
        operations="Hybrid",
        physical_assets=["Manufacturing plant / factory", "Warehouse / fulfilment centre"],
        hardware_software_split=0.75,
        scores={**BASE_SCORES, "Liability Risk": 86, "Property Risk": 82, "Reputation Risk": 78},
    ))
    assert recs
    assert recs[0].bundle == "Corporate Cover II"


def test_compliance_flags_fire_for_drone_profile_without_drone_product():
    cfg = load_config()
    bm = cfg.bundle_meta["Business_Shield_SME"]
    flags = compliance_flags(bm, _profile(
        sector="Deeptech / AI / Robotics",
        regulatory=["DGCA / drone operations"],
        drone_ops=True,
    ), cfg)
    assert any(flag["required_product"] == "Drone_RPAS" for flag in flags)


def test_bharat_sookshma_rejected_above_si_cap():
    recs = rank(_profile(
        sector="D2C / Consumer Brands",
        funding_stage="Seed",
        asset_value_inr=60_000_000,
        physical_assets=["Warehouse / fulfilment centre"],
        scores={**BASE_SCORES, "Property Risk": 80},
    ))
    assert all(rec.bundle != "Bharat Sookshma Udyam Suraksha" for rec in recs)


def test_v2_payload_preserves_legacy_schema_keys():
    legacy = server._legacy_score(_profile())
    v2 = server._v2_score(_profile())
    assert not (set(legacy) - set(v2))
    for key in (
        "revenue_breakdown",
        "risk_multiplier_breakdown",
        "regulatory_triggers_fired",
        "graduation_map",
        "compliance_flags",
        "config_version",
    ):
        assert key in v2


def test_shadow_mode_logs_and_serves_legacy_payload(monkeypatch):
    old_engine = server.SPARC_ENGINE
    log_path = server.PROJECT_ROOT / "sparc_shadow_test.jsonl"
    try:
        if log_path.exists():
            log_path.unlink()
        monkeypatch.setenv("SPARC_SHADOW_LOG_PATH", str(log_path))
        server.SPARC_ENGINE = "shadow"
        payload = server.score(_profile())
        assert "config_version" not in payload
        assert log_path.exists()
    finally:
        server.SPARC_ENGINE = old_engine
        if log_path.exists():
            log_path.unlink()
