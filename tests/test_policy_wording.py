import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from policy_wording import canonical_policy_key, compare_policy_wording


def test_canonical_policy_key_matches_bundle_and_product_names():
    assert canonical_policy_key("Business Shield SME") == "business_shield_sme"
    assert canonical_policy_key("Professional Indemnity / E&O Insurance") == "professional_indemnity"
    assert canonical_policy_key("D&O Liability") == "dno_liability"


def test_policy_comparison_flags_reference_exclusions_and_gaps():
    result = compare_policy_wording({
        "product_name": "Business Shield SME",
        "policy_text": (
            "This policy includes Cyber Liability, Directors and Officers liability, "
            "and Professional Indemnity. Prior acts before the retroactive date are not "
            "covered. Bodily injury and physical property damage are excluded under PI. "
            "War and nuclear exclusions apply."
        ),
        "profile": {"sector": "Fintech", "team_size": 50, "has_investors": "Yes"},
        "bundle_match": {"mandatory_covers": ["cyber_liability", "dno_liability", "professional_indemnity"]},
        "recommendations": [{"key": "employment_practices", "name": "Employment Practices Liability"}],
    })
    assert result["ok"] is True
    assert result["matched_reference"] == "Business Shield SME"
    assert result["coverage_gaps"]
    assert any(item["key"] == "employment_practices" for item in result["missing_recommended_covers"])
    assert result["manual_review_required"] is True


def test_policy_comparison_rejects_short_paste():
    result = compare_policy_wording({"policy_text": "too short", "product_name": "Cyber Liability"})
    assert result["ok"] is False
    assert "80 characters" in result["error"]

