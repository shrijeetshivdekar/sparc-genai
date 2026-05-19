import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pricing_engine import infer_underwriting_inputs, price_output_stage
from quote_prefill import suggest_quote_inputs
from startup_shield_web import server


BASE_SCORES = {
    "Cyber Technical Risk": 82,
    "Data Privacy Risk": 78,
    "Liability Risk": 64,
    "IP Infringement Risk": 58,
    "Key Person Risk": 55,
    "Governance & Fraud Risk": 72,
    "Property Risk": 45,
    "Regulatory Compliance Risk": 75,
    "ESG & Climate Risk": 30,
    "Geopolitical Risk": 45,
    "Gig & Labour Risk": 30,
    "Policy Velocity Risk": 66,
    "Reputation Risk": 61,
}


def test_pricing_engine_prices_bundle_components_with_gst():
    profile = {
        "sector": "Fintech",
        "funding_stage": "Series A",
        "team_size": 60,
        "data_sensitivity": "High",
        "has_investors": "Yes",
        "physical_assets": ["Office / coworking space"],
        "data_handled": ["Payments / financial transactions"],
        "b2b_pct": 0.9,
        "quote_requested": True,
        "cyber_limit_cr": 7.5,
        "dno_limit_cr": 5.0,
        "pi_limit_cr": 5.0,
        "annual_revenue_cr": 15.0,
        "data_records_lakhs": 5.0,
        "claims_last_3_years": False,
    }
    bundle = {
        "name": "Startup Shield Pack",
        "mandatory_covers": ["CYBER", "D_AND_O", "PI_TECH_EO"],
        "optional_covers": [],
    }

    quote = price_output_stage(profile, BASE_SCORES, [], bundle)

    assert quote["gross_premium_lakh"] > quote["net_premium_lakh"] > 0
    assert quote["gst_lakh"] > 0
    assert quote["cover_count"] == 3
    assert {item["cover_key"] for item in quote["covers_priced"]} == {
        "cyber_liability",
        "dno_liability",
        "professional_indemnity",
    }
    assert quote["missing_inputs"] == []


def test_pricing_engine_does_not_quote_without_user_request():
    profile = {
        "sector": "Fintech",
        "funding_stage": "Series A",
        "team_size": 60,
        "data_sensitivity": "High",
        "has_investors": "Yes",
    }
    bundle = {
        "name": "Startup Shield Pack",
        "mandatory_covers": ["CYBER", "D_AND_O", "PI_TECH_EO"],
        "optional_covers": [],
    }

    quote = price_output_stage(profile, BASE_SCORES, [], bundle)

    assert quote["quote_type"] == "input_required"
    assert quote["status"] == "not_requested"
    assert "gross_premium_lakh" not in quote
    assert {row["key"] for row in quote["missing_required_inputs"]} == {
        "cyber_limit_cr",
        "dno_limit_cr",
        "pi_limit_cr",
        "annual_revenue_cr",
        "data_records_lakhs",
        "claims_last_3_years",
    }
    assert all(row.get("suggestion") for row in quote["required_inputs"])


def test_quote_suggestions_are_deterministic_and_profile_grounded():
    suggestions = suggest_quote_inputs({
        "sector": "Fintech",
        "funding_stage": "Series B+",
        "team_size": 185,
        "data_sensitivity": "High",
        "annual_revenue_cr": 95,
        "physical_assets": ["Office / coworking space", "Data centre / server room"],
        "data_handled": ["Payments / financial transactions", "Personal identity data (KYC / Aadhaar)"],
        "has_investors": "Yes",
        "b2b_pct": 0.85,
    })

    assert suggestions["annual_revenue_cr"]["value"] == 95
    assert suggestions["annual_revenue_cr"]["source"] == "profile"
    assert suggestions["payroll_cr"]["value"] > 0
    assert suggestions["data_records_lakhs"]["value"] > 0
    assert suggestions["cyber_limit_cr"]["value"] >= 20
    assert suggestions["dno_limit_cr"]["value"] >= 25
    assert suggestions["pi_limit_cr"]["value"] >= 15
    assert suggestions["product_liability_limit_cr"]["value"] >= 1


def test_profile_values_are_suggestions_not_submitted_quote_inputs_when_not_requested():
    profile = {
        "sector": "Fintech",
        "funding_stage": "Series A",
        "team_size": 60,
        "data_sensitivity": "High",
        "annual_revenue_cr": 15.0,
        "cyber_limit_cr": 7.5,
        "dno_limit_cr": 5.0,
        "pi_limit_cr": 5.0,
        "claims_last_3_years": False,
    }
    bundle = {
        "name": "Startup Shield Pack",
        "mandatory_covers": ["CYBER", "D_AND_O", "PI_TECH_EO"],
        "optional_covers": [],
    }

    quote = price_output_stage(profile, BASE_SCORES, [], bundle)

    assert quote["quote_type"] == "input_required"
    assert quote["status"] == "not_requested"
    assert {row["key"] for row in quote["missing_required_inputs"]} == {
        "cyber_limit_cr",
        "dno_limit_cr",
        "pi_limit_cr",
        "annual_revenue_cr",
        "data_records_lakhs",
        "claims_last_3_years",
    }
    cyber = next(row for row in quote["required_inputs"] if row["key"] == "cyber_limit_cr")
    assert cyber["provided"] is False
    assert cyber["suggestion"]["value"] == 7.5


def test_quote_user_inputs_are_required_before_quote_even_with_profile_numbers():
    profile = {
        "sector": "Fintech",
        "funding_stage": "Series A",
        "team_size": 60,
        "data_sensitivity": "High",
        "annual_revenue_cr": 15.0,
        "cyber_limit_cr": 7.5,
        "dno_limit_cr": 5.0,
        "pi_limit_cr": 5.0,
        "claims_last_3_years": False,
        "quote_requested": True,
        "quote_user_inputs": {},
    }
    bundle = {
        "name": "Startup Shield Pack",
        "mandatory_covers": ["CYBER", "D_AND_O", "PI_TECH_EO"],
        "optional_covers": [],
    }

    quote = price_output_stage(profile, BASE_SCORES, [], bundle)

    assert quote["quote_type"] == "input_required"
    assert quote["status"] == "awaiting_inputs"
    assert "gross_premium_inr" not in quote


def test_quote_user_inputs_generate_quote_after_user_confirms_suggestions():
    profile = {
        "sector": "Fintech",
        "funding_stage": "Series A",
        "team_size": 60,
        "data_sensitivity": "High",
        "annual_revenue_cr": 15.0,
        "quote_requested": True,
        "quote_user_inputs": {
            "cyber_limit_cr": 7.5,
            "dno_limit_cr": 5.0,
            "pi_limit_cr": 5.0,
            "annual_revenue_cr": 15.0,
            "data_records_lakhs": 5.0,
            "claims_last_3_years": False,
        },
    }
    bundle = {
        "name": "Startup Shield Pack",
        "mandatory_covers": ["CYBER", "D_AND_O", "PI_TECH_EO"],
        "optional_covers": [],
    }

    quote = price_output_stage(profile, BASE_SCORES, [], bundle)

    assert quote["quote_type"] == "indicative_underwriting_quote"
    assert quote["gross_premium_inr"] > 0
    assert quote["underwriting_inputs"]["cyber_limit_cr"] == 7.5


def test_enterprise_fintech_suggestions_are_capped_and_flagged():
    profile = {
        "sector": "Fintech",
        "funding_stage": "Series B+",
        "team_size": 2500,
        "data_sensitivity": "High",
        "annual_revenue_cr": 2500,
        "data_handled": ["Payments / financial transactions", "Personal identity data (KYC / Aadhaar)"],
        "regulatory": ["RBI / SEBI / IRDAI licensed", "DPDP Act obligations"],
        "has_investors": "Yes",
        "quote_requested": True,
    }
    suggestions = suggest_quote_inputs(profile)
    profile["quote_user_inputs"] = {
        key: item["value"]
        for key, item in suggestions.items()
        if key in {
            "cyber_limit_cr", "dno_limit_cr", "pi_limit_cr", "annual_revenue_cr",
            "data_records_lakhs", "crime_limit_cr", "employment_practices_limit_cr",
            "claims_last_3_years",
        }
    }
    bundle = {
        "name": "I-select Liability Insurance",
        "mandatory_covers": ["PI_TECH_EO", "D_AND_O", "CYBER", "CRIME_FIDELITY", "EMPLOYMENT_PRACTICES"],
        "optional_covers": [],
    }

    quote = price_output_stage(profile, BASE_SCORES, [], bundle)
    inputs = quote["underwriting_inputs"]

    assert inputs["cyber_limit_cr"] == 50.0
    assert inputs["dno_limit_cr"] == 30.0
    assert inputs["pi_limit_cr"] == 25.0
    assert inputs["employment_practices_limit_cr"] == 10.0
    assert quote["pricing_scale"]["segment"] == "enterprise"
    assert quote["pricing_scale"]["benchmark_range_applicable"] is False
    cyber = next(item for item in quote["covers_priced"] if item["cover_key"] == "cyber_liability")
    assert 15 <= cyber["premium_lakh"] <= 40
    assert 0.003 <= cyber["effective_rol"] <= 0.008
    assert cyber["enterprise_rol_cap_applied"] is True
    assert quote["gross_premium_lakh"] < 300


def test_enterprise_cyber_uses_market_rol_not_multiplicative_loading():
    profile = {
        "sector": "Edtech",
        "funding_stage": "Series B+",
        "team_size": 900,
        "data_sensitivity": "High",
        "annual_revenue_cr": 650,
        "data_records_lakhs": 150,
        "quote_requested": True,
        "quote_user_inputs": {
            "cyber_limit_cr": 50,
            "annual_revenue_cr": 650,
            "data_records_lakhs": 150,
            "claims_last_3_years": False,
        },
    }
    scores = {
        **BASE_SCORES,
        "Cyber Technical Risk": 100,
        "Data Privacy Risk": 100,
        "Regulatory Compliance Risk": 100,
    }
    bundle = {
        "name": "Cyber only",
        "mandatory_covers": ["CYBER"],
        "optional_covers": [],
    }

    quote = price_output_stage(profile, scores, [], bundle)
    cyber = quote["covers_priced"][0]

    assert cyber["cover_key"] == "cyber_liability"
    assert 15 <= cyber["premium_lakh"] <= 40
    assert cyber["effective_rol"] <= 0.008
    assert cyber["enterprise_rol_cap_applied"] is True
    assert quote["bundle_discount_lakh"] == 0


def test_enterprise_liability_lines_use_regressive_rol_bands():
    profile = {
        "sector": "SaaS / Enterprise Software",
        "funding_stage": "Series B+",
        "team_size": 900,
        "annual_revenue_cr": 600,
        "quote_requested": True,
        "quote_user_inputs": {
            "dno_limit_cr": 30,
            "pi_limit_cr": 25,
            "public_liability_limit_cr": 25,
            "crime_limit_cr": 30,
            "employment_practices_limit_cr": 30,
            "annual_revenue_cr": 600,
            "claims_last_3_years": False,
        },
    }
    scores = {
        **BASE_SCORES,
        "Governance & Fraud Risk": 100,
        "Regulatory Compliance Risk": 100,
        "Reputation Risk": 100,
        "Liability Risk": 100,
        "IP Infringement Risk": 100,
        "Gig & Labour Risk": 100,
    }
    bundle = {
        "name": "Enterprise liability pack",
        "mandatory_covers": ["D_AND_O", "PI_TECH_EO", "CGL_I_ELITE", "CRIME_FIDELITY", "EMPLOYMENT_PRACTICES"],
        "optional_covers": [],
    }

    quote = price_output_stage(profile, scores, [], bundle)
    covers = {item["cover_key"]: item for item in quote["covers_priced"]}

    assert 0.001 <= covers["dno_liability"]["effective_rol"] <= 0.0025
    assert 0.001 <= covers["professional_indemnity"]["effective_rol"] <= 0.002
    assert 0.0005 <= covers["comprehensive_general_liability"]["effective_rol"] <= 0.001
    assert 0.0005 <= covers["crime_fidelity"]["effective_rol"] <= 0.0015
    assert 0.0005 <= covers["employment_practices"]["effective_rol"] <= 0.0015
    assert all(covers[key]["enterprise_rol_cap_applied"] for key in covers)
    assert quote["bundle_discount_rate"] == 0.10


def test_group_health_uses_group_size_burning_cost_matrix():
    profile = {
        "sector": "Edtech",
        "funding_stage": "Series B+",
        "team_size": 900,
        "quote_requested": True,
        "quote_user_inputs": {"employee_count": 900},
    }
    scores = {**BASE_SCORES, "Key Person Risk": 100, "Gig & Labour Risk": 100}
    bundle = {
        "name": "Group health",
        "mandatory_covers": ["GROUP_HEALTH"],
        "optional_covers": [],
    }

    quote = price_output_stage(profile, scores, [], bundle)
    health = quote["covers_priced"][0]

    assert health["cover_key"] == "employee_health"
    assert 108 <= health["premium_lakh"] <= 162
    assert 0.12 <= health["per_head_lakh"] <= 0.18
    assert health["quote_confidence_band"] == "directional_only"
    assert quote["precision_mode"] == "range"


def test_explicit_asset_value_drives_property_sum_insured():
    low = infer_underwriting_inputs({
        "sector": "D2C / Consumer Brands",
        "funding_stage": "Seed",
        "team_size": 10,
        "physical_assets": ["Warehouse / fulfilment centre"],
        "asset_value_inr": 10_000_000,
    })
    high = infer_underwriting_inputs({
        "sector": "D2C / Consumer Brands",
        "funding_stage": "Seed",
        "team_size": 10,
        "physical_assets": ["Warehouse / fulfilment centre"],
        "asset_value_inr": 50_000_000,
    })

    assert low["property_sum_insured_cr"] == 1.0
    assert high["property_sum_insured_cr"] == 5.0


def test_analyze_response_asks_for_pricing_inputs_by_default():
    payload = server._v2_score({
        "startup_name": "Pricing Test",
        "sector": "Fintech",
        "funding_stage": "Series A",
        "team_size": 55,
        "operations": "Digital-only",
        "data_sensitivity": "High",
        "data_handled": ["Payments / financial transactions", "Personal identity data (KYC / Aadhaar)"],
        "regulatory": ["RBI / SEBI / IRDAI licensed", "DPDP Act obligations"],
        "physical_assets": ["Office / coworking space"],
        "has_investors": "Yes",
    })

    quote = payload["pricing_engine_quote"]
    assert quote["quote_type"] == "input_required"
    assert quote["status"] == "not_requested"
    assert "gross_premium_inr" not in quote
    assert quote["required_inputs"]


def test_analyze_response_quotes_after_user_supplies_inputs():
    payload = server._v2_score({
        "startup_name": "Pricing Test",
        "sector": "Fintech",
        "funding_stage": "Series A",
        "team_size": 55,
        "operations": "Digital-only",
        "data_sensitivity": "High",
        "data_handled": ["Payments / financial transactions", "Personal identity data (KYC / Aadhaar)"],
        "regulatory": ["RBI / SEBI / IRDAI licensed", "DPDP Act obligations"],
        "physical_assets": ["Office / coworking space"],
        "has_investors": "Yes",
        "quote_requested": True,
        "cyber_limit_cr": 7.5,
        "dno_limit_cr": 5.0,
        "pi_limit_cr": 5.0,
        "crime_limit_cr": 1.0,
        "receivables_on_credit_cr": 2.0,
        "public_liability_limit_cr": 2.0,
        "annual_revenue_cr": 20.0,
        "data_records_lakhs": 8.0,
        "claims_last_3_years": False,
    })

    quote = payload["pricing_engine_quote"]
    assert quote["quote_type"] == "indicative_underwriting_quote"
    assert quote["gross_premium_inr"] > 0
    assert quote["covers_priced"]


def test_v1_prefill_claims_unknown_and_ladder_metadata():
    suggestions = suggest_quote_inputs({
        "sector": "Fintech",
        "funding_stage": "Series A",
        "team_size": 80,
        "annual_revenue_cr": 20,
        "data_sensitivity": "High",
        "has_investors": "Yes",
        "data_handled": ["Payments / financial transactions"],
    })

    assert suggestions["claims_last_3_years"]["value"] == "unknown"
    assert suggestions["claims_last_3_years"]["source"] == "not_assumed"
    assert suggestions["cyber_limit_cr"]["value"] in {1, 2, 5, 10, 25, 50}
    assert suggestions["dno_limit_cr"]["value"] in {1, 2, 5, 10, 20, 25, 30}
    assert suggestions["pi_limit_cr"]["value"] in {1, 2, 5, 10, 15, 25}
    assert suggestions["cyber_limit_cr"]["suggested_input"] == suggestions["cyber_limit_cr"]["value"]
    assert suggestions["cyber_limit_cr"]["pricing_submitted_input"] is None
    assert suggestions["cyber_limit_cr"]["confidence_of_suggestion"] == suggestions["cyber_limit_cr"]["confidence"]


def test_v1_cargo_prefill_is_conservative_for_non_transit_profile():
    suggestions = suggest_quote_inputs({
        "sector": "SaaS / Enterprise Software",
        "funding_stage": "Series B+",
        "team_size": 150,
        "annual_revenue_cr": 100,
        "physical_assets": ["Office / coworking space"],
        "data_handled": ["User analytics"],
    })

    assert suggestions["cargo_turnover_cr"]["value"] == 5.0
    assert suggestions["cargo_turnover_cr"]["confidence"] == "low"


def test_v1_specialty_flags_from_profile_signals():
    suggestions = suggest_quote_inputs({
        "sector": "Deeptech / AI / Robotics",
        "sub_sector": "Spacetech",
        "team_size": 220,
        "hardware_software_split": 0.75,
        "physical_assets": ["Lab / R&D equipment", "Medical devices / diagnostic equipment"],
        "product_description": "Satellite medical device platform",
        "export_us_pct": 0.15,
    })

    assert suggestions["specialty_deeptech_hardware"]["value"] is True
    assert suggestions["specialty_spacetech"]["value"] is True
    assert suggestions["specialty_med_device"]["value"] is True
    assert suggestions["specialty_export_product"]["value"] is True


def test_v1_cyber_benchmark_hidden_above_startup_box_without_global_enterprise():
    profile = {
        "sector": "SaaS / Enterprise Software",
        "funding_stage": "Series A",
        "team_size": 120,
        "quote_requested": True,
        "quote_user_inputs": {
            "cyber_limit_cr": 12,
            "annual_revenue_cr": 40,
            "data_records_lakhs": 20,
            "claims_last_3_years": False,
        },
    }
    bundle = {"name": "Cyber only", "mandatory_covers": ["CYBER"], "optional_covers": []}

    quote = price_output_stage(profile, BASE_SCORES, [], bundle)
    cyber = quote["covers_priced"][0]

    assert quote["pricing_scale"]["segment"] == "specialty_or_enterprise"
    assert quote["benchmark_comparison"]["status"] == "not_comparable"
    assert cyber["benchmark_comparison"]["status"] == "not_comparable"
    assert cyber["quote_confidence_band"] == "technically_priced"
    assert quote["precision_mode"] == "point_estimate"


def test_v1_cyber_above_precise_box_becomes_directional():
    profile = {
        "sector": "SaaS / Enterprise Software",
        "funding_stage": "Series B+",
        "team_size": 300,
        "quote_requested": True,
        "quote_user_inputs": {
            "cyber_limit_cr": 30,
            "annual_revenue_cr": 120,
            "data_records_lakhs": 40,
            "claims_last_3_years": False,
        },
    }
    bundle = {"name": "Cyber only", "mandatory_covers": ["CYBER"], "optional_covers": []}

    quote = price_output_stage(profile, BASE_SCORES, [], bundle)
    cyber = quote["covers_priced"][0]

    assert cyber["quote_confidence_band"] == "directional_only"
    assert cyber["precision_mode"] == "range"
    assert quote["precision_mode"] == "range"
    assert quote["display_premium_range_lakh"]


def test_v1_property_above_bharat_laghu_box_suppresses_benchmark():
    profile = {
        "sector": "D2C / Consumer Brands",
        "funding_stage": "Series A",
        "team_size": 200,
        "quote_requested": True,
        "quote_user_inputs": {"property_sum_insured_cr": 60},
    }
    bundle = {"name": "Property only", "mandatory_covers": ["BHARAT_SOOKSHMA"], "optional_covers": []}

    quote = price_output_stage(profile, BASE_SCORES, [], bundle)
    prop = quote["covers_priced"][0]

    assert prop["cover_key"] == "property_fire"
    assert prop["benchmark_comparison"]["status"] == "not_comparable"
    assert quote["benchmark_comparison"]["status"] == "not_comparable"
    assert prop["precision_mode"] == "range"


def test_v1_unknown_claims_lowers_confidence_without_claims_loading():
    common = {
        "sector": "Fintech",
        "funding_stage": "Series A",
        "team_size": 80,
        "quote_requested": True,
    }
    bundle = {"name": "Cyber only", "mandatory_covers": ["CYBER"], "optional_covers": []}
    clean = price_output_stage({
        **common,
        "quote_user_inputs": {
            "cyber_limit_cr": 7.5,
            "annual_revenue_cr": 20,
            "data_records_lakhs": 8,
            "claims_last_3_years": False,
        },
    }, BASE_SCORES, [], bundle)
    unknown = price_output_stage({
        **common,
        "quote_user_inputs": {
            "cyber_limit_cr": 7.5,
            "annual_revenue_cr": 20,
            "data_records_lakhs": 8,
            "claims_last_3_years": "unknown",
        },
    }, BASE_SCORES, [], bundle)

    assert unknown["covers_priced"][0]["premium_lakh"] == clean["covers_priced"][0]["premium_lakh"]
    assert unknown["quote_confidence"]["score"] < clean["quote_confidence"]["score"]
    assert "claims_history_unknown" in unknown["quote_confidence"]["reason_codes"]


def test_v1_marine_without_max_send_is_directional():
    profile = {
        "sector": "D2C / Consumer Brands",
        "funding_stage": "Series A",
        "team_size": 150,
        "quote_requested": True,
        "quote_user_inputs": {"cargo_annual_turnover_cr": 8},
    }
    bundle = {"name": "Marine only", "mandatory_covers": ["MARINE_CARGO"], "optional_covers": []}

    quote = price_output_stage(profile, BASE_SCORES, [], bundle)
    marine = quote["covers_priced"][0]

    assert marine["pricing_basis"] == "annual_transit_turnover"
    assert marine["quote_confidence_band"] == "directional_only"
    assert "marine_turnover_or_max_send_unconfirmed" in marine["quote_confidence"]["reason_codes"]


def test_v1_bundle_discount_and_gst_remain_consistent():
    profile = {
        "sector": "Fintech",
        "funding_stage": "Series A",
        "team_size": 90,
        "quote_requested": True,
        "quote_user_inputs": {
            "cyber_limit_cr": 7.5,
            "dno_limit_cr": 5,
            "pi_limit_cr": 5,
            "crime_limit_cr": 2,
            "employment_practices_limit_cr": 2,
            "annual_revenue_cr": 25,
            "data_records_lakhs": 10,
            "claims_last_3_years": False,
        },
    }
    bundle = {
        "name": "Liability bundle",
        "mandatory_covers": ["CYBER", "D_AND_O", "PI_TECH_EO", "CRIME_FIDELITY", "EMPLOYMENT_PRACTICES"],
        "optional_covers": [],
    }

    quote = price_output_stage(profile, BASE_SCORES, [], bundle)
    subtotal = round(sum(item["premium_lakh"] for item in quote["covers_priced"]), 2)

    assert quote["subtotal_premium_lakh"] == subtotal
    assert quote["bundle_discount_lakh"] == round(subtotal * quote["bundle_discount_rate"], 2)
    assert quote["net_premium_lakh"] == round(subtotal - quote["bundle_discount_lakh"], 2)
    assert quote["gst_lakh"] == round(quote["net_premium_lakh"] * quote["gst_rate"], 2)
    assert quote["gross_premium_lakh"] == round(quote["net_premium_lakh"] + quote["gst_lakh"], 2)


def test_v1_deeptech_hardware_degrades_specialty_cover_confidence():
    profile = {
        "sector": "Deeptech / AI / Robotics",
        "funding_stage": "Series A",
        "team_size": 80,
        "hardware_software_split": 0.8,
        "physical_assets": ["Lab / R&D equipment"],
        "quote_requested": True,
        "quote_user_inputs": {"product_liability_limit_cr": 5},
    }
    bundle = {"name": "Product liability", "mandatory_covers": ["PRODUCT_LIABILITY"], "optional_covers": []}

    quote = price_output_stage(profile, BASE_SCORES, [], bundle)
    product = quote["covers_priced"][0]

    assert product["quote_confidence_band"] == "directional_only"
    assert "specialty_deeptech_hardware" in product["quote_confidence"]["reason_codes"]
