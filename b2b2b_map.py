import re


B2B2B_MAP = {
    ("Fintech", "SMB / MSME"): [
        {
            "product": "Fire + Equipment Cover",
            "rationale": "NBFC lending is often secured against SME physical assets; insuring the asset protects the loan book.",
            "premium_per_customer": "INR 0.5-2 lakhs per SME borrower",
            "icici_product_key": "property_fire",
            "penetration_assumption": 0.10,
        },
        {
            "product": "Credit Shield / Loan Protection",
            "rationale": "Loan protection can reduce default pressure if a borrower dies or is disabled.",
            "premium_per_customer": "INR 0.2-0.8 lakhs per borrower",
            "icici_product_key": "key_person",
            "penetration_assumption": 0.10,
        },
    ],
    ("Fintech", "B2C Consumers"): [
        {
            "product": "Consumer Payment Protection",
            "rationale": "BNPL and EMI platforms can naturally distribute repayment-protection add-ons.",
            "premium_per_customer": "INR 0.02-0.1 lakhs per borrower",
            "icici_product_key": "group_pa",
            "penetration_assumption": 0.15,
        }
    ],
    ("Logistics / Mobility", "SMB / MSME"): [
        {
            "product": "Marine Cargo + Goods in Transit",
            "rationale": "SME shippers on the platform bear cargo loss risk; transit cover protects every truckload.",
            "premium_per_customer": "INR 0.3-1.5 lakhs per SME shipper",
            "icici_product_key": "marine_transit",
            "penetration_assumption": 0.10,
        },
        {
            "product": "Motor Fleet / Goods Vehicle Insurance",
            "rationale": "Owner-operators need commercial vehicle cover and the platform creates a fleet-program opportunity.",
            "premium_per_customer": "INR 0.5-2 lakhs per vehicle owner",
            "icici_product_key": "motor_fleet",
            "penetration_assumption": 0.15,
        },
    ],
    ("HRtech", "B2B Enterprise"): [
        {
            "product": "Group Health Insurance",
            "rationale": "HR platforms already manage employee benefits and can co-distribute group health.",
            "premium_per_customer": "INR 2-15 lakhs per corporate client",
            "icici_product_key": "employee_health",
            "penetration_assumption": 0.10,
        },
        {
            "product": "Group Personal Accident",
            "rationale": "Group PA is a low-ticket add-on to corporate employee-benefit workflows.",
            "premium_per_customer": "INR 0.3-1.5 lakhs per corporate client",
            "icici_product_key": "group_pa",
            "penetration_assumption": 0.20,
        },
    ],
    ("Edtech", "B2C Consumers"): [
        {
            "product": "Personal Accident - Student",
            "rationale": "Edtech platforms have a direct parent/student billing relationship, making embedded PA low-friction.",
            "premium_per_customer": "INR 0.05-0.2 lakhs per student",
            "icici_product_key": "group_pa",
            "penetration_assumption": 0.05,
        }
    ],
    ("Healthtech", "B2B Enterprise"): [
        {
            "product": "Group Health + OPD Rider",
            "rationale": "Hospital and clinic clients need employee health cover and already trust the platform.",
            "premium_per_customer": "INR 3-20 lakhs per hospital client",
            "icici_product_key": "employee_health",
            "penetration_assumption": 0.10,
        },
        {
            "product": "Healthcare Professional Liability",
            "rationale": "Hospitals and clinics using the platform face medical negligence exposure.",
            "premium_per_customer": "INR 1-5 lakhs per clinic",
            "icici_product_key": "clinical_trials",
            "penetration_assumption": 0.08,
        },
    ],
    ("Agritech", "SMB / MSME"): [
        {
            "product": "Crop + Weather Parametric Insurance",
            "rationale": "Farmer and FPO customers face rainfall and yield risk that can be distributed through the platform.",
            "premium_per_customer": "INR 0.1-0.5 lakhs per farmer",
            "icici_product_key": "property_fire",
            "penetration_assumption": 0.10,
        },
        {
            "product": "Marine Inland Transit",
            "rationale": "Farmers and FPOs ship produce to mandis and processors; transit cover protects goods in motion.",
            "premium_per_customer": "INR 0.05-0.3 lakhs per FPO",
            "icici_product_key": "marine_transit",
            "penetration_assumption": 0.08,
        },
    ],
    ("D2C / Consumer Brands", "D2C / Marketplace"): [
        {
            "product": "Product Liability",
            "rationale": "D2C sellers on marketplaces face strict product liability and can be covered through platform journeys.",
            "premium_per_customer": "INR 0.4-2 lakhs per D2C seller",
            "icici_product_key": "product_liability",
            "penetration_assumption": 0.10,
        }
    ],
    ("SaaS / Enterprise Software", "B2B Enterprise"): [
        {
            "product": "Professional Indemnity / E&O",
            "rationale": "SaaS customers and vendors frequently need PI/E&O to satisfy enterprise contract prerequisites.",
            "premium_per_customer": "INR 0.5-3 lakhs per SMB client",
            "icici_product_key": "professional_indemnity",
            "penetration_assumption": 0.10,
        }
    ],
    ("Foodtech / Cloud Kitchen", "B2C Consumers"): [
        {
            "product": "Food Contamination / Product Recall",
            "rationale": "Aggregators and partner kitchens face food-safety and recall exposure.",
            "premium_per_customer": "INR 0.1-0.5 lakhs per kitchen partner",
            "icici_product_key": "product_liability",
            "penetration_assumption": 0.08,
        }
    ],
    ("Cleantech / Climatetech", "B2B Enterprise"): [
        {
            "product": "Contractor All Risk + Erection All Risk",
            "rationale": "Solar, EV, and energy infra deployments need project-period CAR/EAR cover.",
            "premium_per_customer": "INR 1-5 lakhs per installation project",
            "icici_product_key": "contractors_all_risk",
            "penetration_assumption": 0.12,
        }
    ],
    ("Legaltech", "B2B Enterprise"): [
        {
            "product": "Professional Indemnity - Legal",
            "rationale": "Law firm and legal-service clients need PI, and the platform manages their matter workflow.",
            "premium_per_customer": "INR 1-8 lakhs per law firm",
            "icici_product_key": "professional_indemnity",
            "penetration_assumption": 0.08,
        }
    ],
    ("Gaming / Media / Content", "B2C Consumers"): [
        {
            "product": "Personal Accident - Player",
            "rationale": "Esports and events create player injury exposure that can be embedded at registration.",
            "premium_per_customer": "INR 0.02-0.1 lakhs per esports player",
            "icici_product_key": "group_pa",
            "penetration_assumption": 0.05,
        }
    ],
}


def _range_lakhs(text: str) -> tuple[float, float] | None:
    match = re.search(r"([0-9]+(?:\.[0-9]+)?)-([0-9]+(?:\.[0-9]+)?)", text)
    if not match:
        return None
    return float(match.group(1)), float(match.group(2))


def get_b2b2b_opportunities(sector: str, customer_types: list, customer_base_estimate: int = 0) -> list[dict]:
    results = []
    for ctype in customer_types or []:
        for opp in B2B2B_MAP.get((sector, ctype), []):
            item = dict(opp)
            item["customer_type"] = ctype
            if customer_base_estimate > 0:
                penetrated = int(customer_base_estimate * opp["penetration_assumption"])
                item["penetration_count"] = penetrated
                parsed = _range_lakhs(opp["premium_per_customer"])
                if parsed:
                    item["total_opportunity_lakhs_min"] = round(parsed[0] * penetrated, 2)
                    item["total_opportunity_lakhs_max"] = round(parsed[1] * penetrated, 2)
            results.append(item)
    return results
