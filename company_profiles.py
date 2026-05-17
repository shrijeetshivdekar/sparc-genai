"""Seed company profiles for one-click SPARC analysis.

These are starter profiles, not verified underwriting submissions. The names
are real companies, while numeric fields are conservative analysis assumptions
used to prefill the SPARC intake. Users should replace assumptions with actual
company-provided data before relying on a quote or underwriting decision.
"""

from __future__ import annotations

from copy import deepcopy


ARCHETYPES = {
    "fintech_payments": {
        "sector": "Fintech",
        "sub_sector": "Fintech.PA_PG",
        "operations": "Hybrid",
        "data_sensitivity": "High",
        "customer_type": ["B2B Enterprise", "SMB / MSME", "D2C / Marketplace"],
        "data_handled": [
            "Payments / financial transactions",
            "Personal identity data (KYC / Aadhaar)",
            "Customer behavioural / usage data",
            "Sensitive personal data (DPDP Act)",
            "Intellectual property / source code",
        ],
        "regulatory": ["RBI / SEBI / IRDAI licensed", "DPDP Act obligations", "IT Act / CERT-In obligations"],
        "physical_assets": ["Office / coworking space", "Data centre / server room"],
        "rbi_registration": True,
        "payment_or_card_program": True,
        "cert_in_poc_designated": True,
        "sdf_probability": 0.85,
        "b2b_pct": 0.9,
        "facility_climate_risk_zone": "Low",
    },
    "fintech_lending": {
        "sector": "Fintech",
        "sub_sector": "Fintech.NBFC_Digital_Lending",
        "operations": "Digital-only",
        "data_sensitivity": "High",
        "customer_type": ["B2C Consumers", "SMB / MSME"],
        "data_handled": [
            "Payments / financial transactions",
            "Personal identity data (KYC / Aadhaar)",
            "Customer behavioural / usage data",
            "Sensitive personal data (DPDP Act)",
        ],
        "regulatory": ["RBI / SEBI / IRDAI licensed", "DPDP Act obligations", "IT Act / CERT-In obligations"],
        "physical_assets": ["Office / coworking space", "Data centre / server room"],
        "rbi_registration": True,
        "payment_or_card_program": True,
        "cert_in_poc_designated": True,
        "sdf_probability": 0.8,
        "b2b_pct": 0.35,
        "facility_climate_risk_zone": "Low",
    },
    "healthtech": {
        "sector": "Healthtech",
        "sub_sector": "Healthtech.Telemedicine",
        "operations": "Hybrid",
        "data_sensitivity": "High",
        "customer_type": ["B2B Enterprise", "B2C Consumers"],
        "data_handled": [
            "Health / medical records",
            "Personal identity data (KYC / Aadhaar)",
            "Sensitive personal data (DPDP Act)",
            "Customer behavioural / usage data",
        ],
        "regulatory": ["DPDP Act obligations", "IT Act / CERT-In obligations", "NMC / telemedicine regulations"],
        "physical_assets": ["Office / coworking space", "Medical devices / diagnostic equipment", "Data centre / server room"],
        "healthcare_operations": True,
        "cert_in_poc_designated": True,
        "sdf_probability": 0.8,
        "b2b_pct": 0.55,
        "facility_climate_risk_zone": "Low",
    },
    "saas": {
        "sector": "SaaS / Enterprise Software",
        "operations": "Digital-only",
        "data_sensitivity": "High",
        "customer_type": ["B2B Enterprise", "SMB / MSME"],
        "data_handled": [
            "Customer behavioural / usage data",
            "Employee / HR data (payroll, biometrics)",
            "Intellectual property / source code",
            "Sensitive personal data (DPDP Act)",
        ],
        "regulatory": ["DPDP Act obligations", "IT Act / CERT-In obligations"],
        "physical_assets": ["Office / coworking space", "Data centre / server room"],
        "cert_in_poc_designated": True,
        "sdf_probability": 0.7,
        "ai_in_product": True,
        "ai_tier": "Applied",
        "b2b_pct": 0.95,
        "facility_climate_risk_zone": "Low",
    },
    "d2c": {
        "sector": "D2C / Consumer Brands",
        "operations": "Hybrid",
        "data_sensitivity": "Medium",
        "customer_type": ["B2C Consumers", "D2C / Marketplace"],
        "data_handled": ["Customer behavioural / usage data", "Physical inventory / goods"],
        "regulatory": ["DPDP Act obligations", "BIS / QCO product certification", "EPR / environmental compliance"],
        "physical_assets": ["Warehouse / fulfilment centre", "Retail stores / kiosks", "Office / coworking space"],
        "product_recall_exposure": True,
        "b2b_pct": 0.15,
        "facility_climate_risk_zone": "Medium",
    },
    "foodtech": {
        "sector": "Foodtech / Cloud Kitchen",
        "operations": "Hybrid",
        "data_sensitivity": "Medium",
        "customer_type": ["B2C Consumers", "D2C / Marketplace"],
        "data_handled": ["Customer behavioural / usage data", "Location / GPS tracking data", "Physical inventory / goods"],
        "regulatory": ["FSSAI / food safety", "DPDP Act obligations", "Labour Codes / gig worker regulations"],
        "physical_assets": ["Kitchen / food processing", "Cold chain / refrigeration", "Warehouse / fulfilment centre"],
        "food_or_pharma_manufacturing": True,
        "product_recall_exposure": True,
        "gig_headcount_pct": 0.25,
        "facility_climate_risk_zone": "Medium",
    },
    "logistics": {
        "sector": "Logistics / Mobility",
        "sub_sector": "Logistics.Last_Mile_Delivery",
        "operations": "Hybrid",
        "data_sensitivity": "Medium",
        "customer_type": ["B2B Enterprise", "B2C Consumers", "SMB / MSME"],
        "data_handled": ["Location / GPS tracking data", "Employee / HR data (payroll, biometrics)", "Physical inventory / goods"],
        "regulatory": ["MV Act / transport regulations", "Labour Codes / gig worker regulations", "DPDP Act obligations"],
        "physical_assets": ["Vehicles / delivery fleet", "Warehouse / fulfilment centre", "Office / coworking space"],
        "fleet_count": 500,
        "gig_headcount_pct": 0.45,
        "b2b_pct": 0.55,
        "facility_climate_risk_zone": "Medium",
    },
    "edtech": {
        "sector": "Edtech",
        "operations": "Digital-only",
        "data_sensitivity": "High",
        "customer_type": ["B2C Consumers", "B2B Enterprise"],
        "data_handled": ["Minors' / children's data", "Customer behavioural / usage data", "Sensitive personal data (DPDP Act)"],
        "regulatory": ["DPDP Act obligations", "IT Act / CERT-In obligations"],
        "physical_assets": ["Office / coworking space", "Data centre / server room"],
        "cert_in_poc_designated": True,
        "sdf_probability": 0.75,
        "b2b_pct": 0.35,
        "facility_climate_risk_zone": "Low",
    },
    "deeptech": {
        "sector": "Deeptech / AI / Robotics",
        "sub_sector": "Deeptech.Hardware_Robotics",
        "operations": "Hardware / IoT",
        "data_sensitivity": "High",
        "customer_type": ["B2B Enterprise", "Government / PSU"],
        "data_handled": ["Intellectual property / source code", "Customer behavioural / usage data", "Sensitive personal data (DPDP Act)"],
        "regulatory": ["BIS / QCO product certification", "IT Act / CERT-In obligations"],
        "physical_assets": ["Lab / R&D equipment", "Manufacturing plant / factory", "Office / coworking space"],
        "ai_in_product": True,
        "ai_tier": "Applied",
        "hardware_software_split": 0.75,
        "b2b_pct": 0.9,
        "facility_climate_risk_zone": "Medium",
    },
    "spacetech": {
        "sector": "Deeptech / AI / Robotics",
        "operations": "Hardware / IoT",
        "data_sensitivity": "High",
        "customer_type": ["Government / PSU", "B2B Enterprise"],
        "data_handled": ["Intellectual property / source code", "Sensitive personal data (DPDP Act)"],
        "regulatory": ["BIS / QCO product certification", "IT Act / CERT-In obligations"],
        "physical_assets": ["Lab / R&D equipment", "Manufacturing plant / factory"],
        "hardware_software_split": 0.85,
        "b2b_pct": 0.95,
        "facility_climate_risk_zone": "Medium",
    },
    "cleantech": {
        "sector": "Cleantech / Climatetech",
        "operations": "Hybrid",
        "data_sensitivity": "Medium",
        "customer_type": ["B2B Enterprise", "Government / PSU"],
        "data_handled": ["Physical inventory / goods", "Customer behavioural / usage data"],
        "regulatory": ["EPR / environmental compliance", "SEBI BRSR / ESG reporting", "BIS / QCO product certification"],
        "physical_assets": ["Solar / clean energy infrastructure", "Manufacturing plant / factory", "Warehouse / fulfilment centre"],
        "hardware_software_split": 0.7,
        "listed_customer_brsr_dependency": True,
        "facility_climate_risk_zone": "High",
    },
    "agritech": {
        "sector": "Agritech",
        "operations": "Hybrid",
        "data_sensitivity": "Medium",
        "customer_type": ["B2B Enterprise", "SMB / MSME"],
        "data_handled": ["Physical inventory / goods", "Location / GPS tracking data", "Customer behavioural / usage data"],
        "regulatory": ["EPR / environmental compliance", "DPDP Act obligations"],
        "physical_assets": ["Warehouse / fulfilment centre", "Cold chain / refrigeration", "Vehicles / delivery fleet"],
        "fleet_count": 120,
        "b2b_pct": 0.8,
        "facility_climate_risk_zone": "High",
    },
    "gaming_media": {
        "sector": "Gaming / Media / Content",
        "operations": "Digital-only",
        "data_sensitivity": "High",
        "customer_type": ["B2C Consumers"],
        "data_handled": ["Customer behavioural / usage data", "Payments / financial transactions", "Sensitive personal data (DPDP Act)"],
        "regulatory": ["DPDP Act obligations", "IT Act / CERT-In obligations", "Competition Act / CCI"],
        "physical_assets": ["Office / coworking space", "Data centre / server room"],
        "payment_or_card_program": True,
        "cert_in_poc_designated": True,
        "sdf_probability": 0.7,
        "facility_climate_risk_zone": "Low",
    },
}


SCALES = {
    "growth": {"funding_stage": "Series B+", "team_size": 2500, "annual_revenue_cr": 2500, "assets_cr": 180, "gross_profit_cr": 500, "fundraising_cr": 3000},
    "large": {"funding_stage": "Series B+", "team_size": 900, "annual_revenue_cr": 650, "assets_cr": 80, "gross_profit_cr": 130, "fundraising_cr": 1200},
    "mid": {"funding_stage": "Series B+", "team_size": 320, "annual_revenue_cr": 180, "assets_cr": 35, "gross_profit_cr": 40, "fundraising_cr": 450},
    "series_a": {"funding_stage": "Series A", "team_size": 120, "annual_revenue_cr": 45, "assets_cr": 12, "gross_profit_cr": 9, "fundraising_cr": 120},
    "seed": {"funding_stage": "Seed", "team_size": 32, "annual_revenue_cr": 4.5, "assets_cr": 1.8, "gross_profit_cr": 0.9, "fundraising_cr": 12},
    "pre_seed": {"funding_stage": "Pre-seed", "team_size": 9, "annual_revenue_cr": 0.75, "assets_cr": 0.35, "gross_profit_cr": 0.15, "fundraising_cr": 2},
}


COMPANY_SEEDS = [
    ("Razorpay", "fintech_payments", "growth"), ("PhonePe", "fintech_payments", "growth"), ("Paytm", "fintech_payments", "growth"),
    ("CRED", "fintech_payments", "large"), ("Groww", "fintech_lending", "growth"), ("Zerodha", "fintech_lending", "growth"),
    ("BharatPe", "fintech_payments", "large"), ("Pine Labs", "fintech_payments", "growth"), ("MobiKwik", "fintech_payments", "large"),
    ("Jupiter", "fintech_lending", "mid"), ("Fi Money", "fintech_lending", "mid"), ("Jar", "fintech_lending", "series_a"),
    ("KreditBee", "fintech_lending", "large"), ("Lendingkart", "fintech_lending", "large"), ("Moneyview", "fintech_lending", "large"),
    ("Perfios", "fintech_payments", "large"), ("OneCard", "fintech_lending", "large"), ("Open Financial", "fintech_payments", "mid"),
    ("Niyo", "fintech_lending", "mid"), ("INDmoney", "fintech_lending", "mid"),
    ("Practo", "healthtech", "large"), ("PharmEasy", "healthtech", "growth"), ("Tata 1mg", "healthtech", "growth"),
    ("HealthifyMe", "healthtech", "mid"), ("MediBuddy", "healthtech", "large"), ("Cult.fit", "healthtech", "large"),
    ("Ultrahuman", "healthtech", "mid"), ("Orange Health", "healthtech", "series_a"), ("Redcliffe Labs", "healthtech", "mid"),
    ("Truemeds", "healthtech", "mid"),
    ("Freshworks", "saas", "growth"), ("Zoho", "saas", "growth"), ("Postman", "saas", "growth"), ("Chargebee", "saas", "large"),
    ("BrowserStack", "saas", "large"), ("Hasura", "saas", "mid"), ("Whatfix", "saas", "large"), ("Yellow.ai", "saas", "large"),
    ("LeadSquared", "saas", "large"), ("Darwinbox", "saas", "large"), ("Icertis", "saas", "growth"), ("Uniphore", "saas", "large"),
    ("Gupshup", "saas", "large"), ("MoEngage", "saas", "large"), ("CleverTap", "saas", "large"),
    ("Lenskart", "d2c", "growth"), ("boAt", "d2c", "growth"), ("Mamaearth", "d2c", "growth"), ("SUGAR Cosmetics", "d2c", "large"),
    ("Nykaa", "d2c", "growth"), ("Wakefit", "d2c", "large"), ("Urban Company", "d2c", "growth"), ("Country Delight", "foodtech", "large"),
    ("Rebel Foods", "foodtech", "growth"), ("Licious", "foodtech", "large"), ("WOW Skin Science", "d2c", "large"), ("Atomberg", "d2c", "mid"),
    ("Sleepy Owl", "foodtech", "series_a"), ("Blue Tokai", "foodtech", "series_a"), ("The Whole Truth", "foodtech", "series_a"),
    ("Swiggy", "logistics", "growth"), ("Zomato", "logistics", "growth"), ("Zepto", "logistics", "growth"), ("Blinkit", "logistics", "growth"),
    ("Dunzo", "logistics", "large"), ("Porter", "logistics", "large"), ("Rapido", "logistics", "large"), ("Ola Electric", "cleantech", "growth"),
    ("Ather Energy", "cleantech", "growth"), ("BluSmart", "cleantech", "large"), ("Delhivery", "logistics", "growth"),
    ("Shadowfax", "logistics", "large"), ("BlackBuck", "logistics", "large"), ("Rivigo", "logistics", "large"), ("Loadshare", "logistics", "mid"),
    ("BYJU'S", "edtech", "growth"), ("Unacademy", "edtech", "large"), ("Vedantu", "edtech", "large"), ("Physics Wallah", "edtech", "growth"),
    ("Classplus", "edtech", "mid"), ("upGrad", "edtech", "growth"), ("Simplilearn", "edtech", "large"), ("Leverage Edu", "edtech", "mid"),
    ("Sarvam AI", "saas", "series_a"), ("Krutrim", "saas", "mid"), ("Netradyne", "deeptech", "large"), ("ideaForge", "deeptech", "large"),
    ("Agnikul Cosmos", "spacetech", "mid"), ("Skyroot Aerospace", "spacetech", "mid"), ("Pixxel", "spacetech", "mid"),
    ("Dhruva Space", "spacetech", "series_a"), ("Ati Motors", "deeptech", "mid"), ("GreyOrange", "deeptech", "large"),
    ("Log9 Materials", "cleantech", "mid"), ("Battery Smart", "cleantech", "mid"), ("SolarSquare", "cleantech", "series_a"),
    ("Ninjacart", "agritech", "large"), ("DeHaat", "agritech", "large"), ("WayCool", "agritech", "large"), ("CropIn", "agritech", "mid"),
    ("AstraPay Labs", "fintech_payments", "seed"), ("LedgerLeaf", "fintech_lending", "pre_seed"),
    ("PulseDesk AI", "healthtech", "seed"), ("CareNest ClinicOps", "healthtech", "pre_seed"),
    ("CloudPilot HQ", "saas", "seed"), ("OpsMint", "saas", "pre_seed"),
    ("FreshBite Kitchen", "foodtech", "seed"), ("BeanCart", "foodtech", "pre_seed"),
    ("ThreadLoop", "d2c", "seed"), ("KoshaWear", "d2c", "pre_seed"),
    ("FleetNest", "logistics", "seed"), ("RouteHawk", "logistics", "pre_seed"),
    ("TutorGrid", "edtech", "seed"), ("KiddoLearn", "edtech", "pre_seed"),
    ("RoboYard", "deeptech", "seed"), ("VisionForge Robotics", "deeptech", "pre_seed"),
    ("SolarMitra", "cleantech", "seed"), ("CarbonTrail", "cleantech", "pre_seed"),
    ("AgroPulse", "agritech", "seed"), ("RainLedger Farms", "agritech", "pre_seed"),
]


def _slug(value: str) -> str:
    return "".join(ch.lower() for ch in value if ch.isalnum())


def _build_profile(name: str, archetype_key: str, scale_key: str) -> dict:
    archetype = deepcopy(ARCHETYPES[archetype_key])
    scale = SCALES[scale_key]
    profile = {
        "startup_name": name,
        "funding_stage": scale["funding_stage"],
        "team_size": scale["team_size"],
        "annual_revenue_cr": scale["annual_revenue_cr"],
        "total_insurable_asset_value_cr": scale["assets_cr"],
        "gross_profit_cr": scale["gross_profit_cr"],
        "cumulative_fundraising_inr_cr": scale["fundraising_cr"],
        "has_investors": "Yes",
        "holdco_domicile": "India",
        "dpiit_recognition": True,
        "posh_ic_constituted": True,
        "claims_last_3_years": False,
        "data_localisation_status": "Full_onshore",
        "state_footprint": ["Karnataka", "Maharashtra", "Delhi", "Telangana"],
        "product_description": f"Assumption-based starter profile for {name}, generated from the {archetype_key.replace('_', ' ')} archetype.",
        "biggest_fear": "A major operational, regulatory, cyber, or liability incident affecting customers, investors, and business continuity.",
        "profile_source": "Seeded public-company starter profile; replace assumptions with verified company inputs before quoting.",
    }
    profile.update(archetype)
    if profile.get("physical_assets") and "Vehicles / delivery fleet" in profile["physical_assets"]:
        profile["fleet_count"] = max(profile.get("fleet_count", 0), scale["team_size"])
    return profile


COMPANY_PROFILES = {
    name: _build_profile(name, archetype, scale)
    for name, archetype, scale in COMPANY_SEEDS
}


_DEMO_PROFILES: dict[str, dict] = {
    "RazorFlow Pay": {
        "startup_name": "RazorFlow Pay",
        "sector": "Fintech",
        "sub_sector": "Fintech.PA_PG",
        "funding_stage": "Series B+",
        "team_size": 180,
        "operations": "Hybrid",
        "data_sensitivity": "High",
        "product_description": "Payment gateway and payout API for SMB merchants.",
        "customer_type": ["B2B Enterprise", "SMB / MSME"],
        "data_handled": ["Payments / financial transactions", "Personal identity data (KYC / Aadhaar)", "Sensitive personal data (DPDP Act)"],
        "regulatory": ["RBI / SEBI / IRDAI licensed", "DPDP Act obligations", "IT Act / CERT-In obligations"],
        "physical_assets": ["Office / coworking space", "Data centre / server room"],
        "has_investors": "Yes",
        "biggest_fear": "Payment data breach or RBI audit issue.",
        "rbi_registration": True,
        "payment_or_card_program": True,
        "annual_revenue_cr": 120,
        "total_insurable_asset_value_cr": 8,
    },
    "MediLink AI": {
        "startup_name": "MediLink AI",
        "sector": "Healthtech",
        "sub_sector": "Healthtech.Telemedicine",
        "funding_stage": "Series A",
        "team_size": 72,
        "operations": "Hybrid",
        "data_sensitivity": "High",
        "product_description": "Telemedicine platform with AI-assisted triage and doctor consultations.",
        "customer_type": ["B2C Consumers", "B2B Enterprise"],
        "data_handled": ["Health / medical records", "Personal identity data (KYC / Aadhaar)", "Sensitive personal data (DPDP Act)"],
        "regulatory": ["DPDP Act obligations", "IT Act / CERT-In obligations", "NMC / telemedicine regulations"],
        "physical_assets": ["Office / coworking space", "Medical devices / diagnostic equipment"],
        "has_investors": "Yes",
        "biggest_fear": "Patient data breach or wrong clinical recommendation.",
        "annual_revenue_cr": 28,
        "total_insurable_asset_value_cr": 4,
    },
    "CloudDesk Systems": {
        "startup_name": "CloudDesk Systems",
        "sector": "SaaS / Enterprise Software",
        "funding_stage": "Series A",
        "team_size": 95,
        "operations": "Digital-only",
        "data_sensitivity": "Medium",
        "product_description": "Workflow automation SaaS for enterprise finance and operations teams.",
        "customer_type": ["B2B Enterprise"],
        "data_handled": ["Customer behavioural / usage data", "Intellectual property / source code", "Employee / HR data (payroll, biometrics)"],
        "regulatory": ["DPDP Act obligations", "IT Act / CERT-In obligations"],
        "physical_assets": ["None - fully cloud"],
        "has_investors": "Yes",
        "biggest_fear": "Enterprise outage or customer data incident.",
        "annual_revenue_cr": 35,
        "total_insurable_asset_value_cr": 2,
    },
    "FreshCart Foods": {
        "startup_name": "FreshCart Foods",
        "sector": "Foodtech / Cloud Kitchen",
        "funding_stage": "Seed",
        "team_size": 42,
        "operations": "Hybrid",
        "data_sensitivity": "Medium",
        "product_description": "Cloud kitchen brand selling packaged ready-to-eat meals through marketplaces.",
        "customer_type": ["B2C Consumers", "D2C / Marketplace"],
        "data_handled": ["Customer behavioural / usage data", "Physical inventory / goods"],
        "regulatory": ["FSSAI / food safety", "Labour Codes / gig worker regulations"],
        "physical_assets": ["Kitchen / food processing", "Cold chain / refrigeration"],
        "has_investors": "Yes",
        "biggest_fear": "Food contamination claim or kitchen fire.",
        "annual_revenue_cr": 8,
        "total_insurable_asset_value_cr": 2,
    },
    "VoltFleet Mobility": {
        "startup_name": "VoltFleet Mobility",
        "sector": "Logistics / Mobility",
        "funding_stage": "Series B+",
        "team_size": 220,
        "operations": "Hybrid",
        "data_sensitivity": "Medium",
        "product_description": "EV last-mile delivery fleet for ecommerce and grocery platforms.",
        "customer_type": ["B2B Enterprise", "D2C / Marketplace"],
        "data_handled": ["Location / GPS tracking data", "Employee / HR data (payroll, biometrics)"],
        "regulatory": ["MV Act / transport regulations", "Labour Codes / gig worker regulations", "EPR / environmental compliance"],
        "physical_assets": ["Vehicles / delivery fleet", "Warehouse / fulfilment centre"],
        "has_investors": "Yes",
        "biggest_fear": "Fleet accident, vehicle fire, or gig-worker claim.",
        "fleet_count": 180,
        "annual_revenue_cr": 95,
        "total_insurable_asset_value_cr": 30,
    },
    "RoboFab Labs": {
        "startup_name": "RoboFab Labs",
        "sector": "Deeptech / AI / Robotics",
        "sub_sector": "Deeptech.Hardware_Robotics",
        "funding_stage": "Series A",
        "team_size": 58,
        "operations": "Hybrid",
        "data_sensitivity": "Medium",
        "product_description": "Robotics startup building warehouse automation arms and AI control software.",
        "customer_type": ["B2B Enterprise"],
        "data_handled": ["Intellectual property / source code", "Customer behavioural / usage data"],
        "regulatory": ["BIS / QCO product certification"],
        "physical_assets": ["Lab / R&D equipment", "Manufacturing plant / factory"],
        "has_investors": "Yes",
        "biggest_fear": "Prototype failure causing customer loss or equipment damage.",
        "annual_revenue_cr": 18,
        "total_insurable_asset_value_cr": 12,
    },
    "LearnLoop Kids": {
        "startup_name": "LearnLoop Kids",
        "sector": "Edtech",
        "sub_sector": "Edtech.K12_Children",
        "funding_stage": "Seed",
        "team_size": 36,
        "operations": "Digital-only",
        "data_sensitivity": "High",
        "product_description": "Online learning app for school children with adaptive assessments.",
        "customer_type": ["B2C Consumers"],
        "data_handled": ["Minors' / children's data", "Customer behavioural / usage data", "Sensitive personal data (DPDP Act)"],
        "regulatory": ["DPDP Act obligations"],
        "physical_assets": ["None - fully cloud"],
        "has_investors": "Yes",
        "biggest_fear": "Child data privacy complaint or platform outage during exams.",
        "annual_revenue_cr": 4,
        "total_insurable_asset_value_cr": 1,
    },
    "GreenGrid Solar": {
        "startup_name": "GreenGrid Solar",
        "sector": "Cleantech / Climatetech",
        "funding_stage": "Series A",
        "team_size": 88,
        "operations": "Hybrid",
        "data_sensitivity": "Low",
        "product_description": "Commercial rooftop solar installation and monitoring platform.",
        "customer_type": ["B2B Enterprise", "SMB / MSME"],
        "data_handled": ["Customer behavioural / usage data"],
        "regulatory": ["EPR / environmental compliance", "SEBI BRSR / ESG reporting"],
        "physical_assets": ["Solar / clean energy infrastructure", "Vehicles / delivery fleet"],
        "has_investors": "Yes",
        "biggest_fear": "Solar asset damage, contractor injury, or performance dispute.",
        "annual_revenue_cr": 32,
        "total_insurable_asset_value_cr": 20,
    },
    "StyleNest D2C": {
        "startup_name": "StyleNest D2C",
        "sector": "D2C / Consumer Brands",
        "sub_sector": "D2C.Apparel_Footwear",
        "funding_stage": "Series A",
        "team_size": 64,
        "operations": "Hybrid",
        "data_sensitivity": "Medium",
        "product_description": "D2C fashion brand selling through own website and marketplaces.",
        "customer_type": ["B2C Consumers", "D2C / Marketplace"],
        "data_handled": ["Customer behavioural / usage data", "Physical inventory / goods"],
        "regulatory": ["BIS / QCO product certification", "Labour Codes / gig worker regulations"],
        "physical_assets": ["Warehouse / fulfilment centre", "Retail stores / kiosks"],
        "has_investors": "Yes",
        "biggest_fear": "Warehouse fire, product quality claim, or marketplace disruption.",
        "annual_revenue_cr": 22,
        "total_insurable_asset_value_cr": 5,
    },
    "CreatorPlay Studios": {
        "startup_name": "CreatorPlay Studios",
        "sector": "Gaming / Media / Content",
        "sub_sector": "Gaming.Casual_Esports",
        "funding_stage": "Seed",
        "team_size": 28,
        "operations": "Digital-only",
        "data_sensitivity": "Medium",
        "product_description": "Casual mobile gaming studio with creator-led live tournaments.",
        "customer_type": ["B2C Consumers"],
        "data_handled": ["Customer behavioural / usage data", "Intellectual property / source code"],
        "regulatory": ["IT Act / CERT-In obligations"],
        "physical_assets": ["None - fully cloud"],
        "has_investors": "Yes",
        "biggest_fear": "IP dispute, game outage, or user data incident.",
        "annual_revenue_cr": 3,
        "total_insurable_asset_value_cr": 1,
    },
}

COMPANY_PROFILES.update(_DEMO_PROFILES)


def search_company_profiles(query: str = "", limit: int = 10) -> list[dict]:
    q = _slug(query)
    prefix_rows = []
    for name, profile in COMPANY_PROFILES.items():
        slug = _slug(name)
        if not q or slug.startswith(q):
            target = prefix_rows
        else:
            continue
        target.append({
                "name": name,
                "sector": profile["sector"],
                "funding_stage": profile["funding_stage"],
                "team_size": profile["team_size"],
                "operations": profile["operations"],
        })
    if q:
        rows = sorted(prefix_rows, key=lambda item: (len(_slug(item["name"])), item["name"].lower()))
    else:
        rows = sorted(prefix_rows, key=lambda item: item["name"].lower())
    return rows[: max(1, min(limit, len(COMPANY_PROFILES)))]


def get_company_profile(name: str) -> dict | None:
    target = _slug(name)
    for company_name, profile in COMPANY_PROFILES.items():
        if _slug(company_name) == target:
            return deepcopy(profile)
    return None


def company_profile_count() -> int:
    return len(COMPANY_PROFILES)
