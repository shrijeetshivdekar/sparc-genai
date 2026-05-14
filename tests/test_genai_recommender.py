import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from genai_recommender import parse_genai_response, rerank_payload
from startup_shield_web import server


def _payload():
    return {
        "profile": {
            "startup_name": "GenAI Test",
            "sector": "Fintech",
            "funding_stage": "Series A",
            "team_size": 55,
            "data_handled": ["Payments / financial transactions"],
            "regulatory": ["RBI / SEBI / IRDAI licensed"],
        },
        "scores": {
            "Cyber Technical Risk": 88,
            "Data Privacy Risk": 82,
            "Regulatory Compliance Risk": 86,
            "Governance & Fraud Risk": 74,
        },
        "recommendations": [
            {"key": "cyber_liability", "name": "Cyber Liability", "score": 91.0},
            {"key": "dno_liability", "name": "D&O Liability", "score": 84.0},
            {"key": "employee_health", "name": "Employee Health", "score": 40.0, "mandatory": True},
        ],
        "bundle_match": {
            "name": "Startup Shield Pack",
            "fit_pct": 88,
            "mandatory_covers": ["CYBER", "D_AND_O"],
        },
        "bundle_alternatives": [
            {"name": "I-select Liability Insurance", "fit_pct": 77, "mandatory_covers": ["CYBER", "PI_TECH_EO"]},
        ],
        "recommended_bundle_set": [],
        "global_products": [],
        "size_bucket": "small",
    }


def test_structured_genai_parsing_accepts_only_shortlisted_items():
    products = [
        {"key": "cyber_liability", "name": "Cyber Liability"},
        {"key": "dno_liability", "name": "D&O Liability"},
    ]
    bundles = [{"name": "Startup Shield Pack"}]
    recs, bundle, audit = parse_genai_response(
        {
            "recommendations": [
                {
                    "product_key": "dno_liability",
                    "confidence": 0.81,
                    "rationale": "Investor governance exposure is high.",
                    "why_it_fits": "Series A fintech with RBI exposure.",
                    "missing_information": ["board composition"],
                }
            ],
            "bundle_match": {"name": "Startup Shield Pack", "confidence": "high"},
            "audit": {"guardrails_followed": True, "notes": ["shortlist only"]},
        },
        products,
        bundles,
    )

    assert recs[0]["product_key"] == "dno_liability"
    assert recs[0]["confidence"] == 0.81
    assert bundle["name"] == "Startup Shield Pack"
    assert bundle["confidence"] == 0.85
    assert audit["shortlisted_product_count"] == 2


def test_primary_mode_falls_back_when_model_unavailable():
    deterministic = _payload()
    result = rerank_payload(
        deterministic,
        mode="primary",
        model_available=False,
        call_json=lambda prompt: ({}, None),
    )

    assert result.source == "fallback"
    assert result.payload["recommendations"] == deterministic["recommendations"]
    assert result.payload["bundle_match"] == deterministic["bundle_match"]
    assert result.payload["genai_error"]


def test_hard_gate_enforcement_rejects_ineligible_model_output():
    deterministic = _payload()
    result = rerank_payload(
        deterministic,
        mode="primary",
        model_available=True,
        call_json=lambda prompt: (
            {
                "recommendations": [{"product_key": "invented_cover", "confidence": 0.9}],
                "bundle_match": {"name": "Startup Shield Pack"},
            },
            None,
        ),
    )

    assert result.source == "fallback"
    assert "ineligible product" in result.error
    assert result.payload["recommendations"] == deterministic["recommendations"]


def test_primary_mode_applies_genai_order_but_preserves_mandatory_fallbacks():
    deterministic = _payload()
    result = rerank_payload(
        deterministic,
        mode="primary",
        model_available=True,
        call_json=lambda prompt: (
            {
                "recommendations": [
                    {"product_key": "dno_liability", "confidence": 0.82},
                    {"product_key": "cyber_liability", "confidence": 0.79},
                ],
                "bundle_match": {"name": "I-select Liability Insurance", "confidence": 0.7},
                "audit": {"guardrails_followed": True},
            },
            None,
        ),
    )

    assert result.source == "gemini"
    assert [item["key"] for item in result.payload["recommendations"]] == [
        "dno_liability",
        "cyber_liability",
        "employee_health",
    ]
    assert result.payload["bundle_match"]["name"] == "I-select Liability Insurance"
    assert result.payload["genai_shadow_diff"]["changed"] is True


def test_shadow_mode_logs_diff_and_serves_deterministic_payload(monkeypatch, tmp_path):
    log_path = tmp_path / "genai_shadow.jsonl"
    monkeypatch.setenv("SPARC_GENAI_MODE", "shadow")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("SPARC_SHADOW_LOG_PATH", str(log_path))

    def fake_call(prompt):
        if "allowed_product_keys" not in prompt or "shortlisted_products" not in prompt:
            return {}, None
        payload = json.loads(prompt.split("INPUT DATA:\n", 1)[1].split("\n\nRespond with ONLY", 1)[0])
        keys = payload["allowed_product_keys"]
        bundles = payload["allowed_bundle_names"]
        return {
            "recommendations": [{"product_key": key, "confidence": 0.7} for key in reversed(keys[:2])],
            "bundle_match": {"name": bundles[0], "confidence": 0.7},
            "audit": {"guardrails_followed": True},
        }, None

    monkeypatch.setattr(server, "call_gemini_json", fake_call)
    payload = server.score({
        "startup_name": "Shadow Fintech",
        "sector": "Fintech",
        "sub_sector": "Fintech.NBFC_Digital_Lending",
        "funding_stage": "Series A",
        "team_size": 55,
        "operations": "Digital-only",
        "data_sensitivity": "High",
        "data_handled": ["Payments / financial transactions", "Personal identity data (KYC / Aadhaar)"],
        "regulatory": ["RBI / SEBI / IRDAI licensed", "DPDP Act obligations"],
        "physical_assets": ["Office / coworking space"],
    })

    assert payload["recommendation_mode"] == "shadow"
    assert payload["genai_source"] == "gemini"
    assert payload["genai_shadow_diff"]["product_order_changed"] is True
    assert [item["key"] for item in payload["recommendations"][:2]] != [
        item["product_key"] for item in payload["genai_recommendations"][:2]
    ]
    assert log_path.exists()
    assert "genai_shadow_diff" in payload
