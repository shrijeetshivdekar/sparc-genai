import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from startup_shield_web import server


def _bundle_with_companion():
    return {
        "name": "Group Safeguard Insurance Policy",
        "description": "Group protection for employees.",
        "mandatory_covers": ["employee_health", "group_pa"],
        "optional_covers": ["employment_practices"],
        "covers_criticality": {
            "employee_health": {"reason": "Group health helps retain a growing team."},
            "group_pa": {"reason": "Group PA protects employees from accident risk."},
            "employment_practices": {"reason": "EPL helps with hiring and termination disputes."},
        },
        "companion_note": "Also review a sector-specific package.",
        "companion_bundle": {
            "name": "Contractor All Risk (CAR) Insurance Policy",
            "description": "Engineering project protection.",
            "mandatory_covers": ["engineering", "public_liability"],
            "optional_covers": ["surety"],
            "covers_criticality": {
                "engineering": {"reason": "Engineering cover protects project works."},
                "public_liability": {"reason": "Public liability protects against third-party site claims."},
                "surety": {"reason": "Surety supports bid and performance bond needs."},
            },
        },
    }


def test_why_it_matters_fallback_includes_bundle_companion_and_products(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    result = server.generate_why_it_matters(
        {"sector": "Fintech", "funding_stage": "Series A", "team_size": 80},
        _bundle_with_companion(),
        [{"key": "cyber_liability", "name": "Cyber", "nudge": "Cyber protects customer data exposure."}],
    )

    assert result["bundle"] == "Group protection for employees."
    assert result["bundle_covers"]["employee_health"] == "Group health helps retain a growing team."
    assert result["companion_bundle"] == "Engineering project protection."
    assert result["companion_covers"]["engineering"] == "Engineering cover protects project works."
    assert result["products"]["cyber_liability"] == "Cyber protects customer data exposure."
    assert result["cyber_liability"] == "Cyber protects customer data exposure."


def test_why_it_matters_uses_generated_nested_payload(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    def fake_call_gemini_json(prompt):
        assert "Sector: Fintech" in prompt
        assert "Team size: 80" in prompt
        return {
            "bundle": "Generated bundle reason.",
            "bundle_covers": {"employee_health": "Generated group health reason."},
            "companion_bundle": "Generated companion reason.",
            "companion_covers": {"engineering": "Generated engineering reason."},
            "products": {"cyber_liability": "Generated cyber reason."},
        }, None

    monkeypatch.setattr(server, "call_gemini_json", fake_call_gemini_json)
    result = server.generate_why_it_matters(
        {
            "sector": "Fintech",
            "funding_stage": "Series A",
            "team_size": 80,
            "operations": "Digital-only",
            "data_sensitivity": "High",
        },
        _bundle_with_companion(),
        [{"key": "cyber_liability", "name": "Cyber", "nudge": "Fallback cyber reason."}],
    )

    assert result["bundle"] == "Generated bundle reason."
    assert result["bundle_covers"]["employee_health"] == "Generated group health reason."
    assert result["bundle_covers"]["group_pa"] == "Group PA protects employees from accident risk."
    assert result["companion_bundle"] == "Generated companion reason."
    assert result["companion_covers"]["engineering"] == "Generated engineering reason."
    assert result["products"]["cyber_liability"] == "Generated cyber reason."


def test_group_safeguard_companion_uses_highest_fit_candidate():
    primary, alternatives, recommended_set = server.attach_group_safeguard_companion(
        {"name": "Group Safeguard Insurance Policy", "fit_pct": 83},
        [
            {"name": "I-select Liability Insurance", "fit_pct": 77, "final_score": 0.42, "rank": 2},
            {"name": "Industrial All Risk (IAR) Policy", "fit_pct": 71, "final_score": 0.65, "rank": 3},
        ],
    )

    assert primary["companion_bundle"]["name"] == "Industrial All Risk (IAR) Policy"
    assert [item["name"] for item in recommended_set] == [
        "Group Safeguard Insurance Policy",
        "Industrial All Risk (IAR) Policy",
    ]
    assert [item["name"] for item in alternatives] == ["I-select Liability Insurance"]


def test_group_safeguard_legacy_fallback_excludes_group_and_sorts():
    candidates = server.group_safeguard_companion_candidates(
        {"name": "Group Safeguard Insurance Policy"},
        [],
        {
            "bundle_match": {"name": "Group Safeguard Insurance Policy", "fit_pct": 90, "final_score": 0.9},
            "bundle_alternatives": [
                {"name": "I-select Liability Insurance", "fit_pct": 98, "final_score": 0.2},
                {"name": "Business Shield SME", "fit_pct": 88, "final_score": 0.5},
            ],
        },
    )

    assert [item["name"] for item in candidates] == [
        "Business Shield SME",
        "I-select Liability Insurance",
    ]
