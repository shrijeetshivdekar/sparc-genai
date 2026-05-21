import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from company_profiles import company_profile_count, get_company_profile, search_company_profiles


def test_seed_database_contains_100_company_profiles():
    assert company_profile_count() >= 230


def test_company_profile_search_and_exact_lookup():
    matches = search_company_profiles("razor")
    assert matches
    assert matches[0]["name"] == "Razorpay"

    profile = get_company_profile("Razorpay")
    assert profile["startup_name"] == "Razorpay"
    assert profile["sector"] == "Fintech"
    assert profile["funding_stage"] == "Series B+"
    assert "profile_source" in profile


def test_company_profile_search_can_return_full_dropdown_and_prefix_matches():
    all_rows = search_company_profiles("", limit=company_profile_count())
    assert len(all_rows) == company_profile_count()
    assert all_rows == sorted(all_rows, key=lambda item: item["name"].lower())

    matches = search_company_profiles("A", limit=100)
    assert matches
    assert all(item["name"].lower().startswith("a") for item in matches)
    assert {"name", "sector", "funding_stage", "team_size", "operations"} <= set(matches[0])


def test_company_profile_database_has_seed_and_pre_seed_demos():
    all_rows = search_company_profiles("", limit=company_profile_count())
    stages = {row["funding_stage"] for row in all_rows}

    assert {"Seed", "Pre-seed"} <= stages
    assert get_company_profile("Hyperface")["funding_stage"] == "Seed"
    assert get_company_profile("Arva Health")["funding_stage"] == "Pre-seed"


def test_company_profile_database_includes_real_startup_style_profiles():
    assert get_company_profile("Niro")["funding_stage"] == "Series A"
    assert get_company_profile("Zyla Health")["funding_stage"] == "Series A"
    assert get_company_profile("GalaxEye")["sector"] == "Spacetech"
    assert get_company_profile("Pulse Energy")["funding_stage"] == "Seed"


def test_unknown_company_returns_none():
    assert get_company_profile("Not A Real Seed") is None
