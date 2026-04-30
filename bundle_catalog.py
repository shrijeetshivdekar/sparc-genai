from copy import deepcopy


BUNDLE_CATALOG = {
    "msme_suraksha_kavach": {
        "name": "MSME Suraksha Kavach",
        "il_product_name": "ICICI Lombard MSME Suraksha Kavach Package Policy - Advance",
        "mandatory_covers": ["property_fire", "burglary", "business_interruption"],
        "optional_covers": ["cyber_liability", "product_liability", "money_insurance", "public_liability", "employees_comp"],
        "prerequisites": {"business_interruption": "property_fire"},
        "eligible_sectors": {"D2C / Consumer Brands", "Logistics / Mobility", "Foodtech / Cloud Kitchen", "Agritech", "Cleantech / Climatetech", "Deeptech / AI / Robotics"},
        "eligible_stages": ["Pre-seed", "Seed", "Series A"],
        "description": "All-in-one MSME package for startups with premises, inventory, burglary, public liability, and optional cyber exposure.",
        "criticality": "High",
        "covers_criticality": {
            "property_fire": {"criticality": "Mandatory", "reason": "Physical inventory, leased premises, and lender covenants make fire cover foundational."},
            "burglary": {"criticality": "Mandatory", "reason": "Commercial premises and inventory need theft and burglary protection."},
            "business_interruption": {"criticality": "Recommended", "reason": "BI protects cash flow after insured physical damage and requires fire cover first."},
            "cyber_liability": {"criticality": "Optional", "reason": "Add if the startup accepts digital payments or handles customer data."},
            "product_liability": {"criticality": "Optional", "reason": "Add if selling physical goods to consumers or marketplaces."},
            "money_insurance": {"criticality": "Optional", "reason": "Add for retail, food, or cash-heavy operations."},
            "public_liability": {"criticality": "Optional", "reason": "Add where customers, vendors, or public visitors enter premises."},
            "employees_comp": {"criticality": "Optional", "reason": "Add for field, factory, warehouse, and delivery workforces."},
        },
    },
    "corporate_cover_ii": {
        "name": "Corporate Cover II",
        "il_product_name": "Corporate Cover II Insurance Policy",
        "mandatory_covers": ["property_fire", "business_interruption", "public_liability", "employees_comp"],
        "optional_covers": ["cyber_liability", "dno_liability", "professional_indemnity", "crime_fidelity", "marine_transit", "trade_credit"],
        "prerequisites": {"business_interruption": "property_fire"},
        "eligible_sectors": {"SaaS / Enterprise Software", "Fintech", "Healthtech", "Legaltech", "HRtech", "D2C / Consumer Brands", "Logistics / Mobility", "Cleantech / Climatetech", "Deeptech / AI / Robotics"},
        "eligible_stages": ["Series A", "Series B+"],
        "description": "Growth-stage corporate package combining property, BI, public liability, employees compensation, and optional financial lines.",
        "criticality": "High",
        "covers_criticality": {
            "property_fire": {"criticality": "Mandatory", "reason": "Series A+ asset and downtime exposure justify structured commercial property cover."},
            "business_interruption": {"criticality": "Mandatory", "reason": "Monthly burn and enterprise delivery commitments make downtime financially material."},
            "public_liability": {"criticality": "Mandatory", "reason": "Enterprise and vendor contracts frequently require third-party liability cover."},
            "employees_comp": {"criticality": "Mandatory", "reason": "Mandatory for hazardous occupations and important for distributed teams."},
            "cyber_liability": {"criticality": "Recommended", "reason": "Add where data sensitivity is medium/high or DPDPA exposure exists."},
            "dno_liability": {"criticality": "Recommended", "reason": "Institutional investors often require D&O after priced rounds."},
            "professional_indemnity": {"criticality": "Optional", "reason": "Add for B2B services, SaaS, consulting, and implementation contracts."},
            "crime_fidelity": {"criticality": "Optional", "reason": "Add for payment operations, finance teams, and insider fraud exposure."},
            "marine_transit": {"criticality": "Optional", "reason": "Add for physical goods shipped domestically or cross-border."},
            "trade_credit": {"criticality": "Optional", "reason": "Add where receivables are concentrated in a small number of customers."},
        },
    },
    "startup_shield_pack": {
        "name": "Startup Shield Pack",
        "il_product_name": "Business Shield SME / Business Guard Plus / I-select Liability Insurance",
        "mandatory_covers": ["cyber_liability", "dno_liability", "professional_indemnity"],
        "optional_covers": ["employee_health", "group_pa", "employment_practices", "key_person", "crime_fidelity"],
        "prerequisites": {},
        "eligible_sectors": {"SaaS / Enterprise Software", "Fintech", "Healthtech", "Edtech", "Legaltech", "HRtech", "Gaming / Media / Content"},
        "eligible_stages": ["Seed", "Series A", "Series B+"],
        "description": "Digital-first bundle for startups whose main assets are data, founders, IP, and client contracts.",
        "criticality": "High",
        "covers_criticality": {
            "cyber_liability": {"criticality": "Mandatory", "reason": "For digital startups, breach response and privacy liability are existential risks."},
            "dno_liability": {"criticality": "Mandatory", "reason": "Founder and board personal liability rises after institutional capital."},
            "professional_indemnity": {"criticality": "Mandatory", "reason": "Enterprise clients commonly require E&O/PI for SaaS and service failures."},
            "employee_health": {"criticality": "Recommended", "reason": "Health cover supports talent retention and baseline employee welfare."},
            "group_pa": {"criticality": "Recommended", "reason": "Low-cost accident cover for travel, field work, and employee welfare."},
            "employment_practices": {"criticality": "Optional", "reason": "Add as headcount, POSH, and termination exposure grow."},
            "key_person": {"criticality": "Optional", "reason": "Add when founder concentration or sole technical dependency is high."},
            "crime_fidelity": {"criticality": "Optional", "reason": "Add where employees touch funds, payments, or privileged financial systems."},
        },
    },
    "bharat_sookshma_udyam": {
        "name": "Bharat Sookshma Udyam Suraksha",
        "il_product_name": "ICICI Bharat Sookshma Udyam Suraksha Policy",
        "mandatory_covers": ["property_fire"],
        "optional_covers": ["burglary", "money_insurance", "employees_comp", "public_liability", "machinery_breakdown"],
        "prerequisites": {},
        "eligible_sectors": {"Agritech", "Foodtech / Cloud Kitchen", "D2C / Consumer Brands", "Cleantech / Climatetech", "Logistics / Mobility"},
        "eligible_stages": ["Pre-seed", "Seed"],
        "description": "Entry-level micro-enterprise property policy for startups with modest physical asset values.",
        "criticality": "Medium",
        "covers_criticality": {
            "property_fire": {"criticality": "Mandatory", "reason": "Most affordable entry point for fire and natural peril cover on small assets."},
            "burglary": {"criticality": "Recommended", "reason": "Useful for micro-enterprises with inventory or equipment on site."},
            "money_insurance": {"criticality": "Optional", "reason": "Add where daily cash is handled."},
            "employees_comp": {"criticality": "Optional", "reason": "Add for factory, delivery, warehouse, or field workers."},
            "public_liability": {"criticality": "Optional", "reason": "Add if customers or vendors visit the premises."},
            "machinery_breakdown": {"criticality": "Optional", "reason": "Add where equipment breakdown can stop operations."},
        },
    },
    "deeptech_innovation_bundle": {
        "name": "Deeptech Innovation Bundle",
        "il_product_name": "Property All Risk + Electronic Equipment + PI (Tech) + D&O",
        "mandatory_covers": ["property_all_risk", "electronic_equipment", "professional_indemnity", "dno_liability"],
        "optional_covers": ["cyber_liability", "product_liability", "key_person", "contractors_all_risk", "drone_insurance"],
        "prerequisites": {},
        "eligible_sectors": {"Deeptech / AI / Robotics", "Cleantech / Climatetech", "Healthtech", "Agritech"},
        "eligible_stages": ["Seed", "Series A", "Series B+"],
        "description": "Designed for hardware-software hybrid startups with R&D equipment, pilots, IP, and product liability exposure.",
        "criticality": "High",
        "covers_criticality": {
            "property_all_risk": {"criticality": "Mandatory", "reason": "R&D labs and pilot plants need broader accidental damage cover than basic fire."},
            "electronic_equipment": {"criticality": "Mandatory", "reason": "Servers, GPU clusters, lab electronics, and control systems need affirmative EEI cover."},
            "professional_indemnity": {"criticality": "Mandatory", "reason": "Failed deployments, model drift, and tech service errors can create B2B claims."},
            "dno_liability": {"criticality": "Mandatory", "reason": "Export controls, IP decisions, and investor disclosures create board exposure."},
            "cyber_liability": {"criticality": "Recommended", "reason": "Connected hardware and AI systems raise attack surface."},
            "product_liability": {"criticality": "Recommended", "reason": "Hardware, medical devices, robotics, and consumer devices can injure third parties."},
            "key_person": {"criticality": "Optional", "reason": "Deeptech teams often depend on one or two irreplaceable technical founders."},
            "contractors_all_risk": {"criticality": "Optional", "reason": "Add for physical installation projects and pilot plants."},
            "drone_insurance": {"criticality": "Optional", "reason": "Add for UAV products or commercial drone operations."},
        },
    },
}

SECTOR_FIRE_THRESHOLD = {
    "Logistics / Mobility": {"pct": 83, "reason": "Warehouses, fleet parking yards, and leased logistics sites often carry fire exposure even where assets are not declared."},
    "D2C / Consumer Brands": {"pct": 81, "reason": "Inventory concentration makes fire a company-ending event for early D2C startups."},
    "Foodtech / Cloud Kitchen": {"pct": 92, "reason": "Kitchen fire is a leading SME property loss driver and often precedes liability placement."},
    "Agritech": {"pct": 78, "reason": "Cold-chain, processing, and farm equipment create material property exposure."},
    "Cleantech / Climatetech": {"pct": 85, "reason": "Installed hardware and lender covenants frequently require fire or property all-risk cover."},
}


def _pretty_cover(key: str) -> str:
    return key.replace("_", " ").title()


def match_bundle(sector: str, stage: str, scores: dict, inp) -> dict | None:
    top3 = sorted(scores.values(), reverse=True)[:3]
    score_signal = (sum(top3) / len(top3) / 100) if top3 else 0
    winner = None
    winner_fit = 0

    for bundle in BUNDLE_CATALOG.values():
        fit = 0
        if sector in bundle["eligible_sectors"]:
            fit += 40
        if stage in bundle["eligible_stages"]:
            fit += 30
        relevance = 1.0 if sector in bundle["eligible_sectors"] else 0.55
        fit += int(round(30 * score_signal * relevance))
        if fit > winner_fit:
            winner = bundle
            winner_fit = fit

    if not winner or winner_fit < 40:
        return None

    result = deepcopy(winner)
    result["fit_pct"] = min(100, int(winner_fit))
    result["prerequisite_notes"] = []
    mandatory = result["mandatory_covers"]
    for cover, prereq in result.get("prerequisites", {}).items():
        if cover in mandatory + result.get("optional_covers", []) and prereq not in mandatory:
            mandatory.insert(0, prereq)
            result["prerequisite_notes"].append(
                f"{_pretty_cover(cover)} cover requires {_pretty_cover(prereq)} as a prerequisite - {_pretty_cover(prereq)} has been added automatically."
            )

    note = None
    if sector in SECTOR_FIRE_THRESHOLD and getattr(inp, "hardware_software_split", 0.0) < 0.15:
        fire = SECTOR_FIRE_THRESHOLD[sector]
        note = (
            f"{fire['pct']}% of {sector} startups at your stage carry Fire cover - "
            f"here is why it may apply even without a declared warehouse: {fire['reason']}"
        )
    result["fire_awareness_note"] = note
    return result
