"""
Unit tests for bundle_catalog.py v1 patch (research_config.json v2026.05).

Scenarios:
  (i)   Series-A fintech → Startup_Shield_Pack rank 1, Cyber + D&O mandatory
  (ii)  Deeptech drone startup → Drone_RPAS regulatory trigger fired
  (iii) Series-B D2C with manufacturing → Corporate_Cover_II rank 1
  (iv)  Bharat Sookshma rejected when asset_value_inr > 50 000 000
  (v)   API response shape preservation (all original keys present)
"""
import sys
import os
import types
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from bundle_catalog import (
    BUNDLE_CATALOG,
    _load_research_config,
    _asset_type_from_inp,
    _coverage_score,
    _composite_mult,
    _revenue_score,
    bundle_analytics,
    rank_bundles,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _inp(**kwargs):
    """Create a minimal StartupInput-like namespace."""
    defaults = dict(
        hardware_software_split=0.0,
        physical_assets=[],
        state_footprint=[],
        sdf_probability=0.0,
        data_sensitivity="Low",
        rbi_registration=None,
        listed_customer_brsr_dependency=False,
        is_gig_aggregator=False,
        drone_ops=False,
        asset_value_inr=0,
    )
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


def _scores(cyber=60, data=60, liability=50, ip=40, key=40,
            gov=55, prop=45, reg=50, esg=30, geo=30,
            gig=35, pol=45, rep=50):
    return {
        "Cyber Technical Risk":       cyber,
        "Data Privacy Risk":          data,
        "Liability Risk":             liability,
        "IP Infringement Risk":       ip,
        "Key Person Risk":            key,
        "Governance & Fraud Risk":    gov,
        "Property Risk":              prop,
        "Regulatory Compliance Risk": reg,
        "ESG & Climate Risk":         esg,
        "Geopolitical Risk":          geo,
        "Gig & Labour Risk":          gig,
        "Policy Velocity Risk":       pol,
        "Reputation Risk":            rep,
    }


# Fintech-typical scores (high cyber/data/reg/gov)
FINTECH_SCORES = _scores(cyber=82, data=85, liability=55, ip=45, key=50,
                         gov=72, prop=25, reg=78, esg=20, geo=40, gig=30, pol=65, rep=60)

# Deeptech drone scores (high IP/property/key_person)
DEEPTECH_SCORES = _scores(cyber=65, data=55, liability=60, ip=80, key=70,
                          gov=50, prop=75, reg=55, esg=40, geo=35, gig=40, pol=50, rep=45)

# D2C manufacturing scores (high liability/property)
D2C_SCORES = _scores(cyber=45, data=50, liability=80, ip=30, key=45,
                     gov=68, prop=70, reg=50, esg=55, geo=25, gig=60, rep=70, pol=45)

# Seed D2C scores (for Bharat Sookshma eligibility test)
D2C_SEED_SCORES = _scores(cyber=35, data=40, liability=60, ip=20, key=40,
                           gov=45, prop=65, reg=40, esg=35, geo=20, gig=50, rep=45, pol=35)


# ---------------------------------------------------------------------------
# (i) Series-A Fintech → Startup Shield Pack rank 1
# ---------------------------------------------------------------------------
class TestFintechSeriesA(unittest.TestCase):

    def setUp(self):
        self.inp = _inp(data_sensitivity="High", sdf_probability=0.6)
        self.ranked = rank_bundles("Fintech", "Series A", FINTECH_SCORES, self.inp)

    def test_liability_bundle_rank_1(self):
        self.assertTrue(self.ranked, "rank_bundles returned empty list")
        self.assertEqual(
            self.ranked[0]["name"], "I-select Liability Insurance",
            f"Expected I-select Liability Insurance rank 1, got: {self.ranked[0]['name']}",
        )

    def test_cyber_liability_surfaced_in_business_shield(self):
        top = next((b for b in self.ranked if b["name"] == "Business Shield SME"), None)
        self.assertIsNotNone(top, "Business Shield SME must appear for fintech Series A")
        self.assertIn(
            "cyber_liability", top["mandatory_covers"],
            "cyber_liability must be mandatory for Business Shield SME",
        )

    def test_dno_liability_surfaced_in_business_shield(self):
        top = next((b for b in self.ranked if b["name"] == "Business Shield SME"), None)
        self.assertIsNotNone(top, "Business Shield SME must appear for fintech Series A")
        self.assertIn(
            "dno_liability", top["mandatory_covers"],
            "dno_liability must be mandatory for Business Shield SME",
        )

    def test_result_has_score_fields(self):
        top = self.ranked[0]
        for field in ("final_score", "premium_inr", "risk_mult", "revenue_score", "score_rationale"):
            self.assertIn(field, top, f"Missing field: {field}")

    def test_corporate_cover_ii_excluded_for_series_a(self):
        cc2 = next((b for b in self.ranked if b["name"] == "Corporate Cover II"), None)
        self.assertIsNotNone(cc2, "Corporate Cover II must still appear in ranked list")
        self.assertTrue(
            cc2.get("excluded"),
            "Corporate Cover II must be excluded (stage gate) for Series A",
        )


# ---------------------------------------------------------------------------
# (ii) Deeptech drone startup → Drone_RPAS trigger fired
# ---------------------------------------------------------------------------
class TestDeeptechDroneTrigger(unittest.TestCase):

    def setUp(self):
        self.inp = _inp(
            hardware_software_split=0.35,
            physical_assets=["Lab / R&D equipment", "Drones / UAV equipment"],
            drone_ops=True,
        )
        self.ranked = rank_bundles("Deeptech / AI / Robotics", "Series A", DEEPTECH_SCORES, self.inp)
        self.analytics = bundle_analytics(
            "Deeptech / AI / Robotics", "Series A", DEEPTECH_SCORES, self.inp, self.ranked
        )

    def test_drone_rpa_trigger_fired(self):
        fired_signals = [t["signal"] for t in self.analytics["regulatory_triggers_fired"]]
        self.assertIn(
            "drone_ops", fired_signals,
            "drone_ops trigger must fire when inp.drone_ops=True",
        )

    def test_drone_trigger_product_is_drone_rpas(self):
        for t in self.analytics["regulatory_triggers_fired"]:
            if t["signal"] == "drone_ops":
                self.assertEqual(t["product"], "Drone_RPAS")
                self.assertTrue(t["mandatory"])
                break

    def test_deeptech_bundle_eligible(self):
        names = [b["name"] for b in self.ranked]
        self.assertIn(
            "Industrial All Risk (IAR) Policy", names,
            "Industrial All Risk should be eligible for deeptech Series A",
        )

    def test_analytics_keys_present(self):
        for key in ("revenue_breakdown", "risk_multiplier_breakdown", "regulatory_triggers_fired"):
            self.assertIn(key, self.analytics)

    def test_risk_multiplier_breakdown_keys(self):
        bd = self.analytics["risk_multiplier_breakdown"]
        for k in ("claims_freq", "settlement_time", "regulatory_volatility", "market_saturation", "composite"):
            self.assertIn(k, bd)


# ---------------------------------------------------------------------------
# (iii) Series-B D2C with manufacturing → Corporate Cover II rank 1
# ---------------------------------------------------------------------------
class TestD2CSeriesBManufacturing(unittest.TestCase):

    def setUp(self):
        self.inp = _inp(
            hardware_software_split=0.65,
            physical_assets=["Manufacturing plant / factory", "Warehouse / fulfilment centre"],
        )
        self.ranked = rank_bundles("D2C / Consumer Brands", "Series B+", D2C_SCORES, self.inp)

    def test_enterprise_secure_rank_1(self):
        self.assertTrue(self.ranked, "rank_bundles returned empty list")
        self.assertEqual(
            self.ranked[0]["name"], "Enterprise Secure Package Policy",
            f"Expected Enterprise Secure Package Policy rank 1, got: {self.ranked[0]['name']}",
        )

    def test_corporate_cover_ii_has_mandatory_covers(self):
        top = self.ranked[0]
        for cover in ("property_fire", "public_liability", "employees_comp"):
            self.assertIn(cover, top["mandatory_covers"])

    def test_result_shape_preserved(self):
        top = self.ranked[0]
        legacy_fields = (
            "name", "mandatory_covers", "optional_covers", "description",
            "fit_pct", "match_strength", "rank", "fit_delta", "alternative_status",
            "prerequisite_notes", "fire_awareness_note",
        )
        for field in legacy_fields:
            self.assertIn(field, top, f"Legacy field missing: {field}")


# ---------------------------------------------------------------------------
# (iv) Bharat Sookshma rejected when asset_value_inr > 50 000 000
# ---------------------------------------------------------------------------
class TestBharatSookshmaAssetCap(unittest.TestCase):

    def _find_bs(self, ranked):
        return next((b for b in ranked if b["name"] == "Bharat Sookshma Udyam Suraksha"), None)

    def test_bharat_sookshma_excluded_above_cap(self):
        inp = _inp(asset_value_inr=60_000_000)  # 6 Cr — above 5 Cr si_cap
        ranked = rank_bundles("D2C / Consumer Brands", "Seed", D2C_SEED_SCORES, inp)
        bs = self._find_bs(ranked)
        # Bundle is still returned (backward-compat) but must be flagged excluded
        self.assertIsNotNone(bs, "Bharat Sookshma should still appear in ranked list")
        self.assertTrue(
            bs.get("excluded"),
            "Bharat Sookshma must have excluded=True when asset_value_inr > si_cap",
        )

    def test_bharat_sookshma_not_rank_1_above_cap(self):
        inp = _inp(asset_value_inr=60_000_000)
        ranked = rank_bundles("D2C / Consumer Brands", "Seed", D2C_SEED_SCORES, inp)
        self.assertNotEqual(
            ranked[0]["name"], "Bharat Sookshma Udyam Suraksha",
            "Excluded bundle must not rank 1",
        )

    def test_bharat_sookshma_not_excluded_below_cap(self):
        inp = _inp(asset_value_inr=30_000_000)  # 3 Cr — below 5 Cr si_cap
        ranked = rank_bundles("D2C / Consumer Brands", "Seed", D2C_SEED_SCORES, inp)
        bs = self._find_bs(ranked)
        self.assertIsNotNone(bs)
        self.assertFalse(
            bs.get("excluded", False),
            "Bharat Sookshma should NOT be excluded when asset_value_inr ≤ si_cap",
        )

    def test_si_cap_in_config(self):
        cfg = _load_research_config()
        bsus = cfg["bundle_meta"]["Bharat_Sookshma_Udyam"]
        self.assertEqual(bsus["si_cap_inr"], 50_000_000)


# ---------------------------------------------------------------------------
# (v) API response shape preservation
# ---------------------------------------------------------------------------
class TestAPIResponseShape(unittest.TestCase):

    REQUIRED_KEYS = [
        "name", "mandatory_covers", "optional_covers", "description", "criticality",
        "covered_risks", "fit_pct", "match_strength", "nearest_fallback", "rank",
        "fit_delta", "alternative_status", "prerequisite_notes", "fire_awareness_note",
        "final_score", "premium_inr", "risk_mult", "revenue_score", "score_rationale",
        "excluded", "exclusion_reason",
    ]

    def test_all_required_fields_in_top_bundle(self):
        inp = _inp(data_sensitivity="High")
        ranked = rank_bundles("Fintech", "Series A", FINTECH_SCORES, inp)
        self.assertTrue(ranked)
        top = ranked[0]
        for key in self.REQUIRED_KEYS:
            self.assertIn(key, top, f"Required field absent from top bundle: {key}")

    def test_analytics_returns_three_keys(self):
        inp = _inp()
        ranked = rank_bundles("Fintech", "Series A", FINTECH_SCORES, inp)
        analytics = bundle_analytics("Fintech", "Series A", FINTECH_SCORES, inp, ranked)
        self.assertIn("revenue_breakdown", analytics)
        self.assertIn("risk_multiplier_breakdown", analytics)
        self.assertIn("regulatory_triggers_fired", analytics)

    def test_revenue_breakdown_fields(self):
        inp = _inp()
        ranked = rank_bundles("Fintech", "Series A", FINTECH_SCORES, inp)
        analytics = bundle_analytics("Fintech", "Series A", FINTECH_SCORES, inp, ranked)
        for entry in analytics["revenue_breakdown"]:
            for field in ("bundle", "tam_cr", "adoption", "margin", "trajectory", "score", "why"):
                self.assertIn(field, entry, f"revenue_breakdown entry missing: {field}")

    def test_no_original_keys_removed(self):
        """rank_bundles result must still carry all original _bundle_result fields."""
        inp = _inp()
        ranked = rank_bundles("Fintech", "Series A", FINTECH_SCORES, inp)
        for b in ranked:
            for field in ("name", "mandatory_covers", "optional_covers", "fit_pct", "rank"):
                self.assertIn(field, b)

    def test_config_version(self):
        cfg = _load_research_config()
        self.assertEqual(cfg["version"], "2026.05")

    def test_all_13_risk_weights_present(self):
        cfg = _load_research_config()
        expected = {
            "cyber_technical", "data_privacy", "liability", "ip_infringement",
            "key_person", "governance_fraud", "property", "regulatory_compliance",
            "esg_climate", "geopolitical", "gig_labour", "policy_velocity", "reputation",
        }
        self.assertEqual(set(cfg["risk_weights"].keys()), expected)


# ---------------------------------------------------------------------------
# Scoring primitive unit tests
# ---------------------------------------------------------------------------
class TestScoringPrimitives(unittest.TestCase):

    def setUp(self):
        self.cfg = _load_research_config()

    def test_coverage_score_empty_covered_risks(self):
        profile = {"scores": {"cyber_technical": 80}}
        bundle = {"name": "test", "covered_risks": []}
        self.assertEqual(_coverage_score(profile, bundle, self.cfg), 0.0)

    def test_coverage_score_single_risk(self):
        profile = {"scores": {"cyber_technical": 100}}
        bundle = {"name": "test", "covered_risks": ["cyber_technical"]}
        expected = self.cfg["risk_weights"]["cyber_technical"] * 100
        self.assertAlmostEqual(_coverage_score(profile, bundle, self.cfg), expected)

    def test_composite_mult_fintech_increases_cyber(self):
        profile = {"sector": "fintech", "stage": "series_a", "asset": "asset_light", "state": "DEFAULT"}
        mults = _composite_mult(profile, self.cfg)
        self.assertGreater(mults["cyber_technical"], 1.0)
        self.assertGreater(mults["data_privacy"], 1.0)

    def test_composite_mult_default_state_no_change(self):
        profile = {"sector": "", "stage": "", "asset": "", "state": "DEFAULT"}
        mults = _composite_mult(profile, self.cfg)
        # DEFAULT geo_mult = 1.0, no sector/stage/asset match → all 1.0
        for v in mults.values():
            self.assertAlmostEqual(v, 1.0)

    def test_revenue_score_range(self):
        cfg = self.cfg
        for bkey, meta in cfg["bundle_meta"].items():
            score = _revenue_score(meta)
            self.assertGreaterEqual(score, 0, f"{bkey} revenue_score < 0")
            self.assertLessEqual(score, 100, f"{bkey} revenue_score > 100")

    def test_asset_type_fab_or_plant(self):
        inp = _inp(hardware_software_split=0.8)
        self.assertEqual(_asset_type_from_inp(inp), "fab_or_plant")

    def test_asset_type_lab(self):
        inp = _inp(physical_assets=["Lab / R&D equipment"])
        self.assertEqual(_asset_type_from_inp(inp), "lab_equipment")

    def test_asset_type_default(self):
        inp = _inp()
        self.assertEqual(_asset_type_from_inp(inp), "asset_light")


if __name__ == "__main__":
    unittest.main()
