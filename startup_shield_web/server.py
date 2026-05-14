import json
import math
import os
import sqlite3
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import fields
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent

# Load .env from project root if present (no dependency needed)
_dotenv = PROJECT_ROOT / ".env"
if _dotenv.exists():
    for _line in _dotenv.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            _v = _v.strip()
            if len(_v) >= 2 and _v[0] == _v[-1] and _v[0] in ("'", '"'):
                _v = _v[1:-1]
            os.environ.setdefault(_k.strip(), _v)
    print(f"[startup] .env loaded — GEMINI_API_KEY {'SET' if os.environ.get('GEMINI_API_KEY') else 'MISSING'}", flush=True)
else:
    print(f"[startup] No .env found at {_dotenv}", flush=True)
sys.path.insert(0, str(PROJECT_ROOT))

from risk_engine import (  # noqa: E402
    PRODUCT_CATALOG,
    PRODUCT_RISK_MAP,
    SECTOR_PROFILES,
    StartupInput,
    SUB_SECTOR_PROFILES,
    check_hard_decline_by_subsector,
    compute_risk_scores,
    recommend_products,
)
from b2b2b_map import get_b2b2b_opportunities  # noqa: E402
from bundle_catalog import bundle_analytics, match_bundle, rank_bundles  # noqa: E402
from bundle_recommender_v2 import rank as rank_v2, risk_multiplier_breakdown as risk_multiplier_breakdown_v2  # noqa: E402
from bundle_scoring_utils import load_config  # noqa: E402
from custom_product_triggers import check_custom_triggers  # noqa: E402
from company_profiles import company_profile_count, get_company_profile, search_company_profiles  # noqa: E402
from global_products import get_top5_global  # noqa: E402
from genai_recommender import normalize_mode, rerank_payload  # noqa: E402
from policy_wording import compare_policy_wording  # noqa: E402
from premium_estimator import PREMIUM_FOOTNOTE, estimate_premium, get_size_bucket  # noqa: E402
from pricing_engine import price_output_stage  # noqa: E402
from risk_appetite import get_appetite, get_bad_reason  # noqa: E402
from weightage_rationale import MULTIPLIER_RATIONALE, get_score_rationale  # noqa: E402


DB_PATH = Path(os.environ.get(
    "SPARC_DB_PATH",
    str(Path(tempfile.gettempdir()) / "sparc_data.db") if os.environ.get("VERCEL") else str(PROJECT_ROOT / "sparc_data.db"),
))
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_MAX_TOKENS = int(os.environ.get("GEMINI_MAX_TOKENS", "4096"))
GEMINI_TIMEOUT_SECONDS = int(os.environ.get("GEMINI_TIMEOUT_SECONDS", "30"))
SPARC_ENGINE = os.environ.get("SPARC_ENGINE", "v2")


SUB_SECTOR_OPTIONS = {
    "Fintech": [
        "Fintech.NBFC_Digital_Lending", "Fintech.PA_PG", "Fintech.PA_Cross_Border",
        "Fintech.WealthTech_EOP", "Fintech.Neobank_PPI", "Fintech.InsurTech",
        "Fintech.Account_Aggregator",
    ],
    "Healthtech": [
        "Healthtech.Telemedicine", "Healthtech.Diagnostics",
        "Healthtech.PharmaTech_ePharmacy", "Healthtech.MedDevice_SaMD",
        "Healthtech.Clinical_Trials_SaaS",
    ],
    "Gaming / Media / Content": [
        "Gaming.Real_Money", "Gaming.Casual_Esports", "Gaming.OTT", "Gaming.Creator_Economy",
    ],
    "Logistics / Mobility": [
        "Logistics.Last_Mile_Delivery", "Logistics.B2B_Freight", "Logistics.EV_OEM",
    ],
    "D2C / Consumer Brands": [
        "D2C.Hardware_Electronics", "D2C.Food_Beverage", "D2C.Apparel_Footwear",
    ],
    "Deeptech / AI / Robotics": [
        "Deeptech.AI_Software", "Deeptech.Hardware_Robotics",
    ],
    "Edtech": [
        "Edtech.K12_Children", "Edtech.Test_Prep_Adult",
    ],
}


RISK_DISPLAY_GROUPS = {
    "Digital & Data": ["Cyber Technical Risk", "Data Privacy Risk", "IP Infringement Risk"],
    "Legal & Governance": ["Liability Risk", "Governance & Fraud Risk", "Regulatory Compliance Risk"],
    "Operational": ["Key Person Risk", "Property Risk", "Gig & Labour Risk"],
    "Macro & Emerging": ["ESG & Climate Risk", "Geopolitical Risk", "Policy Velocity Risk", "Reputation Risk"],
}


DATA_HANDLED_OPTIONS = [
    "Payments / financial transactions",
    "Health / medical records",
    "Personal identity data (KYC / Aadhaar)",
    "Employee / HR data (payroll, biometrics)",
    "Minors' / children's data",
    "Location / GPS tracking data",
    "Intellectual property / source code",
    "Customer behavioural / usage data",
    "Physical inventory / goods",
    "Sensitive personal data (DPDP Act)",
    "None of the above",
]

REGULATORY_OPTIONS = [
    "RBI / SEBI / IRDAI licensed",
    "FSSAI / food safety",
    "CDSCO / medical devices",
    "DPDP Act obligations",
    "DGCA / drone operations",
    "IT Act / CERT-In obligations",
    "Labour Codes / gig worker regulations",
    "BIS / QCO product certification",
    "NMC / telemedicine regulations",
    "MV Act / transport regulations",
    "SEBI BRSR / ESG reporting",
    "Competition Act / CCI",
    "EPR / environmental compliance",
    "None / minimal",
]

PHYSICAL_ASSET_OPTIONS = [
    "Office / coworking space",
    "Warehouse / fulfilment centre",
    "Manufacturing plant / factory",
    "Lab / R&D equipment",
    "Medical devices / diagnostic equipment",
    "Vehicles / delivery fleet",
    "Drones / UAV equipment",
    "Kitchen / food processing",
    "Cold chain / refrigeration",
    "Solar / clean energy infrastructure",
    "Retail stores / kiosks",
    "Data centre / server room",
    "None - fully cloud",
]

CUSTOMER_TYPE_OPTIONS = [
    "B2B Enterprise",
    "B2C Consumers",
    "Government / PSU",
    "D2C / Marketplace",
    "SMB / MSME",
]


DEFAULT_PROFILE = {
    "startup_name": "Acme Labs",
    "sector": next(iter(SECTOR_PROFILES.keys())),
    "sub_sector": None,
    "funding_stage": "Seed",
    "team_size": 15,
    "operations": "Digital-only",
    "data_sensitivity": "Medium",
    "product_description": "",
    "customer_type": [],
    "data_handled": [],
    "regulatory": [],
    "physical_assets": [],
    "has_investors": "No",
    "biggest_fear": "",
    "investor_cn_hk_pct": 0.0,
    "cumulative_fundraising_inr_cr": 0.0,
    "holdco_domicile": "India",
    "founder_concentration_index": 0.5,
    "dpiit_recognition": False,
    "rbi_registration": None,
    "gig_headcount_pct": 0.0,
    "posh_ic_constituted": False,
    "state_footprint": [],
    "cert_in_poc_designated": False,
    "sdf_probability": 0.0,
    "data_localisation_status": "Unknown",
    "ai_in_product": False,
    "ai_tier": "None",
    "hardware_software_split": 0.0,
    "b2b_pct": 0.5,
    "annual_revenue_cr": 0.0,
    "total_insurable_asset_value_cr": 0.0,
    "gross_profit_cr": 0.0,
    "fleet_count": 0,
    "vehicle_types": [],
    "healthcare_operations": False,
    "payment_or_card_program": False,
    "product_recall_exposure": False,
    "food_or_pharma_manufacturing": False,
    "contract_bid_or_performance_bond_need": False,
    "project_value_cr": 0.0,
    "event_or_production_operations": False,
    "claims_last_3_years": False,
    "export_eu_pct": 0.0,
    "export_us_pct": 0.0,
    "export_china_pct": 0.0,
    "chinese_supplier_pct_cogs": 0.0,
    "listed_customer_brsr_dependency": False,
    "facility_climate_risk_zone": "Low",
}


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                startup_name TEXT,
                sector TEXT,
                sub_sector TEXT,
                funding_stage TEXT,
                team_size INTEGER,
                risk_scores TEXT,
                icici_products TEXT,
                bundles TEXT,
                competitor_gaps TEXT,
                appetite_flags TEXT,
                premium_potential_total_min REAL,
                premium_potential_total_max REAL,
                size_bucket TEXT
            )
            """
        )


init_db()


def clean_float(value, default=0.0):
    try:
        if value is None or value == "":
            return default
        number = float(value)
        if math.isnan(number) or math.isinf(number):
            return default
        return number
    except (TypeError, ValueError):
        return default


def clean_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def as_list(value):
    return value if isinstance(value, list) else []


def effective_profile(raw):
    profile = DEFAULT_PROFILE.copy()
    profile.update(raw or {})

    profile["team_size"] = max(1, clean_int(profile.get("team_size"), 15))
    for key in [
        "investor_cn_hk_pct", "cumulative_fundraising_inr_cr",
        "founder_concentration_index", "gig_headcount_pct", "sdf_probability",
        "hardware_software_split", "b2b_pct", "export_eu_pct", "export_us_pct",
        "export_china_pct", "chinese_supplier_pct_cogs", "annual_revenue_cr",
        "total_insurable_asset_value_cr", "gross_profit_cr", "project_value_cr",
        "claims_last_3_years",
    ]:
        profile[key] = clean_float(profile.get(key), DEFAULT_PROFILE[key])
    profile["fleet_count"] = max(0, clean_int(profile.get("fleet_count"), 0))
    for key in [
        "healthcare_operations", "payment_or_card_program", "product_recall_exposure",
        "food_or_pharma_manufacturing", "contract_bid_or_performance_bond_need",
        "event_or_production_operations",
    ]:
        profile[key] = bool(profile.get(key))

    for key in ["customer_type", "data_handled", "regulatory", "physical_assets", "state_footprint", "vehicle_types"]:
        profile[key] = as_list(profile.get(key))

    if profile["sector"] not in SECTOR_PROFILES:
        profile["sector"] = DEFAULT_PROFILE["sector"]
    if profile.get("sub_sector") in ("", "General", "— General —", "- General -"):
        profile["sub_sector"] = None
    if profile.get("ai_tier") in ("", None):
        profile["ai_tier"] = "Applied" if profile.get("ai_in_product") else "None"
    profile["ai_in_product"] = bool(profile.get("ai_in_product") or profile.get("ai_tier") not in ("None", None, ""))
    operation_aliases = {
        "Hybrid (online+offline)": "Hybrid",
        "Offline / Physical": "Physical-only",
        "Hardware / IoT": "Hybrid",
        "Marketplace": "Hybrid",
    }
    profile["operations"] = operation_aliases.get(profile.get("operations"), profile.get("operations"))

    physical_assets = profile["physical_assets"]
    regulatory = profile["regulatory"]
    data_handled = profile["data_handled"]

    zone_rank = {"Low": 0, "Medium": 1, "High": 2, "Extreme": 3}
    rank_zone = {0: "Low", 1: "Medium", 2: "High", 3: "Extreme"}
    hw_boost = 0.0
    zone_floor = 0
    for asset in physical_assets:
        if asset == "Warehouse / fulfilment centre":
            hw_boost = max(hw_boost, 0.30)
            zone_floor = max(zone_floor, 1)
        elif asset == "Manufacturing plant / factory":
            hw_boost = max(hw_boost, 0.60)
            zone_floor = max(zone_floor, 2)
        elif asset == "Vehicles / delivery fleet":
            hw_boost = max(hw_boost, 0.20)
            zone_floor = max(zone_floor, 1)
        elif asset == "Lab / R&D equipment":
            hw_boost = max(hw_boost, 0.25)
        elif asset == "Medical devices / diagnostic equipment":
            hw_boost = max(hw_boost, 0.35)
        elif asset == "Drones / UAV equipment":
            hw_boost = max(hw_boost, 0.20)
        elif asset == "Kitchen / food processing":
            hw_boost = max(hw_boost, 0.20)
            zone_floor = max(zone_floor, 1)
        elif asset == "Cold chain / refrigeration":
            hw_boost = max(hw_boost, 0.25)
            zone_floor = max(zone_floor, 1)
        elif asset == "Solar / clean energy infrastructure":
            hw_boost = max(hw_boost, 0.50)
            zone_floor = max(zone_floor, 1)
        elif asset == "Retail stores / kiosks":
            hw_boost = max(hw_boost, 0.10)
            zone_floor = max(zone_floor, 1)
        elif asset == "Data centre / server room":
            hw_boost = max(hw_boost, 0.15)
        elif asset == "Office / coworking space":
            hw_boost = max(hw_boost, 0.05)

    profile["hardware_software_split"] = min(1.0, max(profile["hardware_software_split"], hw_boost))
    current_zone = profile.get("facility_climate_risk_zone", "Low")
    profile["facility_climate_risk_zone"] = rank_zone[max(zone_rank.get(current_zone, 0), zone_floor)]

    sdf_floor = {
        "Minors' / children's data": 0.80,
        "Sensitive personal data (DPDP Act)": 0.75,
        "Employee / HR data (payroll, biometrics)": 0.65,
        "Health / medical records": 0.70,
        "Personal identity data (KYC / Aadhaar)": 0.60,
        "Payments / financial transactions": 0.60,
        "Location / GPS tracking data": 0.40,
        "Customer behavioural / usage data": 0.30,
        "Intellectual property / source code": 0.20,
    }
    sensitive_high = {
        "Health / medical records", "Payments / financial transactions",
        "Personal identity data (KYC / Aadhaar)",
        "Employee / HR data (payroll, biometrics)",
        "Minors' / children's data", "Sensitive personal data (DPDP Act)",
    }
    for item in data_handled:
        profile["sdf_probability"] = max(profile["sdf_probability"], sdf_floor.get(item, 0.0))
    if set(data_handled) & sensitive_high and profile["data_sensitivity"] == "Low":
        profile["data_sensitivity"] = "Medium"
    if "Health / medical records" in data_handled:
        profile["healthcare_operations"] = profile["healthcare_operations"] or profile["sector"] == "Healthtech"
    if "Payments / financial transactions" in data_handled:
        profile["payment_or_card_program"] = profile["payment_or_card_program"] or profile["sector"] == "Fintech"
    if "Physical inventory / goods" in data_handled:
        profile["product_recall_exposure"] = profile["product_recall_exposure"] or profile["sector"] in ("D2C / Consumer Brands", "Foodtech / Cloud Kitchen")

    for reg in regulatory:
        if reg == "IT Act / CERT-In obligations":
            profile["cert_in_poc_designated"] = True
        elif reg == "Labour Codes / gig worker regulations":
            profile["gig_headcount_pct"] = max(profile["gig_headcount_pct"], 0.25)
        elif reg == "MV Act / transport regulations":
            profile["gig_headcount_pct"] = max(profile["gig_headcount_pct"], 0.20)
        elif reg == "BIS / QCO product certification":
            profile["hardware_software_split"] = max(profile["hardware_software_split"], 0.30)
        elif reg == "DGCA / drone operations":
            profile["hardware_software_split"] = max(profile["hardware_software_split"], 0.20)
        elif reg == "SEBI BRSR / ESG reporting":
            profile["listed_customer_brsr_dependency"] = True
        elif reg in ("CDSCO / medical devices", "NMC / telemedicine regulations"):
            profile["healthcare_operations"] = True
        elif reg in ("RBI / SEBI / IRDAI licensed",):
            profile["payment_or_card_program"] = profile["payment_or_card_program"] or profile["sector"] == "Fintech"
        elif reg == "FSSAI / food safety":
            profile["food_or_pharma_manufacturing"] = True
            profile["product_recall_exposure"] = True
    if "Vehicles / delivery fleet" in physical_assets and profile["fleet_count"] == 0:
        profile["fleet_count"] = max(1, int(profile["team_size"] * max(0.1, profile["gig_headcount_pct"] or 0.2)))
    if "Kitchen / food processing" in physical_assets:
        profile["food_or_pharma_manufacturing"] = True
        profile["product_recall_exposure"] = True
    if "Medical devices / diagnostic equipment" in physical_assets:
        profile["healthcare_operations"] = True
    if profile["sector"] == "Gaming / Media / Content" and profile["event_or_production_operations"]:
        profile["hardware_software_split"] = max(profile["hardware_software_split"], 0.10)
    if profile["total_insurable_asset_value_cr"] > 0:
        profile["asset_value_inr"] = profile["total_insurable_asset_value_cr"] * 10_000_000
    if profile["project_value_cr"] > 0:
        profile["capex_project_value_cr"] = profile["project_value_cr"]

    return profile


def make_startup_input(profile):
    allowed = {field.name for field in fields(StartupInput)}
    kwargs = {key: profile[key] for key in allowed if key in profile}
    return StartupInput(**kwargs)


def apply_dropdown_boosts(scores, data_handled, regulatory):
    boosts = {}
    for item in data_handled:
        if item == "Health / medical records":
            boosts["Cyber Technical Risk"] = max(boosts.get("Cyber Technical Risk", 0), 10)
            boosts["Data Privacy Risk"] = max(boosts.get("Data Privacy Risk", 0), 12)
        elif item == "Payments / financial transactions":
            boosts["Cyber Technical Risk"] = max(boosts.get("Cyber Technical Risk", 0), 8)
            boosts["Governance & Fraud Risk"] = max(boosts.get("Governance & Fraud Risk", 0), 8)
        elif item == "Minors' / children's data":
            boosts["Data Privacy Risk"] = max(boosts.get("Data Privacy Risk", 0), 15)
            boosts["Regulatory Compliance Risk"] = max(boosts.get("Regulatory Compliance Risk", 0), 12)
        elif item == "Employee / HR data (payroll, biometrics)":
            boosts["Data Privacy Risk"] = max(boosts.get("Data Privacy Risk", 0), 8)
            boosts["Cyber Technical Risk"] = max(boosts.get("Cyber Technical Risk", 0), 5)
        elif item == "Intellectual property / source code":
            boosts["IP Infringement Risk"] = max(boosts.get("IP Infringement Risk", 0), 12)
        elif item == "Location / GPS tracking data":
            boosts["Data Privacy Risk"] = max(boosts.get("Data Privacy Risk", 0), 6)

    for reg in regulatory:
        if reg == "RBI / SEBI / IRDAI licensed":
            boosts["Regulatory Compliance Risk"] = max(boosts.get("Regulatory Compliance Risk", 0), 15)
            boosts["Governance & Fraud Risk"] = max(boosts.get("Governance & Fraud Risk", 0), 10)
        elif reg == "FSSAI / food safety":
            boosts["Regulatory Compliance Risk"] = max(boosts.get("Regulatory Compliance Risk", 0), 12)
            boosts["Reputation Risk"] = max(boosts.get("Reputation Risk", 0), 10)
        elif reg == "CDSCO / medical devices":
            boosts["Regulatory Compliance Risk"] = max(boosts.get("Regulatory Compliance Risk", 0), 15)
            boosts["Liability Risk"] = max(boosts.get("Liability Risk", 0), 12)
        elif reg == "NMC / telemedicine regulations":
            boosts["Regulatory Compliance Risk"] = max(boosts.get("Regulatory Compliance Risk", 0), 12)
            boosts["Liability Risk"] = max(boosts.get("Liability Risk", 0), 10)
        elif reg == "EPR / environmental compliance":
            boosts["ESG & Climate Risk"] = max(boosts.get("ESG & Climate Risk", 0), 12)
            boosts["Regulatory Compliance Risk"] = max(boosts.get("Regulatory Compliance Risk", 0), 8)
        elif reg == "Competition Act / CCI":
            boosts["Governance & Fraud Risk"] = max(boosts.get("Governance & Fraud Risk", 0), 10)
            boosts["Regulatory Compliance Risk"] = max(boosts.get("Regulatory Compliance Risk", 0), 8)
        elif reg == "DGCA / drone operations":
            boosts["Liability Risk"] = max(boosts.get("Liability Risk", 0), 10)
            boosts["Regulatory Compliance Risk"] = max(boosts.get("Regulatory Compliance Risk", 0), 8)

    for category, delta in boosts.items():
        scores[category] = min(100.0, scores[category] + delta)
    return scores


def cluster_scores(scores):
    output = {}
    for group, keys in RISK_DISPLAY_GROUPS.items():
        vals = [scores[key] for key in keys if key in scores]
        output[group] = round(sum(vals) / len(vals), 1) if vals else 0.0
    return output


def priority_bucket(score):
    if score >= 70:
        return "Critical"
    if score >= 40:
        return "Recommended"
    return "Optional"


def product_mapping(recommendations, scores):
    rows = []
    for product in recommendations:
        key = product.get("key")
        weights = PRODUCT_RISK_MAP.get(key, {})
        drivers = sorted(
            [
                {
                    "risk": risk,
                    "score": round(scores.get(risk, 0.0), 1),
                    "weight": weight,
                }
                for risk, weight in weights.items()
            ],
            key=lambda item: (item["score"], item["weight"]),
            reverse=True,
        )
        rows.append({
            "product": product.get("name", key),
            "key": key,
            "score": product.get("score", 0),
            "priority": product.get("priority", priority_bucket(product.get("score", 0))),
            "top_risks": drivers[:3],
        })
    return rows


def bundle_recommendations(recommendations):
    bundles = [
        {"name": "Essential baseline", "timeline": "Buy now", "products": []},
        {"name": "Growth protection", "timeline": "Next 3 months", "products": []},
        {"name": "Regulatory resilience", "timeline": "Later / as exposure scales", "products": []},
    ]
    for product in recommendations:
        key = product.get("key", "")
        priority = product.get("priority", "")
        if product.get("mandatory") or key in {"employee_health", "employees_comp", "property_fire", "cyber_liability"} or priority == "Critical":
            bundles[0]["products"].append(product)
        elif key in {"dno_liability", "professional_indemnity", "product_liability", "business_interruption", "employment_practices"}:
            bundles[1]["products"].append(product)
        else:
            bundles[2]["products"].append(product)
    return [bundle for bundle in bundles if bundle["products"]]


def regulatory_triggers(profile):
    triggers = []
    if profile.get("rbi_registration") or "RBI / SEBI / IRDAI licensed" in profile["regulatory"]:
        triggers.append({"name": "Financial-sector registration", "detail": "RBI / SEBI / IRDAI exposure increases compliance and D&O pressure."})
    if profile.get("sdf_probability", 0) >= 0.5 or "DPDP Act obligations" in profile["regulatory"]:
        triggers.append({"name": "DPDP / SDF exposure", "detail": "Sensitive data handling can raise privacy, breach notification, and fiduciary obligations."})
    if profile.get("cert_in_poc_designated") or "IT Act / CERT-In obligations" in profile["regulatory"]:
        triggers.append({"name": "CERT-In readiness", "detail": "Incident reporting, log retention, and designated contact expectations apply."})
    if profile.get("team_size", 0) >= 10 and not profile.get("posh_ic_constituted"):
        triggers.append({"name": "POSH governance gap", "detail": "Teams above 10 employees should have an Internal Committee."})
    if profile.get("hardware_software_split", 0) > 0.3 or "BIS / QCO product certification" in profile["regulatory"]:
        triggers.append({"name": "Product / BIS exposure", "detail": "Hardware or certified products increase product-liability and recall exposure."})
    if profile.get("gig_headcount_pct", 0) > 0.2:
        triggers.append({"name": "Gig workforce exposure", "detail": "Aggregator and workforce obligations can trigger GPA, WC, and EPL needs."})
    if profile.get("listed_customer_brsr_dependency"):
        triggers.append({"name": "BRSR value-chain pressure", "detail": "Listed customers may push ESG reporting and controls down to suppliers."})
    return triggers


def mitigation_actions(top_risks, profile):
    actions = []
    for risk in top_risks[:5]:
        name = risk["name"]
        if "Cyber" in name:
            action = "Run access review, MFA enforcement, backup restore test, and incident-response drill."
        elif "Data Privacy" in name:
            action = "Map personal data flows, consent basis, retention, breach notification owner, and vendor DPAs."
        elif "Regulatory" in name:
            action = "Create a compliance calendar with owner, filing date, evidence folder, and escalation route."
        elif "Governance" in name:
            action = "Formalise board minutes, maker-checker approvals, fraud reporting, and investor disclosures."
        elif "Liability" in name:
            action = "Review customer contracts for indemnity caps, SLAs, disclaimers, and claims notification clauses."
        elif "Property" in name:
            action = "Inventory assets, verify replacement values, and document fire/flood/security controls."
        else:
            action = "Assign an owner, document controls, and review exposure again every quarter."
        actions.append({"risk": name, "action": action})
    if profile.get("biggest_fear"):
        actions.insert(0, {"risk": "Founder concern", "action": profile["biggest_fear"]})
    return actions[:6]


def assumptions(profile):
    fields_to_show = [
        "startup_name", "sector", "sub_sector", "funding_stage", "team_size",
        "operations", "data_sensitivity", "customer_type", "data_handled",
        "regulatory", "physical_assets", "has_investors", "rbi_registration",
        "sdf_probability", "gig_headcount_pct", "hardware_software_split",
        "b2b_pct", "facility_climate_risk_zone",
    ]
    return {key: profile.get(key) for key in fields_to_show}


def json_safe(value):
    if isinstance(value, dict):
        return {key: json_safe(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    if isinstance(value, set):
        return sorted(value)
    return value


def annotate_recommendations(recommendations, sector, size_bucket):
    annotated = []
    appetite_flags = {}
    for product in recommendations:
        item = dict(product)
        appetite = get_appetite(item.get("key"), sector)
        appetite_flags[item.get("key")] = appetite
        item["appetite"] = appetite
        if appetite == "bad":
            item["bad_reason"] = get_bad_reason(item.get("key"), sector)
        item["premium"] = estimate_premium(item.get("key"), size_bucket)
        annotated.append(item)
    return annotated, appetite_flags


def premium_summary(recommendations, bundle, global_products, size_bucket):
    seen = set()
    total_min = 0.0
    total_max = 0.0
    count = 0

    def add(key, premium):
        nonlocal total_min, total_max, count
        if not key or key in seen or not premium:
            return
        seen.add(key)
        total_min += premium.get("min_lakh", 0.0)
        total_max += premium.get("max_lakh", 0.0)
        count += 1

    for product in recommendations:
        add(product.get("key"), product.get("premium"))
    for key in (bundle or {}).get("mandatory_covers", []):
        add(key, estimate_premium(key, size_bucket))
    for product in (global_products or [])[:2]:
        add(product.get("key"), product.get("premium_range"))
    return {"min_lakh": round(total_min, 1), "max_lakh": round(total_max, 1), "count": count}


def score_rationales(sector, scores):
    output = {}
    for category in scores:
        rationale = get_score_rationale(sector, category)
        if rationale:
            output[category] = rationale
    return output


def multiplier_breakdown(profile):
    items = []
    if profile.get("sdf_probability", 0) > 0:
        items.append({"key": "sdf_adjuster", "applied": f"SDF multiplier {1 + profile['sdf_probability'] * 0.5:.2f}x from {profile['sdf_probability'] * 100:.0f}% SDF probability."})
    items.append({"key": "stage_multiplier", "applied": f"Funding stage {profile['funding_stage']} applied through sector category multipliers."})
    items.append({"key": "data_sensitivity_multiplier", "applied": f"Data sensitivity {profile['data_sensitivity']} applied to cyber, privacy, and compliance."})
    if profile.get("gig_headcount_pct", 0) > 0:
        items.append({"key": "gig_adjuster", "applied": f"Gig workforce {profile['gig_headcount_pct'] * 100:.0f}% lifts gig labour exposure."})
    if profile.get("hardware_software_split", 0) > 0:
        items.append({"key": "hardware_adjuster", "applied": f"Hardware split {profile['hardware_software_split'] * 100:.0f}% lifts property and compliance exposure."})
    if profile.get("export_eu_pct", 0) > 0:
        items.append({"key": "cbam_adjuster", "applied": f"EU revenue {profile['export_eu_pct'] * 100:.0f}% lifts ESG and geopolitical exposure."})
    if profile.get("ai_in_product"):
        items.append({"key": "ai_adjuster", "applied": "AI in product applies the AI policy-velocity multiplier."})
    if profile.get("listed_customer_brsr_dependency"):
        items.append({"key": "brsr_adjuster", "applied": "Listed-customer BRSR dependency applies ESG push-through uplift."})
    if profile.get("facility_climate_risk_zone") not in ("Low", None, ""):
        items.append({"key": "climate_adjuster", "applied": f"Climate zone {profile['facility_climate_risk_zone']} lifts property and ESG exposure."})
    if profile.get("b2b_pct", 0) > 0:
        items.append({"key": "b2b_adjuster", "applied": f"B2B revenue {profile['b2b_pct'] * 100:.0f}% lifts liability exposure."})
    return [{**item, **MULTIPLIER_RATIONALE.get(item["key"], {})} for item in items]


def save_recommendation(profile, scores, recommendations, bundle, global_products, appetite_flags, premium, size_bucket):
    with sqlite3.connect(DB_PATH) as conn:
        exists = conn.execute(
            "SELECT 1 FROM recommendations WHERE startup_name = ? AND risk_scores = ? LIMIT 1",
            (profile.get("startup_name"), json.dumps(scores, sort_keys=True)),
        ).fetchone()
        if exists:
            return
        conn.execute(
            """
            INSERT INTO recommendations
            (timestamp, startup_name, sector, sub_sector, funding_stage, team_size,
             risk_scores, icici_products, bundles, competitor_gaps, appetite_flags,
             premium_potential_total_min, premium_potential_total_max, size_bucket)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.utcnow().isoformat(),
                profile.get("startup_name"),
                profile.get("sector"),
                profile.get("sub_sector"),
                profile.get("funding_stage"),
                profile.get("team_size"),
                json.dumps(scores, sort_keys=True),
                json.dumps([r.get("key") for r in recommendations]),
                json.dumps(json_safe(bundle or {})),
                json.dumps([g.get("key") for g in global_products if g.get("label") != "icici"]),
                json.dumps(appetite_flags),
                premium["min_lakh"],
                premium["max_lakh"],
                size_bucket,
            ),
        )


def load_contacts():
    path = PROJECT_ROOT / "contacts.json"
    if not path.exists():
        return {
            "RM_NAME": "{{RM_NAME}}",
            "RM_PHONE": "{{RM_PHONE}}",
            "RM_EMAIL": "{{RM_EMAIL}}",
            "RM_OFFICE": "ICICI Lombard General Insurance - Commercial Lines",
        }
    return json.loads(path.read_text(encoding="utf-8"))


def gemini_enabled():
    return bool(os.environ.get("GEMINI_API_KEY"))


def extract_json_object(text):
    if not text:
        return None
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        return json.loads(cleaned[start:end + 1])
    except json.JSONDecodeError:
        return None


def call_gemini_json(prompt):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None, "GEMINI_API_KEY is not configured."

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent?key={api_key}"
    )
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}],
            }
        ],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": GEMINI_MAX_TOKENS,
            "responseMimeType": "application/json",
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }
    data = json.dumps(payload).encode("utf-8")
    body = None
    for attempt in range(2):
        try:
            req_copy = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req_copy, timeout=GEMINI_TIMEOUT_SECONDS) as response:
                body = json.loads(response.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as exc:
            try:
                detail = exc.read().decode("utf-8")[:500]
            except Exception:
                detail = str(exc)
            if exc.code == 503 and attempt == 0:
                import time as _time
                _time.sleep(2)
                continue
            return None, f"Gemini HTTP {exc.code}: {detail}"
        except urllib.error.URLError as exc:
            return None, f"Gemini network error: {exc.reason}"
        except TimeoutError:
            return None, "Gemini request timed out."
        except json.JSONDecodeError:
            return None, "Gemini returned a non-JSON API envelope."
    if body is None:
        return None, "Gemini unavailable after retry."

    candidate = body.get("candidates", [{}])[0]
    finish_reason = candidate.get("finishReason", "")
    parts = candidate.get("content", {}).get("parts", [])
    text = "".join(part.get("text", "") for part in parts)
    if finish_reason == "MAX_TOKENS":
        print(f"[gemini] Response truncated at {GEMINI_MAX_TOKENS} tokens; raw tail: {text[-200:]!r}", flush=True)
        return None, f"Gemini response truncated (MAX_TOKENS={GEMINI_MAX_TOKENS}); increase GEMINI_MAX_TOKENS."
    parsed = extract_json_object(text)
    if not isinstance(parsed, dict):
        print(f"[gemini] Could not parse JSON; finishReason={finish_reason!r}; raw text ({len(text)} chars): {text[:500]!r}", flush=True)
        return None, "Gemini response did not contain a valid JSON object."
    return parsed, None


def _non_empty_profile_value(value):
    if value in (None, "", False):
        return None
    if isinstance(value, (int, float)) and value == 0:
        return None
    if isinstance(value, list):
        items = [str(v) for v in value if v not in (None, "", "None", "None / minimal", "None - fully cloud")]
        return ", ".join(items) if items else None
    if value is True:
        return "Yes"
    return str(value)


def profile_context_for_why(profile):
    """Compact only useful entered fields so GenAI copy stays specific."""
    fields_to_include = [
        ("Sector", "sector"),
        ("Sub-sector", "sub_sector"),
        ("Stage", "funding_stage"),
        ("Team size", "team_size"),
        ("Operations", "operations"),
        ("Data sensitivity", "data_sensitivity"),
        ("Customer type", "customer_type"),
        ("Data handled", "data_handled"),
        ("Regulatory exposure", "regulatory"),
        ("Physical assets", "physical_assets"),
        ("Annual revenue / ARR INR Cr", "annual_revenue_cr"),
        ("Total insurable asset value INR Cr", "total_insurable_asset_value_cr"),
        ("Gross profit INR Cr", "gross_profit_cr"),
        ("Fleet count", "fleet_count"),
        ("Gig or contractor workforce share", "gig_headcount_pct"),
        ("Project / contract value INR Cr", "project_value_cr"),
        ("Biggest fear", "biggest_fear"),
        ("AI in product", "ai_in_product"),
        ("Healthcare operations", "healthcare_operations"),
        ("Payment or card programme", "payment_or_card_program"),
        ("Product recall exposure", "product_recall_exposure"),
        ("Food or pharma manufacturing", "food_or_pharma_manufacturing"),
        ("Bid or performance bond need", "contract_bid_or_performance_bond_need"),
        ("Event or production operations", "event_or_production_operations"),
        ("Claims in last 3 years", "claims_last_3_years"),
        ("Facility climate risk zone", "facility_climate_risk_zone"),
        ("Export to EU pct", "export_eu_pct"),
        ("Export to US pct", "export_us_pct"),
    ]
    lines = []
    for label, key in fields_to_include:
        value = _non_empty_profile_value((profile or {}).get(key))
        if value:
            lines.append(f"- {label}: {value}")
    return "\n".join(lines) or "- Profile: Startup"


def _bundle_cover_keys(bundle):
    return list(dict.fromkeys([
        *(((bundle or {}).get("mandatory_covers")) or []),
        *(((bundle or {}).get("optional_covers")) or []),
    ]))


COVER_REASON_FALLBACKS = {
    "CYBER": "Covers breach response, ransomware recovery, and data-related regulatory costs.",
    "cyber_liability": "Covers breach response, ransomware recovery, and data-related regulatory costs.",
    "D_AND_O": "Protects founders and directors if investors, regulators, or employees challenge management decisions.",
    "dno_liability": "Protects founders and directors if investors, regulators, or employees challenge management decisions.",
    "PI_TECH_EO": "Covers defence and client claims if software, APIs, or professional services cause financial loss.",
    "professional_indemnity": "Covers defence and client claims if software, APIs, or professional services cause financial loss.",
    "CRIME_FIDELITY": "Protects against employee fraud, theft, forgery, and misuse of company money or vendor access.",
    "crime_fidelity": "Protects against employee fraud, theft, forgery, and misuse of company money or vendor access.",
    "GROUP_HEALTH": "Medical cover for the team, useful for hiring, retention, and employee wellbeing.",
    "employee_health": "Medical cover for the team, useful for hiring, retention, and employee wellbeing.",
    "GROUP_PA": "Accident cover for employees, especially important where people travel, deliver, or work in the field.",
    "group_pa": "Accident cover for employees, especially important where people travel, deliver, or work in the field.",
    "EMPLOYERS_COMP": "Statutory workforce injury protection for employees and field teams.",
    "employees_comp": "Statutory workforce injury protection for employees and field teams.",
    "EMPLOYMENT_PRACTICES": "Covers legal defence for wrongful termination, discrimination, harassment, and other employment disputes.",
    "employment_practices": "Covers legal defence for wrongful termination, discrimination, harassment, and other employment disputes.",
    "ENGINEERING_CAR_EAR_CPM_MBD_EEI": "Protects machinery, contract works, erection projects, and electronic equipment from physical damage.",
    "engineering": "Protects machinery, contract works, erection projects, and electronic equipment from physical damage.",
    "PUBLIC_LIABILITY": "Covers third-party injury or property damage linked to premises, projects, events, or operations.",
    "public_liability": "Covers third-party injury or property damage linked to premises, projects, events, or operations.",
    "SURETY": "Supports bid and performance bond needs when contracts require proof of delivery or completion.",
    "surety": "Supports bid and performance bond needs when contracts require proof of delivery or completion.",
    "MARINE_CARGO": "Covers goods in transit while inventory, equipment, or project cargo moves between locations.",
    "marine_transit": "Covers goods in transit while inventory, equipment, or project cargo moves between locations.",
    "BUSINESS_INTERRUPTION": "Covers lost gross profit and continuing expenses after insured damage disrupts operations.",
    "business_interruption": "Covers lost gross profit and continuing expenses after insured damage disrupts operations.",
    "PRODUCT_LIABILITY": "Covers claims if a physical product causes injury, damage, or customer loss.",
    "product_liability": "Covers claims if a physical product causes injury, damage, or customer loss.",
}


def _fallback_cover_reason(bundle, key):
    criticality = ((bundle or {}).get("covers_criticality") or {}).get(key) or {}
    reason = criticality.get("reason")
    if reason:
        return reason
    fallback = COVER_REASON_FALLBACKS.get(key) or COVER_REASON_FALLBACKS.get(str(key).lower())
    if fallback:
        return fallback
    return "This cover is part of the matched package because it protects a risk that can affect the startup at this stage."


def _fallback_why_it_matters(bundle_match, recommendations):
    companion = (bundle_match or {}).get("companion_bundle") or {}
    result = {
        "bundle": (bundle_match or {}).get("description") or None,
        "bundle_covers": {
            key: _fallback_cover_reason(bundle_match, key)
            for key in _bundle_cover_keys(bundle_match)
        },
        "companion_bundle": companion.get("description") or (bundle_match or {}).get("companion_note") or None,
        "companion_covers": {
            key: _fallback_cover_reason(companion, key)
            for key in _bundle_cover_keys(companion)
        },
        "products": {},
    }
    for r in (recommendations or []):
        key = r.get("key", "")
        if not key:
            continue
        reason = r.get("nudge") or None
        result["products"][key] = reason
        result[key] = reason
    return result


def _normalised_text_lookup(data):
    if not isinstance(data, dict):
        return {}
    return {str(k).lower(): v for k, v in data.items()}


def _pick_generated_text(data, key, fallback=None):
    if not isinstance(data, dict):
        return fallback
    lookup = _normalised_text_lookup(data)
    value = data.get(key) or lookup.get(str(key).lower())
    if isinstance(value, str) and value.strip():
        return value.strip()
    return fallback


def _pick_generated_map(data, keys, fallback_map):
    if not isinstance(data, dict):
        data = {}
    return {
        key: _pick_generated_text(data, key, fallback_map.get(key))
        for key in keys
    }


def _generate_why_it_matters_legacy(profile, bundle_match, recommendations):
    """Return {bundle: "...", PRODUCT_KEY: "..."} personalised to sector/stage/team/ops.

    Falls back to static nudge strings when Gemini is unavailable.
    """
    sector = profile.get("sector", "startup")
    stage  = profile.get("funding_stage", "early stage")
    team   = profile.get("team_size", "")
    ops    = profile.get("business_model", "")
    revenue = profile.get("revenue_cr", "")

    team_str    = f"{team}-person team" if team else "team"
    revenue_str = f", ₹{revenue}Cr revenue" if revenue else ""
    ops_str     = f", {ops} ops" if ops else ""

    bundle_name = (bundle_match or {}).get("name", "")
    products = [{"key": r.get("key",""), "name": r.get("name", r.get("key",""))} for r in (recommendations or [])[:8]]

    if not gemini_enabled():
        result = {"bundle": None}
        for r in (recommendations or []):
            result[r.get("key", "")] = r.get("nudge") or None
        return result

    # Build the exact JSON template Gemini must fill — keys are pre-set so it cannot invent names
    template = {"bundle": f"<why {bundle_name} matters for this {sector} {stage}>"}
    for p in products:
        template[p["key"]] = f"<why {p['name']} matters for this {sector} {stage}>"
    template_str = json.dumps(template, indent=2, ensure_ascii=False)

    prompt = (
        f"You are a concise insurance risk analyst. Fill in the JSON template below with a "
        f"1-2 sentence 'Why it matters' explanation for each key, personalised to this startup:\n"
        f"- Sector: {sector}\n"
        f"- Stage: {stage}\n"
        f"- Team: {team_str}{revenue_str}{ops_str}\n\n"
        f"Rules:\n"
        f"- Keep ALL key names EXACTLY as shown — do not rename, lowercase, or add keys.\n"
        f"- Each value: 1-2 sentences, mentions sector/stage/team context, no bullet points.\n\n"
        f"Template to fill:\n{template_str}"
    )

    data, err = call_gemini_json(prompt)
    if err or not isinstance(data, dict):
        print(f"[why_it_matters] Gemini fallback: {err}", flush=True)
        result = {"bundle": None}
        for r in (recommendations or []):
            result[r.get("key", "")] = r.get("nudge") or None
        return result

    print(f"[why_it_matters] Gemini keys returned: {list(data.keys())}", flush=True)
    # normalise: build a lowercase lookup so key casing differences don't break matches
    data_lower = {k.lower(): v for k, v in data.items()}
    result = {"bundle": data.get("bundle")}
    for r in (recommendations or []):
        key = r.get("key", "")
        result[key] = data.get(key) or data_lower.get(key.lower()) or r.get("nudge") or None
    return result


def generate_why_it_matters(profile, bundle_match, recommendations):
    """Return personalised reasons for bundles, bundle covers, companions, and products."""
    fallback = _fallback_why_it_matters(bundle_match, recommendations)
    if not gemini_enabled():
        return fallback

    sector = (profile or {}).get("sector", "startup")
    stage = (profile or {}).get("funding_stage", "early stage")
    bundle_name = (bundle_match or {}).get("name", "recommended bundle")
    companion = (bundle_match or {}).get("companion_bundle") or {}
    products = [
        {"key": r.get("key", ""), "name": r.get("name", r.get("key", ""))}
        for r in (recommendations or [])
        if r.get("key")
    ]

    template = {
        "bundle": f"<two detailed simple sentences on why {bundle_name} matters>",
        "bundle_covers": {
            key: f"<two detailed simple sentences on why {key} matters inside {bundle_name}>"
            for key in fallback["bundle_covers"]
        },
        "companion_bundle": (
            f"<two detailed simple sentences on why {companion.get('name')} should be reviewed alongside Group Safeguard>"
            if companion.get("name")
            else None
        ),
        "companion_covers": {
            key: f"<two detailed simple sentences on why {key} matters inside {companion.get('name', 'the companion bundle')}>"
            for key in fallback["companion_covers"]
        },
        "products": {
            p["key"]: f"<two detailed simple sentences on why {p['name']} matters>"
            for p in products
        },
    }
    template_str = json.dumps(template, indent=2, ensure_ascii=False)

    prompt = (
        "You are a concise insurance risk analyst for Indian startups. Fill the JSON template with "
        "plain-English explanations that make the recommended insurance attractive to a founder or RM.\n\n"
        f"Startup context:\n{profile_context_for_why(profile)}\n\n"
        "Rules:\n"
        "- Keep the exact JSON shape and all keys exactly as provided; do not add or remove keys.\n"
        "- Each non-null value must be exactly two detailed but simple sentences.\n"
        "- The first sentence should explain what business risk the bundle or cover protects.\n"
        "- The second sentence should connect that protection to this startup's profile and why it matters now.\n"
        "- Personalise using the startup's sector, stage, team size, operations, data, people, asset, and regulatory context where relevant.\n"
        "- Explain business importance only; do not invent policy limits, prices, exclusions, guarantees, or legal advice.\n"
        f"- This is a {sector} startup at {stage} stage.\n\n"
        f"Template to fill:\n{template_str}"
    )

    data, err = call_gemini_json(prompt)
    if err or not isinstance(data, dict):
        print(f"[why_it_matters] Gemini fallback: {err}", flush=True)
        return fallback

    print(f"[why_it_matters] Gemini keys returned: {list(data.keys())}", flush=True)
    generated_products = data.get("products") if isinstance(data.get("products"), dict) else {}
    result = {
        "bundle": _pick_generated_text(data, "bundle", fallback.get("bundle")),
        "bundle_covers": _pick_generated_map(
            data.get("bundle_covers"),
            fallback["bundle_covers"].keys(),
            fallback["bundle_covers"],
        ),
        "companion_bundle": _pick_generated_text(data, "companion_bundle", fallback.get("companion_bundle")),
        "companion_covers": _pick_generated_map(
            data.get("companion_covers"),
            fallback["companion_covers"].keys(),
            fallback["companion_covers"],
        ),
        "products": {},
    }
    for r in (recommendations or []):
        key = r.get("key", "")
        if not key:
            continue
        reason = _pick_generated_text(generated_products, key, fallback["products"].get(key))
        result["products"][key] = reason
        result[key] = reason
    return result


def generate_bundle_insights(profile, bundle_match, revenue_breakdown, triggers, graduation_path):
    """Return a plain-English, neuromarketing-style explanation of why this bundle was chosen."""
    sector  = profile.get("sector", "startup")
    stage   = profile.get("funding_stage", "early stage")
    team    = profile.get("team_size", "")
    bundle_name = (bundle_match or {}).get("name", "this bundle")
    team_str = f"{team}-person team" if team else "team"

    # Summarise triggers in plain English
    trigger_lines = []
    for t in (triggers or [])[:4]:
        sig   = t.get("signal", "")
        prod  = t.get("product", "")
        reg   = t.get("regulation") or t.get("reg", "")
        trigger_lines.append(f"signal={sig}, product={prod}, regulation={reg}")

    # Summarise graduation path
    grad_lines = [f"{g.get('stage')} → {g.get('bundle')}" for g in (graduation_path or [])[:4]]

    if not gemini_enabled():
        return None

    prompt = f"""You are a startup insurance advisor writing for a first-time founder who has never bought insurance.
Write a "Why this bundle was chosen" section for their dashboard in plain, friendly English using neuromarketing principles (loss aversion, social proof, urgency, simplicity). No jargon, no formulas, no percentages.

Startup context:
- Sector: {sector}
- Stage: {stage}
- Team: {team_str}
- Recommended bundle: {bundle_name}
- Regulatory signals detected: {"; ".join(trigger_lines) if trigger_lines else "none"}
- Coverage growth path: {" / ".join(grad_lines) if grad_lines else "not available"}

Return a JSON object with exactly these keys:
{{
  "headline": "one punchy sentence (max 12 words) explaining why this bundle fits right now",
  "why_now": "2-3 sentences using loss aversion — what specific bad thing could happen without this cover at this exact stage/size",
  "social_proof": "1 sentence: what similar startups at this stage typically do (use social proof, not numbers)",
  "compliance_plain": ["plain-English sentence per regulatory trigger, max 3 items, e.g. 'You handle customer data — a breach without cyber cover means you pay DPDP fines out of pocket'"],
  "roadmap_narrative": "2 sentences describing the coverage journey as the startup grows, written like a story not a list"
}}

Rules: no bullet points inside string values, no markdown, no technical terms like TAM/margin/multiplier, write as if explaining to a smart non-finance person."""

    data, err = call_gemini_json(prompt)
    if err or not isinstance(data, dict):
        print(f"[bundle_insights] Gemini fallback: {err}", flush=True)
        return None
    return data


TRIGGER_PRODUCT_ALIASES = {
    "CYBER": "cyber_liability",
    "D_AND_O": "dno_liability",
    "PI_TECH_EO": "professional_indemnity",
    "CRIME_FIDELITY": "crime_fidelity",
    "GROUP_PA": "group_pa",
    "GROUP_HEALTH": "employee_health",
    "EMPLOYERS_COMP": "employees_comp",
    "EMPLOYMENT_PRACTICES": "employment_practices",
    "PUBLIC_LIABILITY": "public_liability",
    "PRODUCT_LIABILITY": "product_liability",
    "CGL_I_ELITE": "comprehensive_general_liability",
    "BHARAT_SOOKSHMA": "property_fire",
    "PROPERTY_FIRE": "property_fire",
    "PROPERTY_ALL_RISK": "property_all_risk",
    "BUSINESS_INTERRUPTION": "business_interruption",
    "MACHINERY_BREAKDOWN": "machinery_breakdown",
    "ELECTRONIC_EQUIPMENT": "electronic_equipment",
    "ENGINEERING_CAR_EAR_CPM_MBD_EEI": "engineering",
    "SURETY": "surety",
    "Drone_RPAS": "drone_insurance",
    "MARINE_CARGO": "marine_transit",
    "TRADE_CREDIT": "trade_credit",
    "EVENT_PRODUCTION": "event_production",
    "PRODUCT_RECALL": "product_recall",
    "PAYMENT_PROTECTION": "payment_protection",
    "FINANCIAL_SERVICES_PI": "financial_services_pi",
    "HEALTHCARE_PI": "healthcare_pi",
}


def canonical_cover_key(key):
    if not key:
        return ""
    text = str(key)
    return TRIGGER_PRODUCT_ALIASES.get(text) or TRIGGER_PRODUCT_ALIASES.get(text.upper()) or text


def displayed_cover_keys(bundle, recommendations):
    keys = set()
    bundles = [bundle or {}]
    if (bundle or {}).get("companion_bundle"):
        bundles.append((bundle or {}).get("companion_bundle") or {})
    for item in bundles:
        for key in item.get("mandatory_covers", []):
            keys.add(canonical_cover_key(key))
            keys.add(str(key))
        for key in item.get("optional_covers", []):
            keys.add(canonical_cover_key(key))
            keys.add(str(key))
    for rec in recommendations or []:
        key = rec.get("key")
        keys.add(canonical_cover_key(key))
        keys.add(str(key))
    return {key for key in keys if key}


def display_regulatory_triggers(triggers, bundle, recommendations):
    """Only show trigger rows for covers that are actually displayed to the user."""
    shown = displayed_cover_keys(bundle, recommendations)
    output = []
    for trigger in triggers or []:
        product = trigger.get("product")
        if product in shown or canonical_cover_key(product) in shown:
            output.append(trigger)
    return output


def contextual_coverage_roadmap(profile, current_bundle):
    """Build a roadmap from the startup's sector and exposure, not the generic config map."""
    sector = profile.get("sector", "")
    stage = profile.get("funding_stage", "Seed")
    assets = set(profile.get("physical_assets") or [])
    data = set(profile.get("data_handled") or [])
    regulatory = set(profile.get("regulatory") or [])
    team = int(profile.get("team_size") or 0)
    current = (current_bundle or {}).get("name")

    if sector == "Fintech":
        path = [
            ("Seed", "Business Shield SME"),
            ("Series A", "I-select Liability Insurance"),
            ("Series B", "Corporate Cover II"),
            ("Growth", "Corporate Cover II"),
        ]
    elif sector == "Healthtech":
        if "Medical devices / diagnostic equipment" in assets or "CDSCO / medical devices" in regulatory:
            path = [
                ("Seed", "I-select Liability Insurance"),
                ("Series A", "Industrial All Risk (IAR) Policy"),
                ("Series B", "Corporate Cover II"),
                ("Growth", "Corporate Cover II"),
            ]
        else:
            path = [
                ("Seed", "Business Shield SME"),
                ("Series A", "I-select Liability Insurance"),
                ("Series B", "Corporate Cover II"),
                ("Growth", "Corporate Cover II"),
            ]
    elif sector == "D2C / Consumer Brands":
        path = [
            ("Seed", "MSME Suraksha Kavach"),
            ("Series A", "Merchants Cover III"),
            ("Series B", "Bharat Laghu Udyam Suraksha"),
            ("Growth", "Corporate Cover II"),
        ]
    elif sector in ("Deeptech / AI / Robotics", "Cleantech / Climatetech"):
        if profile.get("project_value_cr") or profile.get("contract_bid_or_performance_bond_need"):
            path = [
                ("Seed", "Bharat Laghu Udyam Suraksha"),
                ("Series A", "Contractor All Risk (CAR) Insurance Policy"),
                ("Series B", "Industrial All Risk (IAR) Policy"),
                ("Growth", "Corporate Cover II"),
            ]
        else:
            path = [
                ("Seed", "Bharat Laghu Udyam Suraksha"),
                ("Series A", "Industrial All Risk (IAR) Policy"),
                ("Series B", "Industrial All Risk (IAR) Policy"),
                ("Growth", "Corporate Cover II"),
            ]
    elif sector == "Gaming / Media / Content" and profile.get("event_or_production_operations"):
        path = [
            ("Seed", "Entertainment Production Package"),
            ("Series A", "Entertainment Production Package"),
            ("Series B", "Corporate Cover II"),
            ("Growth", "Corporate Cover II"),
        ]
    elif team >= 100 or "Labour Codes / gig worker regulations" in regulatory or profile.get("gig_headcount_pct", 0) > 0.2:
        path = [
            ("Seed", "Group Safeguard Insurance Policy"),
            ("Series A", "Group Safeguard Insurance Policy"),
            ("Series B", "Corporate Cover II"),
            ("Growth", "Corporate Cover II"),
        ]
    elif "Payments / financial transactions" in data or "Personal identity data (KYC / Aadhaar)" in data:
        path = [
            ("Seed", "Business Shield SME"),
            ("Series A", "I-select Liability Insurance"),
            ("Series B", "Corporate Cover II"),
            ("Growth", "Corporate Cover II"),
        ]
    else:
        path = [
            ("Seed", current or "Business Shield SME"),
            ("Series A", current or "Enterprise Secure Package Policy"),
            ("Series B", "Corporate Cover II"),
            ("Growth", "Corporate Cover II"),
        ]

    if current and all(bundle != current for _, bundle in path):
        path.insert(0, (stage, current))

    seen = set()
    output = []
    for item_stage, bundle in path:
        key = (item_stage, bundle)
        if key in seen:
            continue
        seen.add(key)
        output.append({"stage": item_stage, "bundle": bundle})
    return output[:4]


def is_group_safeguard_bundle(bundle):
    return str((bundle or {}).get("name") or "").strip().lower() == "group safeguard insurance policy"


def attach_group_safeguard_companion(bundle, alternatives):
    """When Group Safeguard wins, promote the next closest package too."""
    if not is_group_safeguard_bundle(bundle) or not alternatives:
        return bundle, alternatives, []

    primary = dict(bundle)
    ranked = sorted(
        alternatives,
        key=lambda item: (
            float((item or {}).get("final_score") or 0),
            int((item or {}).get("fit_pct") or 0),
            -int((item or {}).get("rank") or 999),
        ),
        reverse=True,
    )
    companion = dict(ranked[0])
    companion["alternative_status"] = "companion"
    primary["companion_bundle"] = companion
    primary["companion_note"] = (
        "Group Safeguard is strongest for workforce benefits, but it is not sector-specific. "
        "Review the next closest package alongside it for the startup's operating and sector risks."
    )
    recommended_set = [primary, companion]
    remaining = [item for item in alternatives if item.get("name") != companion.get("name")]
    return primary, remaining, recommended_set


def group_safeguard_companion_candidates(primary_bundle, alternatives, legacy_payload):
    """Use ranked legacy candidates if v2 only returns Group Safeguard."""
    if not is_group_safeguard_bundle(primary_bundle) or alternatives:
        return alternatives

    candidates = []
    for item in [
        (legacy_payload or {}).get("bundle_match"),
        *((legacy_payload or {}).get("bundle_alternatives") or []),
    ]:
        if not item or not item.get("name"):
            continue
        if item.get("name") == (primary_bundle or {}).get("name"):
            continue
        if is_group_safeguard_bundle(item):
            continue
        candidates.append(dict(item))

    seen = set()
    deduped = []
    for item in candidates:
        name = item.get("name")
        if name in seen:
            continue
        seen.add(name)
        item.setdefault("alternative_status", "nearest_profile_fit")
        item.setdefault("rank", len(deduped) + 2)
        deduped.append(item)
    return sorted(
        deduped,
        key=lambda item: (
            float(item.get("final_score") or 0),
            int(item.get("fit_pct") or 0),
            -int(item.get("rank") or 999),
        ),
        reverse=True,
    )


def fallback_outreach_prompts(profile, scores, recommendations, bundle):
    contacts = load_contacts()
    top_scores = sorted(scores.items(), key=lambda item: item[1], reverse=True)[:3]
    risk_line = ", ".join(f"{name} {score:.0f}/100" for name, score in top_scores)
    products = list(recommendations[:5])
    if bundle:
        products.insert(0, {"key": "bundle", "name": bundle.get("name"), "nudge": bundle.get("description", "")})
    output = {}
    for product in products[:6]:
        key = product.get("key", "bundle")
        name = product.get("name", key)
        cta = f"We'd be happy to walk you through how {name} fits your current stage - connect with us at a time convenient to you."
        contact_block = f"{contacts.get('RM_NAME')} | {contacts.get('RM_PHONE')} | {contacts.get('RM_EMAIL')} | {contacts.get('RM_OFFICE')}"
        output[key] = {
            "email_subject": f"{profile.get('startup_name')} - {name} fit for your current risk profile",
            "email_body": (
                f"Hi {profile.get('startup_name')} team,\n\n"
                f"SPARC indicates your leading risk dimensions are {risk_line}. For a "
                f"{profile.get('sector')} startup at {profile.get('funding_stage')} with "
                f"{profile.get('team_size')} people, {name} is relevant because it addresses "
                f"the exposures most likely to affect contracts, continuity, and governance. "
                f"{product.get('nudge') or product.get('what_it_covers') or ''}\n\n"
                f"{cta}\n\n{contact_block}"
            ),
            "whatsapp": (
                f"Hi {profile.get('startup_name')} team - SPARC shows {risk_line}. "
                f"{name} looks relevant for your {profile.get('funding_stage')} stage. "
                f"{cta} {contacts.get('RM_NAME')} | {contacts.get('RM_PHONE')}"
            ),
        }
    return output


def outreach_prompt_payload(profile, scores, recommendations, bundle, size_bucket):
    contacts = load_contacts()
    top_scores = sorted(scores.items(), key=lambda item: item[1], reverse=True)[:3]
    products = []
    if bundle:
        products.append({"key": "bundle", "name": bundle.get("name", "Bundle recommendation")})
    for product in recommendations[:5]:
        products.append({"key": product.get("key"), "name": product.get("name", product.get("key"))})
    products = [product for product in products[:6] if product.get("key") and product.get("name")]

    product_lines = "\n".join(
        f"- {product['key']}: {product['name']}" for product in products
    )
    top_score_line = ", ".join(f"{name}: {score:.0f}/100" for name, score in top_scores)
    profile_highlights = [
        f"Customer types: {', '.join(profile.get('customer_type') or ['not specified'])}",
        f"Data handled: {', '.join(profile.get('data_handled') or ['not specified'])}",
        f"Regulatory exposures: {', '.join(profile.get('regulatory') or ['not specified'])}",
        f"Operations: {profile.get('operations')}; data sensitivity: {profile.get('data_sensitivity')}",
        f"Size bucket: {size_bucket}",
    ]

    return f"""
You are an ICICI Lombard Relationship Manager writing personalised outreach for
{profile.get('startup_name')} ({profile.get('sector')}, {profile.get('funding_stage')}, {profile.get('team_size')} people).

Their top risk scores: {top_score_line}.
Their profile highlights:
{chr(10).join('- ' + item for item in profile_highlights)}

Generate concise outreach drafts for the following {len(products)} products. For EACH product:
1. EMAIL VERSION: subject line + body in 70-90 words with a specific "why for them" grounded in their risk score. End with the soft CTA. Include contact block placeholders.
2. WHATSAPP VERSION: 30-40 words, one-message format, casual tone, no subject line, same CTA.

Products to cover:
{product_lines}

Output ONLY valid JSON in this exact shape:
{{
  "product_key": {{
    "email_subject": "...",
    "email_body": "...",
    "whatsapp": "..."
  }}
}}

Contact block to use:
Name: {contacts.get('RM_NAME')} | Phone: {contacts.get('RM_PHONE')} | Email: {contacts.get('RM_EMAIL')} | {contacts.get('RM_OFFICE')}

Soft CTA text:
We'd be happy to walk you through how [Product] fits your current stage - connect with us at a time convenient to you.

Return compact JSON only. Do not wrap in markdown. Do not add commentary outside JSON.
""".strip()


def normalize_outreach_response(raw, profile, scores, recommendations, bundle):
    fallback = fallback_outreach_prompts(profile, scores, recommendations, bundle)
    if not isinstance(raw, dict):
        return fallback, "fallback"

    normalized = {}
    for key, fallback_item in fallback.items():
        item = raw.get(key)
        if not isinstance(item, dict):
            normalized[key] = fallback_item
            continue
        subject = str(item.get("email_subject") or fallback_item["email_subject"]).strip()
        body = str(item.get("email_body") or fallback_item["email_body"]).strip()
        whatsapp = str(item.get("whatsapp") or fallback_item["whatsapp"]).strip()
        normalized[key] = {
            "email_subject": subject,
            "email_body": body,
            "whatsapp": whatsapp,
        }
    return normalized, "gemini"


def outreach_prompts(profile, scores, recommendations, bundle, size_bucket):
    if not gemini_enabled():
        return fallback_outreach_prompts(profile, scores, recommendations, bundle), "fallback", None

    prompt = outreach_prompt_payload(profile, scores, recommendations, bundle, size_bucket)
    raw, error = call_gemini_json(prompt)
    prompts, source = normalize_outreach_response(raw, profile, scores, recommendations, bundle)
    return prompts, source, error


def _legacy_score(raw):
    profile = effective_profile(raw)
    decline = check_hard_decline_by_subsector(profile.get("sub_sector"))
    if decline:
        return {"decline": decline, "profile": profile}

    inp = make_startup_input(profile)
    scores = compute_risk_scores(inp)
    scores = apply_dropdown_boosts(scores, profile["data_handled"], profile["regulatory"])
    recommendations = recommend_products(
        scores,
        profile["sector"],
        profile["team_size"],
        profile["funding_stage"],
        inp=inp,
    )
    size_bucket = get_size_bucket(profile["funding_stage"], profile["team_size"])
    profile["size_bucket"] = size_bucket
    recommendations, appetite_flags = annotate_recommendations(recommendations, profile["sector"], size_bucket)
    preferred_recommendations = [item for item in recommendations if item.get("appetite") != "bad"]
    not_preferred_recommendations = [item for item in recommendations if item.get("appetite") == "bad"]
    ranked_bundles = rank_bundles(profile["sector"], profile["funding_stage"], scores, inp)
    bundle = ranked_bundles[0] if ranked_bundles else match_bundle(profile["sector"], profile["funding_stage"], scores, inp)
    bundle_alternatives = ranked_bundles[1:] if ranked_bundles else []
    analytics = bundle_analytics(profile["sector"], profile["funding_stage"], scores, inp, ranked_bundles)
    global_ranked = get_top5_global(scores, profile["sector"], size_bucket)
    premium = premium_summary(recommendations, bundle, global_ranked, size_bucket)
    downstream = get_b2b2b_opportunities(
        profile["sector"],
        profile.get("customer_type", []),
        customer_base_estimate=max(0, profile.get("team_size", 0) * 2),
    )
    custom_triggers = check_custom_triggers(scores, inp, profile)
    overall = round(sum(scores.values()) / len(scores), 1)
    top_risks = [
        {"name": key, "score": round(value, 1)}
        for key, value in sorted(scores.items(), key=lambda item: item[1], reverse=True)[:5]
    ]
    mapping = product_mapping(recommendations, scores)
    rounded_scores = {key: round(value, 1) for key, value in scores.items()}
    bundle, bundle_alternatives, recommended_bundle_set = attach_group_safeguard_companion(bundle, bundle_alternatives)
    safe_bundle = json_safe(bundle)
    pricing_quote = price_output_stage(profile, rounded_scores, preferred_recommendations, safe_bundle)
    save_recommendation(profile, rounded_scores, recommendations, safe_bundle, global_ranked, appetite_flags, premium, size_bucket)
    outreach, outreach_source, outreach_error = outreach_prompts(profile, rounded_scores, preferred_recommendations, safe_bundle, size_bucket)
    return {
        "profile": profile,
        "scores": rounded_scores,
        "clusters": cluster_scores(scores),
        "overall": overall,
        "top_risks": top_risks,
        "recommendations": preferred_recommendations,
        "not_preferred_recommendations": not_preferred_recommendations,
        "bundles": bundle_recommendations(recommendations),
        "bundle_match": safe_bundle,
        "bundle_alternatives": json_safe(bundle_alternatives),
        "recommended_bundle_set": json_safe(recommended_bundle_set),
        "product_mapping": mapping,
        "size_bucket": size_bucket,
        "premium_summary": premium,
        "pricing_engine_quote": json_safe(pricing_quote),
        "premium_footnote": PREMIUM_FOOTNOTE,
        "global_products": json_safe(global_ranked),
        "score_rationales": score_rationales(profile["sector"], rounded_scores),
        "multiplier_breakdown": multiplier_breakdown(profile),
        "regulatory_triggers": regulatory_triggers(profile),
        "mitigations": mitigation_actions(top_risks, profile),
        "assumptions": assumptions(profile),
        "downstream_opportunities": downstream,
        "custom_triggers": custom_triggers,
        "outreach_prompts": outreach,
        "outreach_source": outreach_source,
        "outreach_error": outreach_error,
        "gemini_enabled": gemini_enabled(),
        # ── New fields (appended; never replaces existing keys) ──────────
        "revenue_breakdown":         analytics.get("revenue_breakdown", []),
        "risk_multiplier_breakdown": analytics.get("risk_multiplier_breakdown", {}),
        "regulatory_triggers_fired": analytics.get("regulatory_triggers_fired", []),
    }


def _v2_bundle_to_payload(rec, rank=1):
    return {
        "name": rec.bundle,
        "il_product_name": "SPARC v2 composite bundle",
        "mandatory_covers": rec.components,
        "optional_covers": [],
        "description": rec.rationale.get("coverage", ""),
        "criticality": "High" if rec.final >= 0.45 else "Medium",
        "fit_pct": min(100, max(0, int(round(rec.final * 100)))),
        "match_strength": "strong" if rec.final >= 0.45 else "nearest",
        "nearest_fallback": rec.final < 0.45,
        "rank": rank,
        "fit_delta": 0,
        "alternative_status": "top_pick" if rank == 1 else "lesser_relevant",
        "prerequisite_notes": [],
        "fire_awareness_note": None,
        "final_score": rec.final,
        "premium_inr": rec.premium_inr,
        "risk_mult": rec.risk_mult,
        "revenue_score": rec.revenue_score,
        "score_rationale": rec.rationale,
        "regulatory_triggers_fired": rec.regulatory_triggers_fired,
        "compliance_flags": rec.compliance_flags,
        "config_version": rec.config_version,
    }


def _revenue_breakdown_v2(recs):
    output = []
    for rec in recs:
        output.append({
            "bundle": rec.bundle,
            "tam_cr": None,
            "adoption": None,
            "margin": None,
            "trajectory": None,
            "score": rec.revenue_score,
            "why": rec.rationale.get("revenue", ""),
        })
    cfg = load_config()
    by_name = {bm.name: bm for bm in cfg.bundle_meta.values()}
    for row in output:
        bm = by_name.get(row["bundle"])
        if bm:
            row.update({
                "tam_cr": bm.tam_cr,
                "adoption": bm.adoption,
                "margin": bm.margin,
                "trajectory": bm.trajectory,
            })
    return output


def _v2_score(raw):
    payload = _legacy_score(raw)
    if "profile" not in payload or "scores" not in payload:
        return payload

    cfg = load_config()
    v2_profile = dict(payload["profile"])
    v2_profile["scores"] = payload["scores"]
    if isinstance(raw, dict):
        for key in ("asset_value_inr", "drone_ops", "drone_operations"):
            if key in raw:
                v2_profile[key] = raw[key]

    recs = rank_v2(v2_profile, cfg)
    if not recs:
        payload["config_version"] = cfg.config_version
        payload.setdefault("compliance_flags", [])
        payload.setdefault("graduation_map", cfg.graduation_map)
        return payload

    legacy_bundle_payload = {
        "bundle_match": payload.get("bundle_match"),
        "bundle_alternatives": payload.get("bundle_alternatives", []),
    }
    bundle_payloads = [_v2_bundle_to_payload(rec, rank=i + 1) for i, rec in enumerate(recs)]
    companion_candidates = group_safeguard_companion_candidates(
        bundle_payloads[0],
        bundle_payloads[1:],
        legacy_bundle_payload,
    )
    top_bundle, bundle_alternatives, recommended_bundle_set = attach_group_safeguard_companion(
        bundle_payloads[0],
        companion_candidates,
    )
    payload["bundle_match"] = json_safe(top_bundle)
    payload["bundle_alternatives"] = json_safe(bundle_alternatives)
    payload["recommended_bundle_set"] = json_safe(recommended_bundle_set)
    payload["pricing_engine_quote"] = json_safe(price_output_stage(
        payload["profile"],
        payload["scores"],
        payload.get("recommendations", []),
        payload["bundle_match"],
    ))
    # Bundle-only quote: prices just the bundle's mandatory covers — no standalone recs.
    payload["bundle_only_pricing_quote"] = json_safe(price_output_stage(
        payload["profile"],
        payload["scores"],
        [],
        {
            "name": bundle_payloads[0].get("name"),
            "mandatory_covers": bundle_payloads[0].get("mandatory_covers", []),
            "optional_covers": [],
        },
    ))
    payload["revenue_breakdown"] = json_safe(_revenue_breakdown_v2(recs))
    payload["risk_multiplier_breakdown"] = json_safe(risk_multiplier_breakdown_v2(v2_profile, cfg))
    payload["regulatory_triggers_fired"] = json_safe(recs[0].regulatory_triggers_fired)
    scoped_triggers = display_regulatory_triggers(
        recs[0].regulatory_triggers_fired,
        payload.get("bundle_match"),
        payload.get("recommendations", []),
    )
    payload["display_regulatory_triggers"] = json_safe(scoped_triggers)
    payload["graduation_map"] = json_safe(cfg.graduation_map)
    payload["coverage_roadmap"] = json_safe(contextual_coverage_roadmap(
        payload["profile"],
        payload.get("bundle_match"),
    ))
    payload["compliance_flags"] = json_safe([
        flag
        for rec in recs
        for flag in rec.compliance_flags
    ])
    payload["config_version"] = cfg.config_version

    payload["why_it_matters"] = json_safe(generate_why_it_matters(
        payload["profile"],
        payload.get("bundle_match"),
        payload.get("recommendations", []),
    ))

    payload["bundle_insights"] = json_safe(generate_bundle_insights(
        payload["profile"],
        payload.get("bundle_match"),
        payload.get("revenue_breakdown", []),
        scoped_triggers,
        payload.get("coverage_roadmap", []),
    ))

    return payload


def _shadow_log_path():
    env_path = os.environ.get("SPARC_SHADOW_LOG_PATH")
    candidates = []
    if env_path:
        candidates.append(Path(env_path))
    candidates.extend([
        Path("/var/log/sparc_shadow.jsonl"),
        PROJECT_ROOT / "sparc_shadow.jsonl",
        Path(tempfile.gettempdir()) / "sparc_shadow.jsonl",
    ])
    for candidate in candidates:
        try:
            candidate.parent.mkdir(parents=True, exist_ok=True)
            with candidate.open("a", encoding="utf-8"):
                pass
            return candidate
        except Exception:
            continue
    return None


def _log_diff(payload_legacy, payload_v2):
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "legacy_top_bundle": (payload_legacy.get("bundle_match") or {}).get("name"),
        "v2_top_bundle": (payload_v2.get("bundle_match") or {}).get("name"),
        "legacy_keys": sorted(payload_legacy.keys()),
        "v2_keys": sorted(payload_v2.keys()),
        "missing_in_v2": sorted(set(payload_legacy.keys()) - set(payload_v2.keys())),
        "config_version": payload_v2.get("config_version"),
    }
    path = _shadow_log_path()
    if path is None:
        return
    try:
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
    except Exception:
        return


def _genai_mode():
    return normalize_mode(os.environ.get("SPARC_GENAI_MODE", "off"))


def _log_genai_shadow_diff(payload):
    if not payload.get("genai_shadow_diff"):
        return
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "mode": payload.get("recommendation_mode"),
        "source": payload.get("genai_source"),
        "genai_error": payload.get("genai_error"),
        "diff": payload.get("genai_shadow_diff"),
        "config_version": payload.get("config_version"),
    }
    path = _shadow_log_path()
    if path is None:
        return
    try:
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
    except Exception:
        return


def _refresh_primary_genai_dependents(payload):
    if payload.get("genai_source") != "gemini" or payload.get("recommendation_mode") != "primary":
        return payload
    if "profile" not in payload or "scores" not in payload:
        return payload

    recommendations = payload.get("recommendations", [])
    bundle = payload.get("bundle_match")
    payload["bundles"] = bundle_recommendations(recommendations)
    payload["product_mapping"] = product_mapping(recommendations, payload["scores"])
    payload["pricing_engine_quote"] = json_safe(price_output_stage(
        payload["profile"],
        payload["scores"],
        recommendations,
        bundle,
    ))
    payload["premium_summary"] = premium_summary(
        recommendations,
        bundle,
        payload.get("global_products", []),
        payload.get("size_bucket"),
    )
    if bundle:
        payload["bundle_only_pricing_quote"] = json_safe(price_output_stage(
            payload["profile"],
            payload["scores"],
            [],
            {
                "name": bundle.get("name"),
                "mandatory_covers": bundle.get("mandatory_covers", []),
                "optional_covers": bundle.get("optional_covers", []),
            },
        ))
    return payload


def _apply_genai_recommendation_mode(payload):
    mode = _genai_mode()
    result = rerank_payload(
        payload,
        mode=mode,
        model_available=gemini_enabled(),
        call_json=call_gemini_json,
    )
    updated = _refresh_primary_genai_dependents(result.payload)
    if mode == "shadow" and updated.get("genai_source") == "gemini":
        _log_genai_shadow_diff(updated)
    return updated


def score(profile):
    if SPARC_ENGINE == "legacy":
        return _apply_genai_recommendation_mode(_legacy_score(profile))
    payload_v2 = _v2_score(profile)
    if SPARC_ENGINE == "shadow":
        payload_legacy = _legacy_score(profile)
        _log_diff(payload_legacy, payload_v2)
        return _apply_genai_recommendation_mode(payload_legacy)
    return _apply_genai_recommendation_mode(payload_v2)


def analyze(raw):
    return score(raw)


def policy_wording_ai_summary(payload, deterministic):
    if not gemini_enabled() or not deterministic.get("ok"):
        return None, "fallback", None

    policy_text = str((payload or {}).get("policy_text") or "")[:12000]
    prompt = f"""
You are an insurance policy wording analyst for Indian startup insurance.
Summarize pasted policy wording against the deterministic SPARC reference.

Rules:
- Return strict JSON only.
- Do not invent coverage, limits, legal advice, or endorsements.
- If a point is not visible in the pasted wording, say it needs manual verification.
- The deterministic exclusions and gaps are the controlling audit source.

Return this JSON shape:
{{
  "plain_english_summary": "3-5 concise sentences",
  "most_important_exclusions": ["..."],
  "coverage_gaps_to_discuss": ["..."],
  "questions_for_underwriter": ["..."],
  "confidence": 0.0
}}

Deterministic comparison:
{json.dumps(deterministic, ensure_ascii=False)[:10000]}

Pasted policy wording:
{policy_text}
"""
    data, err = call_gemini_json(prompt)
    if err or not isinstance(data, dict):
        return None, "fallback", err

    def _list(key):
        value = data.get(key)
        if not isinstance(value, list):
            return []
        return [str(item).strip() for item in value if str(item).strip()][:8]

    try:
        confidence = float(data.get("confidence", 0.0))
    except (TypeError, ValueError):
        confidence = 0.0
    return {
        "plain_english_summary": str(data.get("plain_english_summary") or "").strip(),
        "most_important_exclusions": _list("most_important_exclusions"),
        "coverage_gaps_to_discuss": _list("coverage_gaps_to_discuss"),
        "questions_for_underwriter": _list("questions_for_underwriter"),
        "confidence": max(0.0, min(1.0, confidence)),
    }, "gemini", None


def analyze_policy_wording(payload):
    deterministic = compare_policy_wording(payload or {})
    ai_summary, ai_source, ai_error = policy_wording_ai_summary(payload or {}, deterministic)
    deterministic["genai_source"] = ai_source
    deterministic["genai_error"] = ai_error
    deterministic["genai_summary"] = ai_summary
    return deterministic


def meta():
    sectors = [
        {
            "name": name,
            "emoji": str(data.get("emoji", "")),
            "description": str(data.get("description", "")),
        }
        for name, data in SECTOR_PROFILES.items()
    ]
    return {
        "defaults": DEFAULT_PROFILE,
        "sectors": sectors,
        "subSectorOptions": SUB_SECTOR_OPTIONS,
        "dataHandledOptions": DATA_HANDLED_OPTIONS,
        "regulatoryOptions": REGULATORY_OPTIONS,
        "physicalAssetOptions": PHYSICAL_ASSET_OPTIONS,
        "customerTypeOptions": CUSTOMER_TYPE_OPTIONS,
        "fundingStages": ["Pre-seed", "Seed", "Series A", "Series B+"],
        "operations": ["Digital-only", "Physical-only", "Hybrid"],
        "dataSensitivity": ["Low", "Medium", "High"],
        "holdcoDomiciles": ["India", "DE", "SG", "Cayman", "Flip_pending"],
        "rbiRegistrations": [None, "NBFC", "PA", "PPI", "RIA", "AA"],
        "states": ["Karnataka", "Rajasthan", "Bihar", "Jharkhand", "Telangana", "Maharashtra", "Delhi", "Tamil Nadu", "Gujarat", "Other"],
        "climateZones": ["Low", "Medium", "High", "Extreme"],
        "aiTiers": ["None", "Embedded", "Applied", "Foundational"],
        "geminiEnabled": gemini_enabled(),
        "geminiModel": GEMINI_MODEL,
        "genaiRecommendationMode": _genai_mode(),
        "seedCompanyProfiles": company_profile_count(),
    }


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, format, *args):
        return

    def guess_type(self, path):
        base = super().guess_type(path)
        if isinstance(base, str):
            if base in ("application/javascript", "text/javascript"):
                return "application/javascript; charset=utf-8"
            if base == "text/css":
                return "text/css; charset=utf-8"
            if base and base.startswith("text/html"):
                return "text/html; charset=utf-8"
        return base

    def send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)
        if path == "/api/meta":
            self.send_json(200, meta())
            return
        if path == "/api/health":
            self.send_json(200, {"ok": True})
            return
        if path == "/api/company-profiles":
            query = (params.get("q") or [""])[0]
            name = (params.get("name") or [""])[0]
            if name:
                profile = get_company_profile(name)
                if not profile:
                    self.send_json(404, {"error": "Company profile not found"})
                else:
                    self.send_json(200, {"profile": profile})
                return
            self.send_json(200, {"count": company_profile_count(), "matches": search_company_profiles(query)})
            return
        return super().do_GET()

    def do_POST(self):
        if self.path not in ("/api/analyze", "/api/policy/compare"):
            self.send_json(404, {"error": "Not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            if self.path == "/api/policy/compare":
                result = analyze_policy_wording(payload)
                self.send_json(200 if result.get("ok") else 400, result)
            else:
                self.send_json(200, analyze(payload))
        except Exception as exc:
            self.send_json(500, {"error": str(exc)})


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5174
    log_path = ROOT / "server_runtime.log"
    try:
        server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
        log_path.write_text(f"Startup Shield web app running at http://localhost:{port}\n", encoding="utf-8")
        print(f"Startup Shield web app running at http://localhost:{port}", flush=True)
        server.serve_forever()
    except Exception as exc:
        log_path.write_text(f"Server failed: {exc}\n", encoding="utf-8")
        raise


if __name__ == "__main__":
    main()
