from bundle_pricing_agent import price_bundle


def test_bundle_pricing_agent_returns_enriched_indicative_quote():
    profile = {
        "startup_name": "LogiTrack India",
        "sector": "Logistics / Mobility",
        "funding_stage": "Series A",
        "team_size": 80,
        "employee_count": 72,
        "operations": "Physical + Digital",
        "physical_assets": ["Warehouse / fulfilment centre", "Vehicles / delivery fleet"],
        "data_handled": ["Physical inventory / goods", "Personal identity data (KYC / Aadhaar)"],
        "data_sensitivity": "Medium",
        "annual_revenue_cr": 18.0,
        "b2b_pct": 0.75,
        "has_investors": "Yes",
        "facility_climate_risk_zone": "High",
        "claims_last_3_years": "Yes",
        "data_records_lakhs": 12.0,
        "quote_requested": True,
        "cyber_limit_cr": 3.0,
        "dno_limit_cr": 3.0,
        "pi_limit_cr": 2.0,
        "public_liability_limit_cr": 5.0,
        "property_sum_insured_cr": 12.0,
        "payroll_cr": 4.2,
        "cargo_annual_turnover_cr": 8.5,
    }
    scores = {
        "Cyber Technical Risk": 58,
        "Data Privacy Risk": 55,
        "Liability Risk": 72,
        "Property Risk": 78,
        "Gig & Labour Risk": 68,
        "ESG & Climate Risk": 74,
        "Geopolitical Risk": 52,
        "Governance & Fraud Risk": 65,
        "Regulatory Compliance Risk": 70,
        "Reputation Risk": 60,
        "Key Person Risk": 45,
        "IP Infringement Risk": 30,
    }
    bundle = {
        "name": "Logistics & Mobility Shield",
        "mandatory_covers": [
            "CYBER",
            "PUBLIC_LIABILITY",
            "EMPLOYERS_COMP",
            "GROUP_HEALTH",
            "PROPERTY_FIRE",
        ],
        "optional_covers": [
            "D_AND_O",
            "MARINE_CARGO",
            "BHARAT_SOOKSHMA",
            "GROUP_PA",
            "ELECTRONIC_EQUIPMENT",
            "CRIME_FIDELITY",
            "TRADE_CREDIT",
            "BURGLARY",
            "PROPERTY_ALL_RISK",
            "SURETY",
        ],
    }

    result = price_bundle(profile, scores, bundle)
    quote = result["bundle_quote"]
    analysis = result["bundle_analysis"]

    assert quote["quote_type"] == "indicative_underwriting_quote"
    assert analysis is not None
    assert analysis["value_metrics"]["cover_count"] <= 8
    assert quote["underwriting_inputs"]["employee_count"] == 72
    assert all("market_benchmark" in cover for cover in quote["covers_priced"])
    assert analysis["slim_mandatory_tier"]["available"] is True
