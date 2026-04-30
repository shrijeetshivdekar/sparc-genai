RISK_APPETITE = {
    "cyber_liability": {
        "_default": "moderate",
        "_requires_fire_first": False,
        "Fintech": "bad",
        "Gaming / Media / Content": "bad",
        "Healthtech": "moderate",
        "SaaS / Enterprise Software": "moderate",
        "Deeptech / AI / Robotics": "good",
        "Edtech": "moderate",
        "HRtech": "moderate",
        "Legaltech": "good",
        "D2C / Consumer Brands": "moderate",
        "Agritech": "good",
        "Cleantech / Climatetech": "good",
        "Logistics / Mobility": "moderate",
        "Foodtech / Cloud Kitchen": "moderate",
    },
    "dno_liability": {
        "_default": "good",
        "_requires_fire_first": False,
        "Fintech": "moderate",
        "Gaming / Media / Content": "bad",
        "Crypto/VDA": "bad",
        "Healthtech": "good",
        "SaaS / Enterprise Software": "good",
        "Deeptech / AI / Robotics": "good",
    },
    "professional_indemnity": {
        "_default": "moderate",
        "_requires_fire_first": False,
        "Fintech": "moderate",
        "Healthtech": "good",
        "SaaS / Enterprise Software": "good",
        "Legaltech": "good",
        "HRtech": "good",
        "Deeptech / AI / Robotics": "moderate",
        "Edtech": "moderate",
        "Gaming / Media / Content": "tbd",
    },
    "business_interruption": {
        "_default": "moderate",
        "_requires_fire_first": True,
        "Fintech": "moderate",
        "Healthtech": "good",
        "Logistics / Mobility": "good",
        "D2C / Consumer Brands": "good",
        "Foodtech / Cloud Kitchen": "good",
        "SaaS / Enterprise Software": "moderate",
        "Agritech": "good",
        "Cleantech / Climatetech": "good",
    },
    "property_fire": {
        "_default": "good",
        "_requires_fire_first": False,
        "SaaS / Enterprise Software": "moderate",
        "Fintech": "moderate",
        "Legaltech": "moderate",
        "HRtech": "moderate",
    },
    "employee_health": {"_default": "good", "_requires_fire_first": False},
    "group_pa": {
        "_default": "good",
        "_requires_fire_first": False,
        "Logistics / Mobility": "good",
        "Agritech": "good",
    },
    "employees_comp": {
        "_default": "good",
        "_requires_fire_first": False,
        "SaaS / Enterprise Software": "moderate",
        "Fintech": "moderate",
        "Legaltech": "moderate",
    },
    "product_liability": {
        "_default": "moderate",
        "_requires_fire_first": False,
        "D2C / Consumer Brands": "good",
        "Foodtech / Cloud Kitchen": "moderate",
        "Healthtech": "good",
        "Agritech": "good",
        "Deeptech / AI / Robotics": "moderate",
        "SaaS / Enterprise Software": "bad",
        "Fintech": "bad",
    },
    "marine_transit": {
        "_default": "good",
        "_requires_fire_first": False,
        "D2C / Consumer Brands": "good",
        "Logistics / Mobility": "good",
        "Agritech": "good",
        "Fintech": "bad",
        "SaaS / Enterprise Software": "bad",
    },
    "crime_fidelity": {
        "_default": "moderate",
        "_requires_fire_first": False,
        "Fintech": "good",
        "D2C / Consumer Brands": "moderate",
        "Foodtech / Cloud Kitchen": "good",
        "Gaming / Media / Content": "tbd",
        "Crypto/VDA": "bad",
    },
    "trade_credit": {
        "_default": "moderate",
        "_requires_fire_first": False,
        "Fintech": "good",
        "Logistics / Mobility": "good",
        "SaaS / Enterprise Software": "good",
        "D2C / Consumer Brands": "moderate",
        "Agritech": "good",
    },
    "motor_fleet": {
        "_default": "good",
        "_requires_fire_first": False,
        "SaaS / Enterprise Software": "bad",
        "Fintech": "bad",
        "Edtech": "bad",
        "Legaltech": "bad",
    },
    "drone_insurance": {
        "_default": "good",
        "_requires_fire_first": False,
        "Agritech": "good",
        "Logistics / Mobility": "good",
        "Deeptech / AI / Robotics": "good",
        "SaaS / Enterprise Software": "bad",
        "Fintech": "bad",
    },
    "clinical_trials": {
        "_default": "moderate",
        "_requires_fire_first": False,
        "Healthtech": "good",
        "Deeptech / AI / Robotics": "moderate",
    },
    "comprehensive_general_liability": {
        "_default": "good",
        "_requires_fire_first": False,
        "Fintech": "moderate",
        "SaaS / Enterprise Software": "good",
        "D2C / Consumer Brands": "good",
        "Logistics / Mobility": "good",
    },
    "key_person": {"_default": "good", "_requires_fire_first": False},
    "employment_practices": {
        "_default": "moderate",
        "_requires_fire_first": False,
        "Fintech": "moderate",
        "Healthtech": "moderate",
        "SaaS / Enterprise Software": "moderate",
    },
    "contractors_all_risk": {
        "_default": "moderate",
        "_requires_fire_first": False,
        "Cleantech / Climatetech": "good",
        "Agritech": "good",
        "Deeptech / AI / Robotics": "moderate",
        "Fintech": "bad",
        "SaaS / Enterprise Software": "bad",
    },
    "msme_suraksha": {
        "_default": "good",
        "_requires_fire_first": False,
        "SaaS / Enterprise Software": "moderate",
        "Fintech": "moderate",
    },
    "enterprise_secure": {
        "_default": "good",
        "_requires_fire_first": False,
        "SaaS / Enterprise Software": "moderate",
        "Fintech": "moderate",
        "Legaltech": "moderate",
    },
}

BAD_RISK_REASONS = {
    "cyber_liability": {
        "Fintech": "High claim frequency and adverse selection in fintech cyber; underwriters may require elevated deductibles.",
        "Gaming / Media / Content": "Ransomware and data extortion claims are disproportionately high in gaming and media platforms.",
    },
    "product_liability": {
        "SaaS / Enterprise Software": "Software-related failures are usually Professional Indemnity/E&O claims, not product liability claims.",
        "Fintech": "Financial service failures are handled through PI/E&O, not product liability.",
    },
    "dno_liability": {
        "Gaming / Media / Content": "Regulatory and litigation exposure is elevated in gaming and real-money media segments.",
        "Crypto/VDA": "Digital-asset platforms need bespoke underwriting outside normal D&O appetite.",
    },
    "marine_transit": {
        "Fintech": "Fintech companies have no physical goods to transit.",
        "SaaS / Enterprise Software": "Digital-only businesses have no cargo exposure.",
    },
    "motor_fleet": {
        "SaaS / Enterprise Software": "Digital-only business with no natural vehicle-fleet exposure.",
        "Fintech": "Digital-only business with no natural vehicle-fleet exposure.",
        "Edtech": "Digital-only business with no natural vehicle-fleet exposure.",
        "Legaltech": "Digital-only business with no natural vehicle-fleet exposure.",
    },
    "drone_insurance": {
        "SaaS / Enterprise Software": "No drone operations in a standard SaaS profile.",
        "Fintech": "No drone operations in a standard fintech profile.",
    },
    "crime_fidelity": {
        "Crypto/VDA": "Digital asset theft usually falls outside standard crime/fidelity policy scope.",
    },
    "contractors_all_risk": {
        "Fintech": "No construction or installation projects in fintech.",
        "SaaS / Enterprise Software": "No physical construction exposure.",
    },
}


def get_appetite(product_key: str, sector: str) -> str:
    entry = RISK_APPETITE.get(product_key, {})
    return entry.get(sector, entry.get("_default", "tbd"))


def get_bad_reason(product_key: str, sector: str) -> str:
    return BAD_RISK_REASONS.get(product_key, {}).get(sector, "Not a preferred risk for this sector.")


def requires_fire_first(product_key: str) -> bool:
    return RISK_APPETITE.get(product_key, {}).get("_requires_fire_first", False)
