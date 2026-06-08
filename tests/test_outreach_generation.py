import json

from startup_shield_web import server


def _profile():
    return {
        "startup_name": "Beco",
        "sector": "D2C / Consumer Brands",
        "funding_stage": "Series A",
        "team_size": 120,
        "operations": "Hybrid",
        "data_sensitivity": "Medium",
    }


def _scores():
    return {
        "Property Risk": 92,
        "Regulatory Compliance Risk": 88,
        "Product Liability Risk": 84,
    }


def _bundle():
    return {
        "name": "MSME Suraksha Kavach",
        "description": "MSME package for asset and operating risks.",
        "mandatory_covers": ["PROPERTY_ALL_RISK", "BUSINESS_INTERRUPTION", "PRODUCT_LIABILITY"],
        "optional_covers": ["EMPLOYERS_COMP"],
    }


def test_fallback_outreach_highlights_fit_and_all_bundle_covers():
    prompts = server.fallback_outreach_prompts(_profile(), _scores(), [], _bundle())

    body = prompts["bundle"]["email_body"]
    assert "WHY THIS FITS:" in body
    assert "WHAT IT COVERS:" in body
    assert "Property all risk" in body
    assert "Business interruption" in body
    assert "Product liability" in body
    assert "Employees compensation" in body


def test_outreach_prompt_passes_compact_deterministic_cover_facts():
    prompt = server.outreach_prompt_payload(_profile(), _scores(), [], _bundle(), "growth")

    payload = json.loads(prompt.split("INPUT_JSON:\n", 1)[1].split("\n\nReturn compact JSON", 1)[0])
    bundle_item = payload["products"][0]
    labels = [item["label"] for item in bundle_item["coverage_facts"]]
    assert bundle_item["key"] == "bundle"
    assert "WHY THIS FITS:" in prompt
    assert labels == [
        "Property all risk",
        "Business interruption",
        "Product liability",
        "Employees compensation",
    ]


def test_outreach_normalization_falls_back_when_ai_omits_cover():
    raw = {
        "bundle": {
            "email_subject": "Test",
            "email_body": (
                "Dear Beco team,\n\nGreetings from ICICI Lombard!\n\n"
                "WHY THIS FITS: relevant.\n\nWHAT IT COVERS:\n- Property all risk only.\n\n"
                "Warm regards,\nRM"
            ),
            "whatsapp": "Short note",
        }
    }

    prompts, source = server.normalize_outreach_response(raw, _profile(), _scores(), [], _bundle())
    assert source == "gemini"
    assert "Business interruption" in prompts["bundle"]["email_body"]
    assert "Product liability" in prompts["bundle"]["email_body"]


def test_bharat_sookshma_component_expands_into_subproduct_explanations():
    bundle = {
        "name": "MSME Suraksha Kavach",
        "description": "MSME package for asset and operating risks.",
        "mandatory_covers": ["BHARAT_SOOKSHMA"],
        "optional_covers": [],
    }

    prompts = server.fallback_outreach_prompts(_profile(), _scores(), [], bundle)
    body = prompts["bundle"]["email_body"]
    why_section = body.split("WHY THIS FITS:", 1)[1].split("WHAT IT COVERS:", 1)[0]

    assert "Bharat Sookshma: This cover is part of the matched package" not in body
    assert "Property fire and allied perils" in why_section
    assert "Stock and inventory protection" in why_section
    assert "Plant, machinery, and equipment" in why_section
    assert "Property fire and allied perils" in body
    assert "Stock and inventory protection" in body
    assert "Plant, machinery, and equipment" in body
    assert "Burglary and theft extension" in body
    assert "Business interruption add-on" in body


def test_bundle_ai_output_falls_back_when_why_section_omits_subproducts():
    raw = {
        "bundle": {
            "email_subject": "Test",
            "email_body": (
                "Dear Beco team,\n\nGreetings from ICICI Lombard!\n\n"
                "WHY THIS FITS: This bundle fits your risks and stage.\n\n"
                "WHAT IT COVERS:\n"
                "- Property all risk: protects assets.\n"
                "- Business interruption: protects downtime.\n"
                "- Product liability: protects product claims.\n"
                "- Employees compensation: protects workforce injury.\n\n"
                "Warm regards,\nRM"
            ),
            "whatsapp": "Short note",
        }
    }

    prompts, source = server.normalize_outreach_response(raw, _profile(), _scores(), [], _bundle())
    why_section = prompts["bundle"]["email_body"].split("WHY THIS FITS:", 1)[1].split("WHAT IT COVERS:", 1)[0]

    assert source == "gemini"
    assert "Property all risk" in why_section
    assert "Business interruption" in why_section
    assert "Product liability" in why_section
