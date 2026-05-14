import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from company_profiles import company_profile_count, get_company_profile, search_company_profiles


def test_seed_database_contains_100_company_profiles():
    assert company_profile_count() == 100


def test_company_profile_search_and_exact_lookup():
    matches = search_company_profiles("razor")
    assert matches
    assert matches[0]["name"] == "Razorpay"

    profile = get_company_profile("Razorpay")
    assert profile["startup_name"] == "Razorpay"
    assert profile["sector"] == "Fintech"
    assert profile["funding_stage"] == "Series B+"
    assert "profile_source" in profile


def test_unknown_company_returns_none():
    assert get_company_profile("Not A Real Seed") is None

