import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from bundle_catalog import BUNDLE_CATALOG, match_bundle, rank_bundles
from global_products import get_top5_global


RISK_SCORES = {
    "Cyber Technical Risk": 82,
    "Data Privacy Risk": 74,
    "Liability Risk": 68,
    "IP Infringement Risk": 52,
    "Key Person Risk": 41,
    "Governance & Fraud Risk": 48,
    "Property Risk": 18,
    "Regulatory Compliance Risk": 66,
    "ESG & Climate Risk": 22,
    "Geopolitical Risk": 35,
    "Gig & Labour Risk": 12,
    "Policy Velocity Risk": 57,
    "Reputation Risk": 44,
}


def test_match_bundle_returns_nearest_for_weak_fit():
    bundle = match_bundle(
        "Unknown Sector",
        "Unknown Stage",
        {key: 0 for key in RISK_SCORES},
        SimpleNamespace(hardware_software_split=0.0),
    )

    assert bundle is not None
    assert bundle["nearest_fallback"] is True
    assert bundle["match_strength"] == "nearest"
    assert bundle["fit_pct"] == 0


def test_match_bundle_marks_existing_strong_fit_as_strong():
    bundle = match_bundle(
        "SaaS / Enterprise Software",
        "Series A",
        RISK_SCORES,
        SimpleNamespace(hardware_software_split=0.0),
    )

    assert bundle is not None
    assert bundle["nearest_fallback"] is False
    assert bundle["match_strength"] == "strong"
    assert bundle["fit_pct"] >= 40


def test_rank_bundles_returns_all_bundle_candidates():
    bundles = rank_bundles(
        "Deeptech / AI / Robotics",
        "Series A",
        RISK_SCORES,
        SimpleNamespace(hardware_software_split=0.8),
    )

    assert len(bundles) == len(BUNDLE_CATALOG)
    assert bundles[0]["alternative_status"] == "top_pick"
    assert [bundle["rank"] for bundle in bundles] == list(range(1, len(bundles) + 1))
    assert all("fit_pct" in bundle for bundle in bundles)


def test_rank_bundles_marks_tied_or_lesser_alternatives():
    bundles = rank_bundles(
        "Agritech",
        "Seed",
        RISK_SCORES,
        SimpleNamespace(hardware_software_split=0.2),
    )
    alternatives = bundles[1:]

    assert alternatives
    assert all(bundle["alternative_status"] in {"tied", "lesser_relevant"} for bundle in alternatives)
    assert any(bundle["alternative_status"] == "tied" for bundle in alternatives)


def test_global_products_edtech_fills_with_non_icici_competitors():
    products = get_top5_global(RISK_SCORES, "Edtech", "micro")

    assert products
    assert all(product["label"] != "icici" for product in products)
    assert any(product["match_basis"] == "nearest_risk" for product in products)


def test_global_products_unknown_sector_returns_nearest_competitors():
    products = get_top5_global(RISK_SCORES, "Unknown Sector", "micro")

    assert len(products) == 5
    assert all(product["label"] != "icici" for product in products)
    assert all(product["match_basis"] == "nearest_risk" for product in products)


def test_global_products_prefers_exact_sector_matches_before_fallbacks():
    products = get_top5_global(RISK_SCORES, "Foodtech / Cloud Kitchen", "micro", top_n=5)

    bases = [product["match_basis"] for product in products]
    if "nearest_risk" in bases:
        first_nearest = bases.index("nearest_risk")
        assert all(basis == "exact_sector" for basis in bases[:first_nearest])
