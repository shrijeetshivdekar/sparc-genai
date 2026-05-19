"""
Deterministic premium pricing engine for SPARC.

The engine deliberately keeps premium math outside GenAI. It accepts the
recommended bundle/output profile, normalises covers, infers missing sum insured
values from the intake profile, and returns an auditable quote object.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from quote_prefill import suggest_quote_inputs
from risk_appetite import get_appetite


CRORE_INR = 10_000_000
GST_RATE = 0.18
ENGINE_VERSION = "pricing-2026.05.r1"

# Maximum multiplier any cover's combined loading can reach.
# Prevents pathological compounding (risk×stage×sector×climate×claims can
# theoretically reach 7x; 4x is the auditable ceiling).
MAX_COMBINED_LOADING = 4.0
MAX_RISK_LOADING = 1.5

# Cyber enterprise accounts should not reuse SME/startup base-rate math.
# For SI > 25 Cr, quote a marketable technical ROL band and push uncertainty
# into referral flags, retentions, and control questionnaires instead of
# compounding multiplicative penalties into a non-bindable price.
CYBER_ENTERPRISE_SI_THRESHOLD_CR = 25.0
CYBER_ENTERPRISE_MIN_ROL = 0.003
CYBER_ENTERPRISE_MAX_ROL = 0.008
ENTERPRISE_LIABILITY_SI_THRESHOLD_CR = 25.0
ENTERPRISE_LIABILITY_ROL_BANDS = {
    "cyber_liability": (0.0030, 0.0080),
    "dno_liability": (0.0010, 0.0025),
    "professional_indemnity": (0.0010, 0.0020),
    "financial_services_pi": (0.0010, 0.0020),
    "healthcare_pi": (0.0010, 0.0020),
    "comprehensive_general_liability": (0.0005, 0.0010),
    "public_liability": (0.0005, 0.0010),
    "crime_fidelity": (0.0005, 0.0015),
    "employment_practices": (0.0005, 0.0015),
}

# Sector-specific rate multipliers applied on top of COVER_SPECS base rates.
# Rationale: a flat base rate is calibrated to the median startup; these adjustments
# correct for systematic over/under-pricing in sectors where exposure materially differs.
# Keys are canonical cover IDs; sector strings match profile["sector"] values.
SECTOR_RATE_ADJUSTMENTS: Dict[str, Dict[str, float]] = {
    "cyber_liability": {
        # Fintech/Healthtech: high data density, regulatory scrutiny, incident response cost
        "Fintech": 1.30,
        "Healthtech": 1.20,
        # D2C/Logistics/Agri: consumer purchase data only, limited PII depth
        "D2C / Consumer Brands": 0.45,
        "Logistics / Mobility": 0.55,
        "Agritech / Foodtech": 0.50,
        "Gaming / Media / Content": 0.70,
        "Deeptech / AI / Robotics": 0.90,
    },
    "professional_indemnity": {
        # Physical-product companies rarely face PI/E&O claims — PI is a services-sector cover
        "D2C / Consumer Brands": 0.40,
        "Logistics / Mobility": 0.50,
        "Agritech / Foodtech": 0.50,
        # High for advice/code/data-intensive sectors
        "Fintech": 1.25,
        "Healthtech": 1.20,
        "SaaS / Enterprise Software": 1.15,
        "Edtech / HRtech": 1.10,
    },
    "marine_transit": {
        # Domestic-only cargo: standard inland rate ~0.10–0.20 L/Cr
        # Export-heavy companies stay at base; multipliers below assume domestic-first profiles
        "D2C / Consumer Brands": 0.45,   # domestic retail goods, well-packed, standard risks
        "Agritech / Foodtech": 0.55,     # domestic perishable; slightly higher spoilage risk
        "Logistics / Mobility": 0.60,    # fleet-based; moderate
        "Fintech": 0.25,                 # minimal physical goods
        "SaaS / Enterprise Software": 0.25,
        "Healthtech": 0.70,              # pharma/device transit; moderate
    },
    "product_liability": {
        # Higher for consumer hardware/food where recall + injury risk is real
        "D2C / Consumer Brands": 1.15,
        "Agritech / Foodtech": 1.20,
        "Healthtech": 1.30,
        # Software companies: product liability rarely applies
        "SaaS / Enterprise Software": 0.40,
        "Fintech": 0.40,
        "Edtech / HRtech": 0.50,
    },
}

# Sector-specific cyber SI caps (in Cr) — overrides stage-only inference.
# Prevents data-light sectors from inheriting fintech-grade limits.
SECTOR_CYBER_SI_CAP_CR: Dict[str, float] = {
    "D2C / Consumer Brands": 8.0,
    "Logistics / Mobility": 8.0,
    "Agritech / Foodtech": 6.0,
    "Gaming / Media / Content": 10.0,
    "Deeptech / AI / Robotics": 12.0,
    "Fintech": 50.0,
    "Healthtech": 30.0,
    "SaaS / Enterprise Software": 25.0,
    "Edtech / HRtech": 15.0,
}

BAD_RISK_REASONS_SHORT = {
    "cyber_liability": {
        "Fintech": "High claim frequency; elevated deductible likely required.",
        "Gaming / Media / Content": "Ransomware/extortion exposure disproportionately high.",
    },
    "product_liability": {
        "SaaS / Enterprise Software": "Software failures are PI/E&O claims, not product liability.",
        "Fintech": "Financial service failures handled through PI/E&O, not product liability.",
    },
    "marine_transit": {
        "Fintech": "No physical goods; no cargo exposure.",
        "SaaS / Enterprise Software": "Digital-only; no cargo exposure.",
    },
}


COVER_ALIASES = {
    "CYBER": "cyber_liability",
    "cyber": "cyber_liability",
    "cyber_liability": "cyber_liability",
    "D_AND_O": "dno_liability",
    "d_and_o": "dno_liability",
    "dno_liability": "dno_liability",
    "PI_TECH_EO": "professional_indemnity",
    "pi_tech_eo": "professional_indemnity",
    "professional_indemnity": "professional_indemnity",
    "CGL_I_ELITE": "comprehensive_general_liability",
    "cgl_i_elite": "comprehensive_general_liability",
    "comprehensive_general_liability": "comprehensive_general_liability",
    "PUBLIC_LIABILITY": "public_liability",
    "public_liability": "public_liability",
    "PRODUCT_LIABILITY": "product_liability",
    "product_liability": "product_liability",
    "EMPLOYERS_COMP": "employees_comp",
    "employees_comp": "employees_comp",
    "GROUP_HEALTH": "employee_health",
    "group_health": "employee_health",
    "employee_health": "employee_health",
    "GROUP_PA": "group_pa",
    "group_pa": "group_pa",
    "BHARAT_SOOKSHMA": "property_fire",
    "bharat_sookshma": "property_fire",
    "property_fire": "property_fire",
    "PROPERTY_FIRE": "property_fire",
    "BUSINESS_INTERRUPTION": "business_interruption",
    "business_interruption": "business_interruption",
    "PROPERTY_ALL_RISK": "property_all_risk",
    "property_all_risk": "property_all_risk",
    "ELECTRONIC_EQUIPMENT": "electronic_equipment",
    "electronic_equipment": "electronic_equipment",
    "MACHINERY_BREAKDOWN": "machinery_breakdown",
    "ENGINEERING_CAR_EAR_CPM_MBD_EEI": "engineering",
    "engineering": "engineering",
    "contractors_all_risk": "engineering",
    "CONTRACTORS_ALL_RISK": "engineering",
    "SURETY": "surety",
    "surety": "surety",
    "MARINE_CARGO": "marine_transit",
    "marine_cargo": "marine_transit",
    "marine_transit": "marine_transit",
    "TRADE_CREDIT": "trade_credit",
    "trade_credit": "trade_credit",
    "PRAKRITIK_PARAMETRIC": "parametric",
    "prakritik_parametric": "parametric",
    "parametric": "parametric",
    "burglary": "burglary",
    "money_insurance": "money_insurance",
    "CRIME_FIDELITY": "crime_fidelity",
    "crime_fidelity": "crime_fidelity",
    "Drone_RPAS": "drone_insurance",
    "drone_rpas": "drone_insurance",
    "drone_insurance": "drone_insurance",
    "employment_practices": "employment_practices",
    "EMPLOYMENT_PRACTICES": "employment_practices",
    "epl": "employment_practices",
    "EPL": "employment_practices",
    "epli": "employment_practices",
    "EPLI": "employment_practices",
    "machinery_breakdown": "machinery_breakdown",
    "MOTOR_FLEET": "motor_fleet",
    "motor_fleet": "motor_fleet",
    "commercial_motor_fleet": "motor_fleet",
    "HEALTHCARE_PI": "healthcare_pi",
    "healthcare_pi": "healthcare_pi",
    "FINANCIAL_SERVICES_PI": "financial_services_pi",
    "financial_services_pi": "financial_services_pi",
    "PAYMENT_PROTECTION": "payment_protection",
    "payment_protection": "payment_protection",
    "PRODUCT_RECALL": "product_recall",
    "TOTAL_RECALL": "product_recall",
    "product_recall": "product_recall",
    "EVENT_PRODUCTION": "event_production",
    "event_production": "event_production",
    "ENTERTAINMENT_PRODUCTION": "event_production",
    "GROUP_CRITI_SHIELD": "group_criti_shield",
    "group_criti_shield": "group_criti_shield",
    "criti_shield": "group_criti_shield",
    "GROUP_HOSPISHIELD": "group_hospishield",
    "group_hospishield": "group_hospishield",
    "hospishield": "group_hospishield",
    "BHARAT_LAGHU": "property_fire",
    "bharat_laghu": "property_fire",
}


@dataclass(frozen=True)
class CoverSpec:
    label: str
    exposure_field: str
    rate_lakh_per_cr: float
    min_lakh: float
    risk_keys: tuple[str, ...]
    pricing_unit: str = "sum_insured"


@dataclass(frozen=True)
class PricingRule:
    pricing_basis: str
    max_benchmark_exposure_cr: Optional[float] = None
    max_precise_exposure_cr: Optional[float] = None
    underwriter_exposure_cr: Optional[float] = None
    calibration_basis: tuple[str, ...] = ("heuristic_rate_curve", "proposal_form_proxy")


# Base rates below are calibrated to Indian SME/startup market mid-points as of Q1 2026.
# Sources: Mitigata Cyber Insurance India 2026; NivaaBupa/Pazcare group health data;
# Pazago marine cargo rates; Allianz Trade credit data; Riskbirbal CAR/EAR guide;
# IRDAI Surety Guidelines 2022; BusinessStandard fire premium analysis Dec 2024;
# WTIB EEI tariff; HDFC ERGO / Liberty General machinery breakdown quotes.
# All covers are non-tariff (market-based) post IRDAI de-notification Apr 2024,
# except Employees Compensation (IIB-based) and Electronic Equipment (ex-tariff reference).
COVER_SPECS: Dict[str, CoverSpec] = {
    # rate 1.75 → effective ~2.0% of limit at mid-loading; market 2–2.5L/Cr (Mitigata 2026)
    "cyber_liability": CoverSpec(
        "Cyber Liability", "cyber_limit_cr", 1.75, 1.50,
        ("Cyber Technical Risk", "Data Privacy Risk", "Regulatory Compliance Risk"),
    ),
    # rate 0.75 → effective ~0.85% of limit; market 0.5–1.5% (Liberty/IFFCO Tokio); floor raised to 2.00L (institutional round trigger)
    "dno_liability": CoverSpec(
        "Directors and Officers Liability", "dno_limit_cr", 0.75, 2.00,
        ("Governance & Fraud Risk", "Regulatory Compliance Risk", "Reputation Risk"),
    ),
    # rate 0.70 → effective ~0.80% of limit; market 0.6–1.2% (IRDAI PI Guidelines 2021)
    "professional_indemnity": CoverSpec(
        "Professional Indemnity / Tech E&O", "pi_limit_cr", 0.70, 1.00,
        ("Liability Risk", "IP Infringement Risk", "Reputation Risk"),
    ),
    # rate 0.40 → effective ~0.45% of limit; HDFC ERGO CGL market range
    "comprehensive_general_liability": CoverSpec(
        "Comprehensive General Liability", "public_liability_limit_cr", 0.40, 0.55,
        ("Liability Risk", "Reputation Risk", "Regulatory Compliance Risk"),
    ),
    # rate 0.30 → effective ~0.34% of limit; Bajaj Allianz PL range
    "public_liability": CoverSpec(
        "Public Liability", "public_liability_limit_cr", 0.30, 0.35,
        ("Liability Risk", "Property Risk"),
    ),
    # rate 0.52 → effective ~0.59% of limit; market for D2C/Healthtech sectors
    "product_liability": CoverSpec(
        "Product Liability", "product_liability_limit_cr", 0.52, 0.60,
        ("Liability Risk", "Reputation Risk", "Regulatory Compliance Risk"),
    ),
    # rate 0.50 → effective ~0.57% of SI; IRDAI de-tariff Apr 2024 drove market rates up 60–80% (BusinessStandard Dec 2024)
    "property_fire": CoverSpec(
        "Property Fire", "property_sum_insured_cr", 0.50, 0.45,
        ("Property Risk", "ESG & Climate Risk"),
    ),
    # rate 0.52 → effective ~0.59% of SI; ~1.5x fire rate per market convention
    "property_all_risk": CoverSpec(
        "Property All Risk", "property_sum_insured_cr", 0.52, 0.55,
        ("Property Risk", "ESG & Climate Risk", "Liability Risk"),
    ),
    # rate 0.22 → effective ~0.25% of BI SI; Trust Risk Control Jan 2025 standardisation
    "business_interruption": CoverSpec(
        "Business Interruption", "gross_profit_si_cr", 0.22, 0.25,
        ("Property Risk", "Liability Risk", "Reputation Risk"),
    ),
    # rate 0.18 → effective ~0.20% of stock; market 0.18–0.25%
    "burglary": CoverSpec(
        "Burglary", "stock_sum_insured_cr", 0.18, 0.15,
        ("Property Risk", "Gig & Labour Risk"),
    ),
    # rate 0.80 → effective ~0.91% of equipment value; ex-tariff 1.25% (WTIB); market 0.8–1.2%
    "electronic_equipment": CoverSpec(
        "Electronic Equipment", "equipment_sum_insured_cr", 0.80, 0.50,
        ("Property Risk", "Cyber Technical Risk"),
    ),
    # rate 0.55 → effective ~0.62% of plant value; HDFC ERGO / Liberty General range
    "machinery_breakdown": CoverSpec(
        "Machinery Breakdown", "equipment_sum_insured_cr", 0.55, 0.40,
        ("Property Risk", "ESG & Climate Risk"),
    ),
    # rate 0.40 → effective ~0.45% of payroll; IRDAI WC office class ~0.5%
    "employees_comp": CoverSpec(
        "Employees Compensation", "payroll_cr", 0.40, 0.30,
        ("Gig & Labour Risk", "Liability Risk", "Regulatory Compliance Risk"),
    ),
    # rate 0.13 lakh/employee → effective ~₹14,700/emp at mid-loading; NivaaBupa/Pazcare ₹10–25K
    "employee_health": CoverSpec(
        "Group Health", "employee_count", 0.13, 1.20,
        ("Key Person Risk", "Gig & Labour Risk"),
        pricing_unit="per_employee",
    ),
    # rate 0.09 lakh/employee → effective ~₹10,200/emp at mid-loading; Bajaj Finserv ₹8–15K
    "group_pa": CoverSpec(
        "Group Personal Accident", "employee_count", 0.09, 0.50,
        ("Gig & Labour Risk", "Key Person Risk"),
        pricing_unit="per_employee",
    ),
    # rate 0.40 → effective ~0.45% of cargo turnover; Pazago domestic marine 0.3–0.8%
    "marine_transit": CoverSpec(
        "Marine Cargo", "cargo_turnover_cr", 0.40, 0.35,
        ("Geopolitical Risk", "Property Risk", "Reputation Risk"),
    ),
    # rate 0.40 → effective ~0.45% of receivables; Allianz Trade 0.1–0.4% of sales
    "trade_credit": CoverSpec(
        "Trade Credit", "receivables_on_credit_cr", 0.40, 0.45,
        ("Governance & Fraud Risk", "Geopolitical Risk", "Reputation Risk"),
    ),
    # rate 0.22 → effective ~0.25% of project value; Riskbirbal CAR/EAR 0.1–0.5%
    "engineering": CoverSpec(
        "Engineering CAR / EAR", "project_value_cr", 0.22, 0.55,
        ("Property Risk", "Liability Risk", "ESG & Climate Risk"),
    ),
    # rate 0.45 → effective ~0.51% of bond value; IRDAI Surety Guidelines 2022
    "surety": CoverSpec(
        "Surety", "project_value_cr", 0.45, 0.65,
        ("Governance & Fraud Risk", "Regulatory Compliance Risk"),
    ),
    # rate 0.22; emerging product in India — limited market data
    "parametric": CoverSpec(
        "Climate Parametric", "weather_exposed_si_cr", 0.22, 0.35,
        ("ESG & Climate Risk", "Property Risk", "Geopolitical Risk"),
    ),
    # rate 0.35; market estimate — no change
    "money_insurance": CoverSpec(
        "Money Insurance", "cash_limit_cr", 0.35, 0.08,
        ("Governance & Fraud Risk", "Property Risk"),
    ),
    # rate 0.35; market estimate — no change
    "crime_fidelity": CoverSpec(
        "Crime / Fidelity", "crime_limit_cr", 0.35, 0.30,
        ("Governance & Fraud Risk", "Cyber Technical Risk"),
    ),
    # rate 0.42; limited public market data — no change
    "drone_insurance": CoverSpec(
        "Drone RPAS", "drone_hull_si_cr", 0.42, 0.30,
        ("Liability Risk", "Property Risk", "Regulatory Compliance Risk"),
    ),
    "motor_fleet": CoverSpec(
        "Commercial Motor Fleet", "fleet_count", 0.18, 0.50,
        ("Liability Risk", "Property Risk", "Gig & Labour Risk"),
        pricing_unit="per_vehicle",
    ),
    "healthcare_pi": CoverSpec(
        "Healthcare / Medical Professional Liability", "healthcare_pi_limit_cr", 0.95, 1.25,
        ("Liability Risk", "Regulatory Compliance Risk", "Reputation Risk"),
    ),
    "financial_services_pi": CoverSpec(
        "Financial Services Professional Indemnity", "fi_pi_limit_cr", 1.05, 1.50,
        ("Liability Risk", "Governance & Fraud Risk", "Regulatory Compliance Risk"),
    ),
    "payment_protection": CoverSpec(
        "Payment / Card Protection", "payment_protection_limit_cr", 0.65, 0.80,
        ("Cyber Technical Risk", "Governance & Fraud Risk", "Data Privacy Risk"),
    ),
    "product_recall": CoverSpec(
        "Product Recall / Contamination", "recall_limit_cr", 0.85, 1.00,
        ("Liability Risk", "Reputation Risk", "Regulatory Compliance Risk"),
    ),
    "event_production": CoverSpec(
        "Entertainment Production Package", "production_budget_cr", 0.60, 0.60,
        ("Liability Risk", "Reputation Risk", "Property Risk"),
    ),
    # rate 0.45 → effective ~0.51% of limit; emerging EPLI market in India (Marsh/AON EPL data 2025)
    "employment_practices": CoverSpec(
        "Employment Practices Liability", "employment_practices_limit_cr", 0.45, 1.00,
        ("Gig & Labour Risk", "Governance & Fraud Risk", "Reputation Risk"),
    ),
    # rate 0.05 lakh/employee → effective ~₹5,600/emp at mid-loading; critical illness rider market India 2025
    "group_criti_shield": CoverSpec(
        "Group Critical Illness Shield", "employee_count", 0.05, 0.30,
        ("Key Person Risk", "Gig & Labour Risk"),
        pricing_unit="per_employee",
    ),
    # rate 0.06 lakh/employee → effective ~₹6,750/emp at mid-loading; hospital cash rider market India 2025
    "group_hospishield": CoverSpec(
        "Group HospiShield (Hospital Daily Cash)", "employee_count", 0.06, 0.40,
        ("Key Person Risk", "Gig & Labour Risk"),
        pricing_unit="per_employee",
    ),
}

PRICING_RULES: Dict[str, PricingRule] = {
    "cyber_liability": PricingRule("limit_based_liability", 10.0, 25.0, 50.0, ("confirmed_customer_inputs", "heuristic_rate_curve", "proposal_form_proxy")),
    "dno_liability": PricingRule("limit_based_liability", 10.0, 15.0, 25.0),
    "professional_indemnity": PricingRule("limit_based_liability", 10.0, 25.0, 25.0),
    "financial_services_pi": PricingRule("limit_based_liability", 10.0, 25.0, 25.0),
    "healthcare_pi": PricingRule("limit_based_liability", 10.0, 15.0, 25.0),
    "comprehensive_general_liability": PricingRule("premises_operations_liability", 10.0, 15.0, 25.0),
    "public_liability": PricingRule("premises_operations_liability", 10.0, 15.0, 25.0),
    "product_liability": PricingRule("turnover_plus_limit_liability", 10.0, 15.0, 25.0),
    "crime_fidelity": PricingRule("fidelity_limit_with_controls", 10.0, 15.0, 25.0),
    "employment_practices": PricingRule("headcount_limit_liability", 10.0, 15.0, 25.0),
    "employee_health": PricingRule("employee_benefit_census", None, None, None, ("proposal_form_proxy", "heuristic_rate_curve")),
    "group_pa": PricingRule("employee_benefit_census", None, None, None, ("proposal_form_proxy", "heuristic_rate_curve")),
    "group_criti_shield": PricingRule("employee_benefit_census", None, None, None, ("proposal_form_proxy", "heuristic_rate_curve")),
    "group_hospishield": PricingRule("employee_benefit_census", None, None, None, ("proposal_form_proxy", "heuristic_rate_curve")),
    "property_fire": PricingRule("asset_value_property", 50.0, 50.0, 75.0, ("public_benchmark", "heuristic_rate_curve", "proposal_form_proxy")),
    "property_all_risk": PricingRule("asset_value_property", 50.0, 50.0, 75.0, ("public_benchmark", "heuristic_rate_curve", "proposal_form_proxy")),
    "business_interruption": PricingRule("asset_value_property", 25.0, 50.0, 75.0),
    "electronic_equipment": PricingRule("asset_value_property", 25.0, 50.0, 75.0),
    "machinery_breakdown": PricingRule("asset_value_property", 25.0, 50.0, 75.0),
    "engineering": PricingRule("project_value_engineering", 10.0, 25.0, 50.0),
    "surety": PricingRule("contract_value_referral", 0.0, 0.0, 0.0, ("proposal_form_proxy",)),
    "marine_transit": PricingRule("annual_transit_turnover", 25.0, 50.0, 100.0),
    "trade_credit": PricingRule("credit_turnover_or_receivables", 25.0, 50.0, 100.0),
}

QUOTE_CONFIDENCE_LABELS = {
    "technically_priced": "Technically priced",
    "directional_only": "Directional only",
    "underwriter_required": "Underwriter validation required",
}

INPUT_FIELD_LABELS = {
    "property_sum_insured_cr": ("Property sum insured", "INR Cr", "Building, fitout, stock, and other insurable property value."),
    "total_insurable_asset_value_cr": ("Total insurable asset value", "INR Cr", "Total building, fitout, stock, equipment, and other insured property value."),
    "asset_value_inr": ("Property asset value", "INR", "Alternative to property SI if available in rupees."),
    "stock_sum_insured_cr": ("Stock sum insured", "INR Cr", "Inventory value to insure against fire/theft."),
    "equipment_sum_insured_cr": ("Equipment sum insured", "INR Cr", "Electronics, machinery, lab, server, or plant equipment value."),
    "gross_profit_si_cr": ("Gross profit / BI sum insured", "INR Cr", "Gross profit or standing charges basis for business interruption."),
    "cyber_limit_cr": ("Cyber limit", "INR Cr", "Cyber liability limit requested."),
    "dno_limit_cr": ("D&O limit", "INR Cr", "Directors and officers liability limit requested."),
    "pi_limit_cr": ("Professional indemnity limit", "INR Cr", "E&O / PI limit requested."),
    "public_liability_limit_cr": ("Public liability limit", "INR Cr", "Third-party bodily injury/property damage limit."),
    "product_liability_limit_cr": ("Product liability limit", "INR Cr", "Physical product liability limit."),
    "payroll_cr": ("Annual payroll", "INR Cr", "Annual payroll/wage roll for employees compensation."),
    "cargo_annual_turnover_cr": ("Annual cargo turnover", "INR Cr", "Annual value of goods moved domestically or internationally."),
    "receivables_on_credit_cr": ("Receivables on credit", "INR Cr", "Outstanding B2B receivables under credit terms."),
    "project_value_cr": ("Project value", "INR Cr", "Contract/project value for engineering or surety covers."),
    "weather_exposed_si_cr": ("Weather-exposed value", "INR Cr", "Assets or revenue exposed to parametric weather events."),
    "cash_limit_cr": ("Cash limit", "INR Cr", "Cash-in-safe/transit limit."),
    "crime_limit_cr": ("Crime / fidelity limit", "INR Cr", "Employee dishonesty/social engineering limit."),
    "drone_hull_si_cr": ("Drone hull SI", "INR Cr", "Drone hull/equipment value."),
    "fleet_count": ("Fleet count", "vehicles", "Owned or operated commercial vehicles, delivery two-wheelers, trailers, or field-service vehicles."),
    "healthcare_pi_limit_cr": ("Healthcare PI limit", "INR Cr", "Medical professional liability limit requested."),
    "fi_pi_limit_cr": ("FI PI limit", "INR Cr", "Financial institution professional indemnity limit requested."),
    "payment_protection_limit_cr": ("Payment protection limit", "INR Cr", "Card/payment protection or unauthorised transaction limit."),
    "recall_limit_cr": ("Recall / contamination limit", "INR Cr", "Product recall, contamination, and brand rehabilitation limit."),
    "production_budget_cr": ("Production budget", "INR Cr", "Insurable event/production budget or equipment-at-risk value."),
    "employment_practices_limit_cr": ("EPL limit", "INR Cr", "Employment practices liability limit - wrongful termination, harassment, discrimination claims."),
    "employee_count": ("Employee count", "count", "Employees to be covered."),
    "team_size": ("Team size", "count", "Existing intake team size used for employee covers."),
    "annual_revenue_cr": ("Annual revenue", "INR Cr", "Annual revenue / ARR — scales Cyber and PI/Tech E&O premium."),
    "data_records_lakhs": ("Data records", "lakhs", "Customer/user records held in lakhs (1 lakh = 100,000). Drives Cyber exposure."),
    "claims_last_3_years": ("Prior claims", "yes/no", "Any insurance claims filed in the last 3 years? Adds a loading if yes."),
}


REQUIRED_INPUTS_BY_COVER = {
    "cyber_liability": (
        ("cyber_limit_cr",),
        ("annual_revenue_cr", "revenue_cr"),
        ("data_records_lakhs",),
        ("claims_last_3_years",),
    ),
    "dno_liability": (
        ("dno_limit_cr",),
        ("claims_last_3_years",),
    ),
    "professional_indemnity": (
        ("pi_limit_cr", "professional_indemnity_limit_cr"),
        ("annual_revenue_cr", "revenue_cr"),
        ("claims_last_3_years",),
    ),
    "crime_fidelity": (
        ("crime_limit_cr",),
        ("claims_last_3_years",),
    ),
    "comprehensive_general_liability": (("public_liability_limit_cr",),),
    "public_liability": (("public_liability_limit_cr",),),
    "product_liability": (("product_liability_limit_cr",),),
    "property_fire": (("property_sum_insured_cr", "total_insurable_asset_value_cr", "asset_value_inr"),),
    "property_all_risk": (("property_sum_insured_cr", "total_insurable_asset_value_cr", "asset_value_inr"),),
    "business_interruption": (("gross_profit_si_cr", "gross_profit_cr"),),
    "burglary": (("stock_sum_insured_cr",),),
    "electronic_equipment": (("equipment_sum_insured_cr",),),
    "machinery_breakdown": (("equipment_sum_insured_cr",),),
    "employees_comp": (("payroll_cr",),),
    "employee_health": (("employee_count", "team_size", "headcount_total"),),
    "group_pa": (("employee_count", "team_size", "headcount_total"),),
    "marine_transit": (("cargo_annual_turnover_cr", "cargo_turnover_cr"),),
    "trade_credit": (("receivables_on_credit_cr",),),
    "engineering": (("project_value_cr", "capex_project_value_cr"),),
    "surety": (("project_value_cr", "capex_project_value_cr"),),
    "parametric": (("weather_exposed_si_cr",),),
    "money_insurance": (("cash_limit_cr",),),
    "drone_insurance": (("drone_hull_si_cr",),),
    "motor_fleet": (("fleet_count",),),
    "healthcare_pi": (("healthcare_pi_limit_cr",), ("claims_last_3_years",)),
    "financial_services_pi": (("fi_pi_limit_cr",), ("annual_revenue_cr", "revenue_cr"), ("claims_last_3_years",)),
    "payment_protection": (("payment_protection_limit_cr",), ("annual_revenue_cr", "revenue_cr"), ("claims_last_3_years",)),
    "product_recall": (("recall_limit_cr",), ("annual_revenue_cr", "revenue_cr"), ("claims_last_3_years",)),
    "event_production": (("production_budget_cr",), ("claims_last_3_years",)),
    "employment_practices": (("employment_practices_limit_cr", "epli_limit_cr"), ("claims_last_3_years",)),
    "group_criti_shield": (("employee_count", "team_size", "headcount_total"),),
    "group_hospishield": (("employee_count", "team_size", "headcount_total"),),
}


def _float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _positive(value: Any) -> Optional[float]:
    number = _float(value)
    return number if number > 0 else None


def _asset_value_in_cr(profile: Dict[str, Any]) -> Optional[float]:
    explicit = _explicit_cr(profile, "total_insurable_asset_value_cr", "property_sum_insured_cr")
    if explicit is not None:
        return explicit
    for key in ("asset_value_inr", "total_asset_value_inr", "sum_insured_inr"):
        value = _positive(profile.get(key))
        if value is not None:
            return value / CRORE_INR
    return None


def _explicit_cr(profile: Dict[str, Any], *keys: str) -> Optional[float]:
    for key in keys:
        value = _positive(profile.get(key))
        if value is not None:
            return value
    return None


def _stage(profile: Dict[str, Any]) -> str:
    return str(profile.get("funding_stage") or profile.get("stage") or "Seed")


def _team_size(profile: Dict[str, Any]) -> int:
    return max(1, int(_float(profile.get("team_size") or profile.get("headcount_total"), 10)))


def _has_any(items: Iterable[str], *needles: str) -> bool:
    item_set = set(items or [])
    return any(needle in item_set for needle in needles)


def _infer_property_si(profile: Dict[str, Any]) -> tuple[float, List[str]]:
    explicit = _explicit_cr(profile, "property_sum_insured_cr", "total_insurable_asset_value_cr")
    asset_inr = _asset_value_in_cr(profile)
    if explicit is not None:
        return explicit, ["Property SI taken from property_sum_insured_cr."]
    if asset_inr is not None:
        return asset_inr, ["Property SI taken from asset_value_inr."]

    stage_base = {"Pre-seed": 0.50, "Seed": 1.50, "Series A": 6.00, "Series B+": 20.00}
    assets = profile.get("physical_assets") or []
    inferred = stage_base.get(_stage(profile), 1.50)
    asset_notes = []
    asset_adders = {
        "Office / coworking space": (0.50, "office/coworking fitout"),
        "Warehouse / fulfilment centre": (2.00, "warehouse and stock concentration"),
        "Manufacturing plant / factory": (8.00, "manufacturing plant"),
        "Lab / R&D equipment": (3.00, "lab/R&D equipment"),
        "Medical devices / diagnostic equipment": (3.00, "medical/diagnostic equipment"),
        "Vehicles / delivery fleet": (1.00, "fleet assets"),
        "Drones / UAV equipment": (1.00, "drone hardware"),
        "Kitchen / food processing": (1.50, "kitchen/processing assets"),
        "Cold chain / refrigeration": (2.00, "cold-chain equipment"),
        "Solar / clean energy infrastructure": (6.00, "clean-energy infrastructure"),
        "Retail stores / kiosks": (1.00, "retail/kiosk fitout"),
        "Data centre / server room": (2.50, "server room equipment"),
    }
    for asset in assets:
        add, note = asset_adders.get(asset, (0.0, ""))
        inferred += add
        if note:
            asset_notes.append(note)

    hardware_split = _float(profile.get("hardware_software_split"))
    if hardware_split > 0:
        inferred *= 1.0 + min(hardware_split, 1.0) * 0.35
    if not assets or "None - fully cloud" in assets:
        inferred = min(inferred, 1.0)

    notes = [f"Property SI inferred from stage, team size, and physical assets ({', '.join(asset_notes) or 'asset-light profile'})."]
    return round(max(0.25, inferred), 2), notes


def infer_underwriting_inputs(profile: Dict[str, Any]) -> Dict[str, Any]:
    property_si, notes = _infer_property_si(profile)
    suggestions = suggest_quote_inputs(profile)

    def suggested_value(key: str, default: Any = None) -> Any:
        item = suggestions.get(key)
        if not item:
            return default
        value = item.get("value")
        return default if value in (None, "") else value

    stage = _stage(profile)
    team = _team_size(profile)
    # Bug fix: read explicit employee_count before falling back to team_size/headcount_total.
    # REQUIRED_INPUTS_BY_COVER lists employee_count as a valid alias; it must be honoured.
    employee_count = max(1, int(_float(
        profile.get("employee_count") or profile.get("team_size") or profile.get("headcount_total"),
        10,
    )))
    sector = str(profile.get("sector") or "")
    data_sensitivity = str(profile.get("data_sensitivity") or "Medium")
    physical_assets = profile.get("physical_assets") or []
    data_handled = profile.get("data_handled") or []

    revenue_base = {"Pre-seed": 0.75, "Seed": 3.0, "Series A": 20.0, "Series B+": 100.0}
    _explicit_rev = _explicit_cr(profile, "annual_revenue_cr", "revenue_cr")
    if _explicit_rev is not None:
        annual_revenue = _explicit_rev
    else:
        # No explicit revenue — estimate from stage, scaled by team size
        annual_revenue = revenue_base.get(stage, 3.0) * max(1.0, team / 50.0)

    cyber_base = {"Pre-seed": 1.0, "Seed": 2.0, "Series A": 5.0, "Series B+": 20.0}.get(stage, 2.0)
    if data_sensitivity == "High":
        cyber_base *= 1.5
    if sector in ("Fintech", "Healthtech"):
        cyber_base *= 1.3
    # Sector cap: data-light sectors should not inherit fintech-grade cyber SI
    sector_cyber_cap = SECTOR_CYBER_SI_CAP_CR.get(sector, 50.0)
    cyber_base = min(cyber_base, sector_cyber_cap)

    dno_base = {"Pre-seed": 1.0, "Seed": 2.0, "Series A": 5.0, "Series B+": 25.0}.get(stage, 2.0)
    if profile.get("has_investors") == "Yes":
        dno_base *= 1.2

    pi_base = {"Pre-seed": 1.0, "Seed": 2.0, "Series A": 5.0, "Series B+": 15.0}.get(stage, 2.0)
    pi_base *= 1.0 + min(1.0, _float(profile.get("b2b_pct"), 0.5)) * 0.25

    stock_default = property_si * 0.35 if _has_any(
        physical_assets,
        "Warehouse / fulfilment centre", "Retail stores / kiosks", "Kitchen / food processing",
    ) or "Physical inventory / goods" in data_handled else property_si * 0.12
    equipment_default = property_si * 0.45 if _has_any(
        physical_assets,
        "Manufacturing plant / factory", "Lab / R&D equipment", "Solar / clean energy infrastructure",
        "Data centre / server room", "Medical devices / diagnostic equipment",
    ) else property_si * 0.18

    export_share = _float(profile.get("export_eu_pct")) + _float(profile.get("export_us_pct")) + _float(profile.get("export_china_pct"))
    has_trade = "Physical inventory / goods" in data_handled or export_share > 0 or _has_any(physical_assets, "Warehouse / fulfilment centre")
    cargo_turnover = annual_revenue * (0.55 if has_trade else 0.10) * (1.0 + min(export_share, 1.0) * 0.5)
    receivables = annual_revenue * max(0.10, min(1.0, _float(profile.get("b2b_pct"), 0.5))) * 0.18
    project_value = property_si * (1.7 if _has_any(physical_assets, "Manufacturing plant / factory", "Solar / clean energy infrastructure") else 0.5)
    fleet_count = int(_float(profile.get("fleet_count"), 0))
    if fleet_count <= 0 and _has_any(physical_assets, "Vehicles / delivery fleet"):
        fleet_count = max(3, int(team * max(0.1, _float(profile.get("gig_headcount_pct"), 0.2))))
    healthcare_limit = max(1.0, annual_revenue * 0.20)
    fi_limit = max(2.0, annual_revenue * 0.25)
    payment_limit = max(1.0, annual_revenue * 0.12)
    recall_limit = max(1.0, annual_revenue * 0.20)
    production_budget = max(0.5, annual_revenue * 0.15)
    if stage in ("Pre-seed", "Seed"):
        gross_profit_default = max(0.25, annual_revenue * 0.25)
    elif stage == "Series A":
        gross_profit_default = max(0.50, annual_revenue * 0.30)
    else:
        gross_profit_default = max(1.00, annual_revenue * 0.35)

    inputs = {
        "property_sum_insured_cr": _float(suggested_value("property_sum_insured_cr", property_si)),
        "stock_sum_insured_cr": _float(suggested_value("stock_sum_insured_cr", round(max(0.10, stock_default), 2))),
        "equipment_sum_insured_cr": _float(suggested_value("equipment_sum_insured_cr", round(max(0.10, equipment_default), 2))),
        "gross_profit_si_cr": _float(suggested_value("gross_profit_si_cr", round(gross_profit_default, 2))),
        "cyber_limit_cr": _float(suggested_value("cyber_limit_cr", round(min(cyber_base, 50.0), 2))),
        "dno_limit_cr": _float(suggested_value("dno_limit_cr", round(min(dno_base, 30.0), 2))),
        "pi_limit_cr": _float(suggested_value("pi_limit_cr", round(min(pi_base, 25.0), 2))),
        "public_liability_limit_cr": _float(suggested_value("public_liability_limit_cr", round(min(max(1.0, property_si * 0.75), 25.0), 2))),
        "product_liability_limit_cr": _float(suggested_value("product_liability_limit_cr", round(min(max(1.0, annual_revenue * 0.20), 25.0), 2))),
        "payroll_cr": _float(suggested_value("payroll_cr", round(max(0.25, team * 0.12), 2))),
        "employee_count": employee_count,
        "cargo_turnover_cr": _float(suggested_value("cargo_turnover_cr", round(max(0.25, cargo_turnover), 2))),
        "receivables_on_credit_cr": _float(suggested_value("receivables_on_credit_cr", round(min(max(0.25, receivables), 500.0), 2))),
        "project_value_cr": _float(suggested_value("project_value_cr", round(max(0.50, project_value), 2))),
        "weather_exposed_si_cr": _float(suggested_value("weather_exposed_si_cr", round(max(0.50, property_si + stock_default), 2))),
        "cash_limit_cr": _float(suggested_value("cash_limit_cr", 0.10)),
        "crime_limit_cr": _float(suggested_value("crime_limit_cr", round(min(max(0.50, annual_revenue * 0.05), 15.0), 2))),
        "drone_hull_si_cr": _float(suggested_value("drone_hull_si_cr", 1.00 if _has_any(physical_assets, "Drones / UAV equipment") else 0.25)),
        "fleet_count": int(suggested_value("fleet_count", fleet_count or 1)),
        "healthcare_pi_limit_cr": _float(suggested_value("healthcare_pi_limit_cr", round(min(healthcare_limit, 25.0), 2))),
        "fi_pi_limit_cr": _float(suggested_value("fi_pi_limit_cr", round(min(fi_limit, 50.0), 2))),
        "payment_protection_limit_cr": _float(suggested_value("payment_protection_limit_cr", round(min(payment_limit, 25.0), 2))),
        "recall_limit_cr": _float(suggested_value("recall_limit_cr", round(min(recall_limit, 25.0), 2))),
        "production_budget_cr": _float(suggested_value("production_budget_cr", round(production_budget, 2))),
        "employment_practices_limit_cr": _float(suggested_value("employment_practices_limit_cr", round(min(max(1.0, annual_revenue * 0.05), 10.0), 2))),
        "_assumption_notes": notes,
    }
    return inputs


def normalize_cover_key(key: Any) -> Optional[str]:
    if key is None:
        return None
    text = str(key).strip()
    if not text:
        return None
    return COVER_ALIASES.get(text) or COVER_ALIASES.get(text.lower()) or text.lower()


def _select_covers(
    recommendations: List[Dict[str, Any]],
    bundle: Optional[Dict[str, Any]],
    max_covers: int = 8,
) -> List[str]:
    # Accumulate raw keys in priority order; deduplication and cap applied after normalization.
    raw: List[str] = []
    for key in (bundle or {}).get("mandatory_covers", []):
        raw.append(key)
    for key in (bundle or {}).get("optional_covers", []):
        raw.append(key)
    for product in recommendations or []:
        raw.append(product.get("key"))

    # Normalise, deduplicate, and enforce the cap across the full combined list.
    normalized: List[str] = []
    seen: set = set()
    for key in raw:
        if len(normalized) >= max_covers:
            break
        cover = normalize_cover_key(key)
        if cover in COVER_SPECS and cover not in seen:
            normalized.append(cover)
            seen.add(cover)
    if "business_interruption" in normalized:
        has_property = any(c in normalized for c in ("property_fire", "property_all_risk"))
        if not has_property and "property_fire" not in seen:
            normalized.insert(normalized.index("business_interruption"), "property_fire")
            seen.add("property_fire")
    return normalized


def _avg_risk(scores: Dict[str, Any], keys: Iterable[str]) -> float:
    values = [_float(scores.get(key), 0.0) for key in keys if key in scores]
    if not values:
        return 45.0
    return sum(values) / len(values)


def _stage_loading(stage: str) -> float:
    return {
        "Pre-seed": 0.90,
        "Seed": 1.00,
        "Series A": 1.12,
        "Series B+": 1.28,
    }.get(stage, 1.00)


def _sector_loading(cover: str, profile: Dict[str, Any]) -> float:
    sector = str(profile.get("sector") or "")

    # Use SECTOR_RATE_ADJUSTMENTS first — covers both upward and downward corrections
    if cover in SECTOR_RATE_ADJUSTMENTS:
        adj = SECTOR_RATE_ADJUSTMENTS[cover].get(sector)
        if adj is not None:
            return adj

    # Legacy upward-only loadings for covers not yet in SECTOR_RATE_ADJUSTMENTS
    if cover in ("property_fire", "property_all_risk", "business_interruption") and sector in (
        "D2C / Consumer Brands", "Logistics / Mobility", "Foodtech / Cloud Kitchen", "Cleantech / Climatetech",
    ):
        return 1.15
    if cover in ("engineering", "surety") and sector in ("Cleantech / Climatetech", "Deeptech / AI / Robotics"):
        return 1.15
    if cover == "motor_fleet" and sector in ("Logistics / Mobility", "D2C / Consumer Brands", "Foodtech / Cloud Kitchen"):
        return 1.15
    if cover == "healthcare_pi" and sector == "Healthtech":
        return 1.20
    if cover in ("financial_services_pi", "payment_protection") and sector == "Fintech":
        return 1.25
    if cover == "product_recall" and sector in ("D2C / Consumer Brands", "Foodtech / Cloud Kitchen", "Healthtech"):
        return 1.20
    if cover == "event_production" and sector == "Gaming / Media / Content":
        return 1.20
    return 1.00


def _control_loading(cover: str, profile: Dict[str, Any]) -> float:
    loading = 1.0
    if cover == "cyber_liability" and profile.get("cert_in_poc_designated"):
        loading *= 0.92
    if cover in ("employees_comp", "employee_health", "group_pa") and profile.get("posh_ic_constituted"):
        loading *= 0.97
    if profile.get("data_localisation_status") == "Full_onshore" and cover == "cyber_liability":
        loading *= 0.96
    return loading


def _climate_loading(cover: str, profile: Dict[str, Any]) -> float:
    if cover not in ("property_fire", "property_all_risk", "business_interruption", "parametric", "marine_transit"):
        return 1.0
    return {
        "Low": 1.00,
        "Medium": 1.08,
        "High": 1.18,
        "Extreme": 1.32,
        "Very High": 1.32,
    }.get(profile.get("facility_climate_risk_zone"), 1.00)


def _claims_loading(profile: Dict[str, Any]) -> float:
    raw = profile.get("claims_last_3_years")
    # Intake may pass a boolean (True/False) or a string ("Yes"/"1"); treat those as 1 claim.
    if isinstance(raw, bool):
        claims = 1.0 if raw else 0.0
    elif isinstance(raw, str):
        claims = 1.0 if raw.strip().lower() in ("yes", "true", "1") else _float(raw, 0.0)
    else:
        claims = max(0.0, _float(raw, 0.0))
    return min(1.75, 1.0 + claims * 0.15)


def _risk_loading(avg_risk: float) -> float:
    return round(min(MAX_RISK_LOADING, 0.75 + (max(0.0, min(avg_risk, 100.0)) / 100.0) * 0.75), 3)


def _revenue_loading(cover: str, profile: Dict[str, Any]) -> float:
    """Scale Cyber and PI premiums by annual revenue band.
    Sub-5Cr startups get a slight discount; 50Cr+ attract up to +20%.
    Only applies when annual_revenue_cr is explicitly provided."""
    if cover not in (
        "cyber_liability", "professional_indemnity", "financial_services_pi",
        "payment_protection", "healthcare_pi", "product_recall",
    ):
        return 1.0
    revenue = _explicit_cr(profile, "annual_revenue_cr", "revenue_cr")
    if revenue is None:
        return 1.0
    if revenue < 5:
        return 0.92
    if revenue < 20:
        return 1.00
    if revenue < 50:
        return 1.08
    if revenue < 100:
        return 1.15
    return 1.20


def _records_loading(cover: str, profile: Dict[str, Any]) -> float:
    """Scale Cyber premium by data records held (in lakhs).
    10M+ records (100 lakhs) is the DPDP significant-data-fiduciary threshold."""
    if cover != "cyber_liability":
        return 1.0
    records = _float(profile.get("data_records_lakhs"), 0)
    if records <= 0:
        return 1.0
    if records < 1:
        return 0.95
    if records < 10:
        return 1.00
    if records < 50:
        return 1.10
    if records < 100:
        return 1.20
    return 1.30


def _claims_unknown(profile: Dict[str, Any]) -> bool:
    raw = profile.get("claims_last_3_years")
    return raw in (None, "", "unknown", "Unknown", "UNKNOWN")


def _explicit_input_present(profile: Dict[str, Any], *keys: str) -> bool:
    for key in keys:
        if key in profile and profile.get(key) not in (None, ""):
            return True
    return False


def _pricing_rule(cover_key: str) -> PricingRule:
    spec = COVER_SPECS.get(cover_key)
    if cover_key in PRICING_RULES:
        return PRICING_RULES[cover_key]
    if spec and spec.pricing_unit == "per_employee":
        return PricingRule("employee_benefit_census")
    if spec and spec.pricing_unit == "per_vehicle":
        return PricingRule("fleet_count")
    return PricingRule("startup_base_rate")


def _specialty_reason_codes(profile: Dict[str, Any]) -> List[str]:
    sector = str(profile.get("sector") or "")
    sub_sector = str(profile.get("sub_sector") or "")
    desc = str(profile.get("product_description") or "").lower()
    assets = profile.get("physical_assets") or []
    export_share = _float(profile.get("export_eu_pct")) + _float(profile.get("export_us_pct")) + _float(profile.get("export_china_pct"))
    reasons = []
    if sector == "Deeptech / AI / Robotics" and (
        _float(profile.get("hardware_software_split"), 0) >= 0.5
        or _has_any(assets, "Lab / R&D equipment", "Manufacturing plant / factory")
    ):
        reasons.append("specialty_deeptech_hardware")
    if "space" in sub_sector.lower() or "spacetech" in sector.lower() or "satellite" in desc:
        reasons.append("specialty_spacetech")
    if profile.get("healthcare_operations") or sector == "Healthtech":
        reasons.append("specialty_healthcare_delivery")
    if _has_any(assets, "Medical devices / diagnostic equipment") or "medical device" in desc:
        reasons.append("specialty_med_device")
    if _float(profile.get("fleet_count"), 0) >= 50 or (sector == "Logistics / Mobility" and _team_size(profile) >= 200):
        reasons.append("specialty_large_logistics_fleet")
    if export_share >= 0.10:
        reasons.append("specialty_export_product")
    return reasons


def _cover_confidence(
    cover_key: str,
    exposure: float,
    profile: Dict[str, Any],
    inputs: Dict[str, Any],
) -> Dict[str, Any]:
    rule = _pricing_rule(cover_key)
    band = "technically_priced"
    precision = "point_estimate"
    score = 82
    reason_codes: List[str] = []
    benchmark_status = "comparable"
    benchmark_explanation = "Selected structure remains inside SPARC's startup benchmark box."

    if _claims_unknown(profile):
        score -= 8
        reason_codes.append("claims_history_unknown")

    if rule.max_benchmark_exposure_cr is not None and exposure > rule.max_benchmark_exposure_cr:
        benchmark_status = "not_comparable"
        benchmark_explanation = (
            f"{COVER_SPECS[cover_key].label} exposure exceeds the startup benchmark assumption; "
            "use quote/referral view instead."
        )
        score -= 14

    if rule.max_precise_exposure_cr is not None and exposure > rule.max_precise_exposure_cr:
        band = "directional_only"
        precision = "range"
        reason_codes.append("outside_precise_operating_box")
        score -= 12

    if rule.underwriter_exposure_cr is not None and exposure > rule.underwriter_exposure_cr:
        band = "underwriter_required"
        precision = "suppressed"
        reason_codes.append("underwriter_limit_threshold")
        score -= 25

    if cover_key == "employee_health" and not (
        _explicit_input_present(profile, "group_health_avg_age", "group_health_census_confirmed", "employee_census_confirmed")
    ):
        band = "directional_only"
        precision = "range"
        reason_codes.append("group_health_census_missing")
        benchmark_status = "not_comparable"
        benchmark_explanation = "Group Health is headcount-based here; census, age, location, and plan design are still missing."
        score -= 15

    if cover_key == "marine_transit":
        explicit_cargo = _explicit_input_present(profile, "cargo_annual_turnover_cr", "cargo_turnover_cr")
        revenue = _float(profile.get("annual_revenue_cr") or profile.get("revenue_cr"), 0.0)
        if not explicit_cargo or not _explicit_input_present(profile, "max_send_cr", "marine_max_send_cr", "cargo_max_send_cr"):
            band = "directional_only"
            precision = "range"
            reason_codes.append("marine_turnover_or_max_send_unconfirmed")
            benchmark_status = "not_comparable"
            benchmark_explanation = "Marine open-cover pricing needs annual transit turnover and max-send/route details."
            score -= 16
        if revenue > 0 and not explicit_cargo and exposure > revenue * 0.40:
            reason_codes.append("inferred_cargo_turnover_capped")
            score -= 8

    if cover_key == "trade_credit" and not _explicit_input_present(profile, "debtor_concentration_pct", "credit_terms_days", "top_buyer_concentration_pct"):
        band = "directional_only"
        precision = "range"
        reason_codes.append("debtor_book_missing")
        benchmark_status = "not_comparable"
        benchmark_explanation = "Trade Credit is directional until debtor spread and payment terms are confirmed."
        score -= 15

    if cover_key == "surety":
        band = "underwriter_required"
        precision = "suppressed"
        reason_codes.append("surety_referral_first")
        benchmark_status = "suppressed"
        benchmark_explanation = "Surety pricing requires contract wording, balance-sheet strength, and underwriter validation."
        score = min(score, 45)

    specialty = _specialty_reason_codes(profile)
    specialty_sensitive = {
        "product_liability", "product_recall", "professional_indemnity", "healthcare_pi",
        "engineering", "machinery_breakdown", "drone_insurance", "marine_transit",
    }
    if specialty and cover_key in specialty_sensitive:
        if band == "technically_priced":
            band = "directional_only"
            precision = "range"
        reason_codes.extend(code for code in specialty if code not in reason_codes)
        benchmark_status = "not_comparable"
        benchmark_explanation = "Specialty operations need product, site, controls, and loss-history validation before precise pricing."
        score -= 12

    score = max(20, min(95, score))
    return {
        "band": band,
        "score": score,
        "reason_codes": reason_codes,
        "precision_mode": precision,
        "pricing_basis": rule.pricing_basis,
        "calibration_basis": list(rule.calibration_basis),
        "benchmark_comparison": {
            "status": benchmark_status,
            "explanation": benchmark_explanation,
        },
    }


def _premium_display_metadata(premium_lakh: float, precision_mode: str) -> Dict[str, Any]:
    if precision_mode == "range":
        low = round(max(0.0, premium_lakh * 0.85), 2)
        high = round(premium_lakh * 1.20, 2)
        return {"display_premium_range_lakh": {"min": low, "max": high}}
    if precision_mode == "suppressed":
        return {"display_premium_lakh": None}
    return {"display_premium_lakh": premium_lakh}


def _portfolio_confidence(covers: List[Dict[str, Any]], scale: Dict[str, Any]) -> Dict[str, Any]:
    order = {"technically_priced": 0, "directional_only": 1, "underwriter_required": 2}
    worst = "technically_priced"
    reason_codes: List[str] = []
    score_values = []
    for item in covers:
        conf = item.get("quote_confidence") or {}
        band = conf.get("band", "technically_priced")
        if order.get(band, 0) > order.get(worst, 0):
            worst = band
        score_values.append(_float(conf.get("score"), 82.0))
        for reason in conf.get("reason_codes", []):
            if reason not in reason_codes:
                reason_codes.append(reason)
    if scale.get("segment") == "enterprise" and worst == "technically_priced":
        worst = "directional_only"
        reason_codes.append("enterprise_account_estimate")
    score = int(round(sum(score_values) / len(score_values))) if score_values else 82
    if worst == "underwriter_required":
        score = min(score, 55)
    elif worst == "directional_only":
        score = min(score, 70)
    return {"band": worst, "score": score, "reason_codes": reason_codes}


def _portfolio_precision(covers: List[Dict[str, Any]], quote_confidence: Dict[str, Any]) -> str:
    if quote_confidence.get("band") == "underwriter_required":
        return "suppressed"
    if quote_confidence.get("band") == "directional_only":
        return "range"
    if any(item.get("precision_mode") == "range" for item in covers):
        return "range"
    return "point_estimate"


def _enterprise_liability_rol(cover_key: str, avg_risk: float, profile: Dict[str, Any]) -> Optional[float]:
    band = ENTERPRISE_LIABILITY_ROL_BANDS.get(cover_key)
    if not band:
        return None
    min_rol, max_rol = band
    risk = max(0.0, min(avg_risk, 100.0))
    rol = min_rol + (risk / 100.0) * (max_rol - min_rol)
    if cover_key == "cyber_liability" and profile.get("cert_in_poc_designated"):
        rol -= 0.0005
    if cover_key == "cyber_liability" and profile.get("data_localisation_status") == "Full_onshore":
        rol -= 0.0003
    if profile.get("claims_last_3_years") and not _claims_unknown(profile):
        rol += (max_rol - min_rol) * 0.20
    if cover_key == "cyber_liability" and _float(profile.get("data_records_lakhs"), 0.0) >= 100:
        rol += 0.0005
    return round(max(min_rol, min(max_rol, rol)), 5)


def _group_health_per_head_lakh(avg_risk: float, employee_count: float) -> float:
    if employee_count >= 500:
        low, high = 0.12, 0.18
    elif employee_count >= 100:
        low, high = 0.13, 0.20
    else:
        low, high = 0.15, 0.24
    risk = max(0.0, min(avg_risk, 100.0)) / 100.0
    return round(low + (high - low) * risk, 4)


def _price_cover(
    cover_key: str,
    spec: CoverSpec,
    inputs: Dict[str, Any],
    scores: Dict[str, Any],
    profile: Dict[str, Any],
) -> Dict[str, Any]:
    exposure = _float(inputs.get(spec.exposure_field), 0.0)
    avg_risk = _avg_risk(scores, spec.risk_keys)
    loadings = {
        "risk": _risk_loading(avg_risk),
        "stage": _stage_loading(_stage(profile)),
        "sector": _sector_loading(cover_key, profile),
        "climate": _climate_loading(cover_key, profile),
        "controls": _control_loading(cover_key, profile),
        "claims": _claims_loading(profile),
        "revenue": _revenue_loading(cover_key, profile),
        "records": _records_loading(cover_key, profile),
    }
    raw_combined = 1.0
    for value in loadings.values():
        raw_combined *= value
    # Cap prevents pathological compounding (theoretical max without cap ≈ 7×).
    liability_like = cover_key in {
        "cyber_liability", "dno_liability", "professional_indemnity", "financial_services_pi",
        "healthcare_pi", "comprehensive_general_liability", "public_liability",
        "product_liability", "crime_fidelity", "employment_practices",
    }
    loading_cap = 2.0 if liability_like else MAX_COMBINED_LOADING
    cap_applied = raw_combined > loading_cap
    combined_loading = min(raw_combined, loading_cap)

    group_health_per_head = None
    if cover_key == "employee_health":
        group_health_per_head = _group_health_per_head_lakh(avg_risk, exposure)
        technical = exposure * group_health_per_head
        exposure_label = f"{int(exposure)} employees"
        sum_insured_cr = 0.0
        cap_applied = raw_combined > MAX_RISK_LOADING
        combined_loading = round(group_health_per_head / max(spec.rate_lakh_per_cr, 0.01), 3)
        loadings["per_head_lakh"] = group_health_per_head
    elif spec.pricing_unit == "per_employee":
        technical = exposure * spec.rate_lakh_per_cr * combined_loading
        exposure_label = f"{int(exposure)} employees"
        # per_employee covers have no sum-insured denomination; intentionally 0 so
        # they don't inflate the aggregate SI used in underwriter referral checks.
        sum_insured_cr = 0.0
    elif spec.pricing_unit == "per_vehicle":
        technical = exposure * spec.rate_lakh_per_cr * combined_loading
        exposure_label = f"{int(exposure)} vehicles"
        sum_insured_cr = 0.0
    else:
        technical = exposure * spec.rate_lakh_per_cr * combined_loading
        exposure_label = f"INR {exposure:.2f} Cr"
        sum_insured_cr = exposure

    enterprise_rol = None
    if spec.pricing_unit == "sum_insured" and exposure >= ENTERPRISE_LIABILITY_SI_THRESHOLD_CR:
        enterprise_rol = _enterprise_liability_rol(cover_key, avg_risk, profile)
    if enterprise_rol is not None:
        technical = exposure * 100.0 * enterprise_rol
        cap_applied = True
        combined_loading = round(technical / max(exposure * spec.rate_lakh_per_cr, 0.01), 3)
        loadings["enterprise_rol"] = enterprise_rol

    if cover_key == "dno_liability" and _stage(profile) in ("Series A", "Series B+"):
        spec_min = max(spec.min_lakh, 2.50)
    else:
        spec_min = spec.min_lakh
    premium_lakh = round(max(spec_min, technical), 2)
    confidence = _cover_confidence(cover_key, exposure, profile, inputs)
    display = _premium_display_metadata(premium_lakh, confidence["precision_mode"])
    return {
        "cover_key": cover_key,
        "cover_name": spec.label,
        "pricing_basis": confidence["pricing_basis"],
        "exposure_field": spec.exposure_field,
        "exposure_value": round(exposure, 2),
        "exposure_label": exposure_label,
        "sum_insured_cr": round(sum_insured_cr, 2),
        "base_rate_lakh_per_cr": spec.rate_lakh_per_cr,
        "average_risk_score": round(avg_risk, 1),
        "loadings": {key: round(value, 3) for key, value in loadings.items()},
        "raw_combined_loading": round(raw_combined, 3),
        "loading_cap_applied": cap_applied,
        "effective_rol": round(premium_lakh / (sum_insured_cr * 100), 4) if sum_insured_cr else None,
        "enterprise_rol_cap_applied": enterprise_rol is not None,
        "per_head_lakh": group_health_per_head,
        "premium_lakh": premium_lakh,
        "precision_mode": confidence["precision_mode"],
        "quote_confidence_band": confidence["band"],
        "quote_confidence": {
            "band": confidence["band"],
            "score": confidence["score"],
            "reason_codes": confidence["reason_codes"],
        },
        "calibration_basis": confidence["calibration_basis"],
        "benchmark_comparison": confidence["benchmark_comparison"],
        **display,
        "basis": (
            f"{spec.label}: {exposure_label} x enterprise ROL {enterprise_rol * 100:.2f}%."
            if enterprise_rol is not None
            else f"{spec.label}: {exposure_label} x per-head burning cost INR {group_health_per_head:.4f}L."
            if group_health_per_head is not None
            else f"{spec.label}: {exposure_label} x base rate {spec.rate_lakh_per_cr:.3f}L/unit x loadings."
        ),
    }


def _missing_inputs(profile: Dict[str, Any], covers: List[str]) -> List[str]:
    prompts = []
    if any(c in covers for c in ("property_fire", "property_all_risk", "business_interruption", "burglary")):
        if _asset_value_in_cr(profile) is None and _explicit_cr(profile, "property_sum_insured_cr") is None:
            prompts.append("Confirm property/stock/equipment sum insured for a bindable quote.")
    if "cyber_liability" in covers and _explicit_cr(profile, "cyber_limit_cr") is None:
        prompts.append("Confirm cyber policy limit and deductible preference.")
    if "dno_liability" in covers and _explicit_cr(profile, "dno_limit_cr") is None:
        prompts.append("Confirm D&O limit, latest fundraise amount, and investor board rights.")
    if "professional_indemnity" in covers and _explicit_cr(profile, "pi_limit_cr") is None:
        prompts.append("Confirm professional indemnity limit and largest customer contract value.")
    if any(c in covers for c in ("marine_transit", "trade_credit")):
        prompts.append("Confirm annual transit turnover, top buyer concentration, and credit terms.")
    if any(c in covers for c in ("engineering", "surety")):
        prompts.append("Confirm project value, contract period, and defect liability period.")
    if "motor_fleet" in covers:
        prompts.append("Confirm vehicle count, vehicle classes, driver controls, and claims history.")
    if "healthcare_pi" in covers:
        prompts.append("Confirm clinical services, practitioner credentials, patient volume, and prior malpractice claims.")
    if any(c in covers for c in ("financial_services_pi", "payment_protection")):
        prompts.append("Confirm licence type, transaction volume, fraud controls, and customer compensation obligations.")
    if "product_recall" in covers:
        prompts.append("Confirm batch volumes, recall plan, quality controls, and prior recall/contamination events.")
    if "event_production" in covers:
        prompts.append("Confirm production budget, venue controls, cast/equipment schedule, and cancellation exposure.")
    return prompts


def _input_present(profile: Dict[str, Any], aliases: Iterable[str]) -> bool:
    for alias in aliases:
        if alias == "claims_last_3_years" and alias in profile:
            return True
        val = profile.get(alias)
        if isinstance(val, bool):
            return True  # False is a valid explicit answer (e.g. claims_last_3_years=False)
        if _positive(val) is not None:
            return True
    return False


def _submitted_quote_source(profile: Dict[str, Any]) -> Dict[str, Any]:
    quote_inputs = profile.get("quote_user_inputs")
    if isinstance(quote_inputs, dict):
        return quote_inputs
    return profile


def _pricing_profile(profile: Dict[str, Any]) -> Dict[str, Any]:
    submitted = _submitted_quote_source(profile)
    if submitted is profile:
        return profile
    merged = dict(profile)
    merged.update(submitted)
    return merged


def _suggestion_for_aliases(suggestions: Dict[str, Dict[str, Any]], aliases: Iterable[str]) -> Optional[Dict[str, Any]]:
    for alias in aliases:
        if alias in suggestions:
            return suggestions[alias]
    return None


def _required_input_specs(
    profile: Dict[str, Any],
    covers: List[str],
    submitted_profile: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Return deduplicated user inputs required to quote the selected covers."""
    rows: List[Dict[str, Any]] = []
    seen = set()
    submitted = submitted_profile if submitted_profile is not None else _submitted_quote_source(profile)
    suggestions = suggest_quote_inputs(profile)
    for cover in covers:
        for aliases in REQUIRED_INPUTS_BY_COVER.get(cover, ()):
            key = aliases[0]
            if key in seen:
                continue
            seen.add(key)
            label, unit, help_text = INPUT_FIELD_LABELS.get(key, (key.replace("_", " ").title(), "", ""))
            rows.append({
                "key": key,
                "aliases": list(aliases),
                "label": label,
                "unit": unit,
                "help": help_text,
                "required_for": cover,
                "provided": _input_present(submitted, aliases),
                "suggestion": _suggestion_for_aliases(suggestions, aliases),
            })
    return rows


def _missing_required_inputs(
    profile: Dict[str, Any],
    covers: List[str],
    submitted_profile: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    return [row for row in _required_input_specs(profile, covers, submitted_profile) if not row["provided"]]


def pricing_input_request(
    profile: Dict[str, Any],
    recommendations: Optional[List[Dict[str, Any]]] = None,
    bundle: Optional[Dict[str, Any]] = None,
    status: str = "not_requested",
    submitted_profile: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    recommendations = recommendations or []
    covers = _select_covers(recommendations, bundle)
    if submitted_profile is None:
        submitted_profile = _submitted_quote_source(profile) if status != "not_requested" else {}
    return {
        "engine_version": ENGINE_VERSION,
        "quote_type": "input_required",
        "status": status,
        "currency": "INR",
        "bundle_name": (bundle or {}).get("name"),
        "covers_to_price": [
            {"cover_key": cover, "cover_name": COVER_SPECS[cover].label}
            for cover in covers
        ],
        "required_inputs": _required_input_specs(profile, covers, submitted_profile),
        "missing_required_inputs": _missing_required_inputs(profile, covers, submitted_profile),
        "message": "Quote is not calculated automatically. Confirm the underwriting inputs to generate an estimated quote.",
    }


def _referral_flags(
    profile: Dict[str, Any],
    scores: Dict[str, Any],
    inputs: Dict[str, Any],
    covers: List[str],
) -> List[str]:
    flags = []
    aggregate_si = sum(_float(inputs.get(field)) for field in (
        "property_sum_insured_cr", "stock_sum_insured_cr", "equipment_sum_insured_cr",
        "cyber_limit_cr", "dno_limit_cr", "pi_limit_cr", "public_liability_limit_cr",
    ))
    if aggregate_si > 50:
        flags.append("Aggregate selected SI exceeds INR 50 Cr; route to underwriter approval.")
    if "cyber_liability" in covers and _float(scores.get("Cyber Technical Risk")) >= 85:
        flags.append("Cyber risk score is 85+; require control questionnaire before firm pricing.")
    if "cyber_liability" in covers and _float(profile.get("data_records_lakhs"), 0) >= 100:
        flags.append("Data records exceed 10M (100 lakhs); DPDP significant-data-fiduciary rules apply — confirm compliance documentation.")
    if any(c in covers for c in ("property_fire", "property_all_risk")) and _float(inputs.get("property_sum_insured_cr")) > 25:
        flags.append("Property SI exceeds INR 25 Cr; validate occupancy, protection, and catastrophe exposure.")
    if profile.get("facility_climate_risk_zone") in ("High", "Extreme", "Very High"):
        flags.append("High climate zone; check flood/cyclone exposure and deductibles.")
    if _claims_unknown(profile):
        flags.append("Claims history is unknown; validate loss runs before treating pricing as technical.")
    elif profile.get("claims_last_3_years"):
        flags.append("Prior claims disclosed; validate loss runs before binding.")
    if "motor_fleet" in covers and _float(inputs.get("fleet_count")) >= 50:
        flags.append("Fleet count is 50+; validate driver vetting, telematics, route controls, and motor loss history.")
    if "healthcare_pi" in covers and profile.get("healthcare_operations"):
        flags.append("Healthcare operations disclosed; require practitioner credential and incident history before firm pricing.")
    if any(c in covers for c in ("financial_services_pi", "payment_protection")) and profile.get("rbi_registration"):
        flags.append("Regulated financial-services exposure; confirm licence scope, outsourcing controls, and regulator correspondence.")
    if "product_recall" in covers and profile.get("product_recall_exposure"):
        flags.append("Recall/contamination exposure disclosed; require QA controls, traceability, and recall plan.")
    if "surety" in covers and profile.get("contract_bid_or_performance_bond_need"):
        flags.append("Surety need disclosed; route to surety underwriter for financial strength and contract wording review.")
    if "event_production" in covers and profile.get("event_or_production_operations"):
        flags.append("Production/event exposure disclosed; validate venue, cancellation, cast, and equipment schedule.")
    sector = profile.get("sector", "")
    for cover in covers:
        appetite = get_appetite(cover, sector)
        if appetite == "bad":
            reason = BAD_RISK_REASONS_SHORT.get(cover, {}).get(sector, "")
            label = COVER_SPECS[cover].label if cover in COVER_SPECS else cover
            flags.append(
                f"{label}: adverse underwriting appetite for {sector} - refer to underwriter "
                f"before presenting quote. {reason}"
            )
    return flags


def _pricing_scale(profile: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
    revenue = _float(profile.get("annual_revenue_cr") or profile.get("revenue_cr"), 0.0)
    team = _team_size(profile)
    aggregate_limit = sum(_float(inputs.get(field)) for field in (
        "cyber_limit_cr", "dno_limit_cr", "pi_limit_cr", "public_liability_limit_cr",
        "product_liability_limit_cr", "fi_pi_limit_cr", "payment_protection_limit_cr",
    ))
    enterprise = revenue >= 500 or team >= 1000 or aggregate_limit > 150
    if enterprise:
        return {
            "segment": "enterprise",
            "benchmark_range_applicable": False,
            "label": "Enterprise account estimate",
            "message": "Startup benchmark premium ranges are suppressed because the account scale requires underwriter-led enterprise validation.",
        }
    return {
        "segment": "startup",
        "benchmark_range_applicable": True,
        "label": "Startup indicative estimate",
        "message": "Benchmark premium ranges remain comparable for this startup-scale account.",
    }


def price_output_stage(
    profile: Dict[str, Any],
    scores: Dict[str, Any],
    recommendations: Optional[List[Dict[str, Any]]] = None,
    bundle: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Return an auditable quote for the current recommendation output."""
    recommendations = recommendations or []
    covers = _select_covers(recommendations, bundle)

    if not profile.get("quote_requested"):
        return pricing_input_request(profile, recommendations, bundle, "not_requested")

    submitted = _submitted_quote_source(profile)
    missing_required = _missing_required_inputs(profile, covers, submitted)
    if missing_required:
        return pricing_input_request(profile, recommendations, bundle, "awaiting_inputs", submitted)

    pricing_profile = _pricing_profile(profile)
    inputs = infer_underwriting_inputs(pricing_profile)
    scale = _pricing_scale(pricing_profile, inputs)
    priced = [
        _price_cover(cover, COVER_SPECS[cover], inputs, scores, pricing_profile)
        for cover in covers
    ]
    cover_benchmark_issues = [
        item.get("benchmark_comparison", {})
        for item in priced
        if (item.get("benchmark_comparison") or {}).get("status") in ("not_comparable", "suppressed")
    ]
    if cover_benchmark_issues:
        scale = dict(scale)
        scale["benchmark_range_applicable"] = False
        scale["segment"] = "specialty_or_enterprise" if scale.get("segment") != "enterprise" else "enterprise"
        scale["label"] = "Specialty / underwriter-led estimate" if scale.get("segment") != "enterprise" else scale.get("label")
        scale["message"] = cover_benchmark_issues[0].get(
            "explanation",
            "Startup benchmark premium ranges are not comparable to the selected limits or specialty exposure.",
        )
    flags = _referral_flags(pricing_profile, scores, inputs, covers)
    if scale["segment"] == "enterprise":
        flags.insert(0, "Enterprise-scale account; treat output as a technical estimate and validate limits, retentions, controls, and tower structure with an underwriter.")
    if any(item.get("loading_cap_applied") for item in priced):
        flags.append(
            "Risk or enterprise ROL cap was applied on one or more covers - "
            "validate final rate, retention, and controls with an underwriter."
        )

    subtotal = round(sum(item["premium_lakh"] for item in priced), 2)
    discount_rate = 0.0
    if bundle and bundle.get("name") and len(priced) >= 3:
        discount_rate = 0.10 if len(priced) >= 5 else 0.05
    discount = round(subtotal * discount_rate, 2)
    net = round(max(0.0, subtotal - discount), 2)
    gst = round(net * GST_RATE, 2)
    gross = round(net + gst, 2)
    quote_confidence = _portfolio_confidence(priced, scale)
    precision_mode = _portfolio_precision(priced, quote_confidence)
    if precision_mode == "range":
        display_range = {"min": round(gross * 0.85, 2), "max": round(gross * 1.20, 2)}
        display_premium = None
    elif precision_mode == "suppressed":
        display_range = None
        display_premium = None
    else:
        display_range = None
        display_premium = gross
    benchmark_status = "comparable" if scale.get("benchmark_range_applicable", True) else "not_comparable"
    benchmark_explanation = scale.get("message") or "Benchmark range remains comparable for this startup-scale account."
    explanation_items = [
        "Premium math is deterministic and non-bindable; GenAI does not set price.",
        "Bundle discount is applied to subtotal before GST.",
    ]
    if precision_mode != "point_estimate":
        explanation_items.append("Precision is downgraded because one or more covers need richer underwriting inputs.")
    if quote_confidence.get("reason_codes"):
        explanation_items.append("Confidence drivers: " + ", ".join(quote_confidence["reason_codes"][:5]) + ".")

    return {
        "engine_version": ENGINE_VERSION,
        "quote_type": "indicative_underwriting_quote",
        "currency": "INR",
        "method": f"SPARC uses line-specific pre-underwriting pricing bases, capped loadings, referral rules, and {int(GST_RATE * 100)}% GST. Estimates are indicative and non-bindable.",
        "bundle_name": (bundle or {}).get("name"),
        "covers_priced": priced,
        "cover_count": len(priced),
        "total_sum_insured_cr": round(sum(item["sum_insured_cr"] for item in priced), 2),
        "subtotal_premium_lakh": subtotal,
        "bundle_discount_rate": discount_rate,
        "bundle_discount_lakh": discount,
        "net_premium_lakh": net,
        "gst_rate": GST_RATE,
        "gst_lakh": gst,
        "gross_premium_lakh": gross,
        "gross_premium_inr": int(round(gross * 100_000)),
        "display_premium_lakh": display_premium,
        "display_premium_range_lakh": display_range,
        "precision_mode": precision_mode,
        "quote_confidence": quote_confidence,
        "quote_confidence_label": QUOTE_CONFIDENCE_LABELS.get(quote_confidence["band"], quote_confidence["band"]),
        "calibration_basis": sorted({basis for item in priced for basis in item.get("calibration_basis", [])}),
        "benchmark_comparison": {
            "status": benchmark_status,
            "explanation": benchmark_explanation,
        },
        "explanation_items": explanation_items,
        "pricing_scale": scale,
        "underwriting_inputs": {key: value for key, value in inputs.items() if not key.startswith("_")},
        "assumptions": inputs.get("_assumption_notes", []),
        "missing_inputs": _missing_inputs(pricing_profile, covers),
        "underwriter_referral_flags": flags,
    }
