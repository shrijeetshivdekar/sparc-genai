STARTUP_SIZE_BUCKETS = {
    "micro": {"stages": ["Pre-seed", "Seed"], "team_max": 25},
    "small": {"stages": ["Series A"], "team_max": 100},
    "growth": {"stages": ["Series B+"], "team_max": 500},
}

PREMIUM_RANGES = {
    "cyber_liability": {
        "micro": {"min_lakh": 0.5, "max_lakh": 2.5, "basis": "INR 1cr SI, digital-only, basic controls"},
        "small": {"min_lakh": 2.5, "max_lakh": 9.0, "basis": "INR 5cr SI, Series A, DPDPA compliance"},
        "growth": {"min_lakh": 9.0, "max_lakh": 30.0, "basis": "INR 25cr SI, Series B+, SDF-likely"},
    },
    "dno_liability": {
        "micro": {"min_lakh": 0.8, "max_lakh": 2.0, "basis": "INR 2cr SI, seed-stage founders"},
        "small": {"min_lakh": 2.0, "max_lakh": 6.0, "basis": "INR 5cr SI, Series A, institutional investors"},
        "growth": {"min_lakh": 6.0, "max_lakh": 20.0, "basis": "INR 25cr SI, Series B+, listed-company exposure"},
    },
    "professional_indemnity": {
        "micro": {"min_lakh": 0.3, "max_lakh": 1.5, "basis": "INR 1cr SI, small client base"},
        "small": {"min_lakh": 1.5, "max_lakh": 5.0, "basis": "INR 5cr SI, enterprise B2B contracts"},
        "growth": {"min_lakh": 5.0, "max_lakh": 18.0, "basis": "INR 25cr SI, large-enterprise contracts"},
    },
    "employee_health": {
        "micro": {"min_lakh": 0.5, "max_lakh": 2.0, "basis": "INR 3L floater, 10 employees"},
        "small": {"min_lakh": 2.0, "max_lakh": 8.0, "basis": "INR 5L floater, 50 employees"},
        "growth": {"min_lakh": 8.0, "max_lakh": 25.0, "basis": "INR 5L floater, 150 employees"},
    },
    "group_pa": {
        "micro": {"min_lakh": 0.1, "max_lakh": 0.4, "basis": "INR 10L cover, 10 employees"},
        "small": {"min_lakh": 0.4, "max_lakh": 1.5, "basis": "INR 10L cover, 50 employees"},
        "growth": {"min_lakh": 1.5, "max_lakh": 5.0, "basis": "INR 10L cover, 150 employees"},
    },
    "employees_comp": {
        "micro": {"min_lakh": 0.2, "max_lakh": 0.8, "basis": "Small team, limited hazardous ops"},
        "small": {"min_lakh": 0.8, "max_lakh": 2.5, "basis": "Mid-size team, moderate hazardous ops"},
        "growth": {"min_lakh": 2.5, "max_lakh": 8.0, "basis": "Large team, warehouse/logistics ops"},
    },
    "property_fire": {
        "micro": {"min_lakh": 0.3, "max_lakh": 1.2, "basis": "INR 2cr property value"},
        "small": {"min_lakh": 1.2, "max_lakh": 4.0, "basis": "INR 10cr property value"},
        "growth": {"min_lakh": 4.0, "max_lakh": 15.0, "basis": "INR 50cr property value"},
    },
    "business_edge": {
        "micro": {"min_lakh": 0.4, "max_lakh": 1.5, "basis": "Package: fire+burglary+PL, SME"},
        "small": {"min_lakh": 1.5, "max_lakh": 5.0, "basis": "Package: comprehensive, mid-size"},
        "growth": {"min_lakh": 5.0, "max_lakh": 15.0, "basis": "Package: full suite, growth"},
    },
    "public_liability": {
        "micro": {"min_lakh": 0.2, "max_lakh": 0.8, "basis": "INR 1cr limit, small premises"},
        "small": {"min_lakh": 0.8, "max_lakh": 2.5, "basis": "INR 2cr limit, medium operations"},
        "growth": {"min_lakh": 2.5, "max_lakh": 8.0, "basis": "INR 5cr limit, multi-site ops"},
    },
    "product_liability": {
        "micro": {"min_lakh": 0.4, "max_lakh": 1.5, "basis": "INR 2cr SI, single product line"},
        "small": {"min_lakh": 1.5, "max_lakh": 5.0, "basis": "INR 5cr SI, multiple product lines"},
        "growth": {"min_lakh": 5.0, "max_lakh": 18.0, "basis": "INR 20cr SI, large production volume"},
    },
    "marine_transit": {
        "micro": {"min_lakh": 0.2, "max_lakh": 1.0, "basis": "Open cover, INR 50L goods per month"},
        "small": {"min_lakh": 1.0, "max_lakh": 3.5, "basis": "Open cover, INR 2cr goods per month"},
        "growth": {"min_lakh": 3.5, "max_lakh": 12.0, "basis": "Open cover, INR 10cr goods per month"},
    },
    "key_person": {
        "micro": {"min_lakh": 0.5, "max_lakh": 1.5, "basis": "INR 2cr cover, 1 founder"},
        "small": {"min_lakh": 1.5, "max_lakh": 4.0, "basis": "INR 5cr cover, 2 key persons"},
        "growth": {"min_lakh": 4.0, "max_lakh": 12.0, "basis": "INR 15cr cover, leadership team"},
    },
    "employment_practices": {
        "micro": {"min_lakh": 0.3, "max_lakh": 1.0, "basis": "INR 1cr limit, small team"},
        "small": {"min_lakh": 1.0, "max_lakh": 3.5, "basis": "INR 3cr limit, 50 employees"},
        "growth": {"min_lakh": 3.5, "max_lakh": 10.0, "basis": "INR 10cr limit, 150+ employees"},
    },
    "crime_fidelity": {
        "micro": {"min_lakh": 0.3, "max_lakh": 1.0, "basis": "INR 50L coverage, small finance ops"},
        "small": {"min_lakh": 1.0, "max_lakh": 3.5, "basis": "INR 2cr coverage, mid-size finance"},
        "growth": {"min_lakh": 3.5, "max_lakh": 12.0, "basis": "INR 10cr coverage, large payment ops"},
    },
    "gadget_equipment": {
        "micro": {"min_lakh": 0.1, "max_lakh": 0.5, "basis": "10 devices, INR 30L cover"},
        "small": {"min_lakh": 0.5, "max_lakh": 1.5, "basis": "50 devices, INR 1.5cr cover"},
        "growth": {"min_lakh": 1.5, "max_lakh": 5.0, "basis": "150 devices, INR 5cr cover"},
    },
    "clinical_trials": {
        "micro": {"min_lakh": 1.0, "max_lakh": 4.0, "basis": "Phase 1 trial, INR 5cr liability"},
        "small": {"min_lakh": 4.0, "max_lakh": 12.0, "basis": "Phase 2 trial, INR 20cr liability"},
        "growth": {"min_lakh": 12.0, "max_lakh": 40.0, "basis": "Phase 3 trial, INR 100cr liability"},
    },
    "comprehensive_general_liability": {
        "micro": {"min_lakh": 0.3, "max_lakh": 1.2, "basis": "INR 1cr limit, small B2B"},
        "small": {"min_lakh": 1.2, "max_lakh": 4.0, "basis": "INR 3cr limit, enterprise contracts"},
        "growth": {"min_lakh": 4.0, "max_lakh": 12.0, "basis": "INR 10cr limit, large-enterprise"},
    },
    "business_interruption": {
        "micro": {"min_lakh": 0.3, "max_lakh": 1.0, "basis": "INR 50L BI cover, 90 days indemnity"},
        "small": {"min_lakh": 1.0, "max_lakh": 4.0, "basis": "INR 2cr BI cover, 180 days indemnity"},
        "growth": {"min_lakh": 4.0, "max_lakh": 15.0, "basis": "INR 10cr BI cover, 365 days indemnity"},
    },
    "property_all_risk": {
        "micro": {"min_lakh": 0.5, "max_lakh": 2.0, "basis": "INR 3cr property, lab/equipment"},
        "small": {"min_lakh": 2.0, "max_lakh": 7.0, "basis": "INR 15cr property, pilot plant"},
        "growth": {"min_lakh": 7.0, "max_lakh": 25.0, "basis": "INR 75cr property, full facility"},
    },
    "electronic_equipment": {
        "micro": {"min_lakh": 0.3, "max_lakh": 1.2, "basis": "INR 1cr EEI SI, GPU/servers"},
        "small": {"min_lakh": 1.2, "max_lakh": 4.0, "basis": "INR 5cr EEI SI, data centre"},
        "growth": {"min_lakh": 4.0, "max_lakh": 15.0, "basis": "INR 25cr EEI SI, large infra"},
    },
    "machinery_breakdown": {
        "micro": {"min_lakh": 0.2, "max_lakh": 0.8, "basis": "INR 1cr machinery, small plant"},
        "small": {"min_lakh": 0.8, "max_lakh": 3.0, "basis": "INR 5cr machinery, mid plant"},
        "growth": {"min_lakh": 3.0, "max_lakh": 10.0, "basis": "INR 25cr machinery, large plant"},
    },
    "motor_fleet": {
        "micro": {"min_lakh": 0.5, "max_lakh": 2.0, "basis": "5-vehicle fleet"},
        "small": {"min_lakh": 2.0, "max_lakh": 7.0, "basis": "20-vehicle fleet"},
        "growth": {"min_lakh": 7.0, "max_lakh": 25.0, "basis": "100-vehicle fleet"},
    },
    "trade_credit": {
        "micro": {"min_lakh": 0.4, "max_lakh": 1.5, "basis": "INR 2cr receivables"},
        "small": {"min_lakh": 1.5, "max_lakh": 5.0, "basis": "INR 10cr receivables"},
        "growth": {"min_lakh": 5.0, "max_lakh": 18.0, "basis": "INR 50cr receivables"},
    },
    "money_insurance": {
        "micro": {"min_lakh": 0.1, "max_lakh": 0.4, "basis": "INR 5L cash limit"},
        "small": {"min_lakh": 0.4, "max_lakh": 1.2, "basis": "INR 20L cash limit"},
        "growth": {"min_lakh": 1.2, "max_lakh": 4.0, "basis": "INR 1cr cash limit"},
    },
    "contractors_all_risk": {
        "micro": {"min_lakh": 0.5, "max_lakh": 2.0, "basis": "INR 2cr project value"},
        "small": {"min_lakh": 2.0, "max_lakh": 8.0, "basis": "INR 10cr project value"},
        "growth": {"min_lakh": 8.0, "max_lakh": 30.0, "basis": "INR 50cr project value"},
    },
    "drone_insurance": {
        "micro": {"min_lakh": 0.3, "max_lakh": 1.0, "basis": "2 drones, INR 50L hull"},
        "small": {"min_lakh": 1.0, "max_lakh": 3.5, "basis": "10 drones, INR 2cr hull"},
        "growth": {"min_lakh": 3.5, "max_lakh": 12.0, "basis": "50 drones, INR 10cr hull"},
    },
    "msme_suraksha": {
        "micro": {"min_lakh": 0.3, "max_lakh": 1.0, "basis": "INR 50L insurable value, all perils"},
        "small": {"min_lakh": 1.0, "max_lakh": 3.5, "basis": "INR 2cr insurable value"},
        "growth": {"min_lakh": 3.5, "max_lakh": 10.0, "basis": "INR 10cr insurable value"},
    },
    "enterprise_secure": {
        "micro": {"min_lakh": 0.8, "max_lakh": 2.5, "basis": "Package: property+BI+PL"},
        "small": {"min_lakh": 2.5, "max_lakh": 8.0, "basis": "Package: full suite, Series A"},
        "growth": {"min_lakh": 8.0, "max_lakh": 25.0, "basis": "Package: enterprise suite"},
    },
}

PREMIUM_FOOTNOTE = (
    "Indicative estimates only. Actual premium is subject to underwriting, SI selection, "
    "controls, and claims history. Sources: IRDAI Annual Report 2023-24, GIC Re pricing "
    "circulars, and industry broker benchmarks Q1 2026."
)


def get_size_bucket(funding_stage: str, team_size: int) -> str:
    if funding_stage in STARTUP_SIZE_BUCKETS["micro"]["stages"] and team_size <= 25:
        return "micro"
    if funding_stage in STARTUP_SIZE_BUCKETS["growth"]["stages"]:
        return "growth"
    return "small"


def estimate_premium(product_key: str, size_bucket: str) -> dict | None:
    return PREMIUM_RANGES.get(product_key, {}).get(size_bucket)


def format_premium(min_lakh: float, max_lakh: float) -> str:
    return f"INR {min_lakh:.1f} - {max_lakh:.1f} lakhs"
