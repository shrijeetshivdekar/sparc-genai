import json
import math
import os
import re
import sqlite3
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import fields
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
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
from competitor_catalog_expanded import get_top5_global  # noqa: E402
from policy_wording import compare_policy_wording  # noqa: E402
from premium_estimator import PREMIUM_FOOTNOTE, estimate_premium, get_size_bucket  # noqa: E402
from pricing_engine import price_output_stage  # noqa: E402
from api.pricing import make_pricing_response  # noqa: E402
from risk_appetite import get_appetite, get_bad_reason  # noqa: E402
from weightage_rationale import MULTIPLIER_RATIONALE, get_score_rationale  # noqa: E402


DB_PATH = Path(os.environ.get(
    "SPARC_DB_PATH",
    str(Path(tempfile.gettempdir()) / "sparc_data.db") if os.environ.get("VERCEL") else str(PROJECT_ROOT / "sparc_data.db"),
))
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_FALLBACK_MODELS = [
    m.strip()
    for m in os.environ.get("GEMINI_FALLBACK_MODELS", "gemini-2.0-flash,gemini-1.5-pro").split(",")
    if m.strip()
]
GEMINI_MAX_TOKENS = int(os.environ.get("GEMINI_MAX_TOKENS", "4096"))
GEMINI_TIMEOUT_SECONDS = int(os.environ.get("GEMINI_TIMEOUT_SECONDS", "30"))
SPARC_ENGINE = os.environ.get("SPARC_ENGINE", "v2")

# Load pitch/objection library once at startup — never sent to Gemini in full
_PITCH_LIBRARY_PATH = ROOT / "pitch_objection_library.json"
try:
    _PITCH_LIBRARY = json.loads(_PITCH_LIBRARY_PATH.read_text(encoding="utf-8"))
except Exception:
    _PITCH_LIBRARY = {}


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
    "startup_name": "",
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


def call_gemini_grounded(prompt, model=None):
    """Call Gemini with Google Search grounding. Returns (parsed_dict_or_None, error_str_or_None)."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None, "GEMINI_API_KEY is not configured."

    _model = model or GEMINI_MODEL
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{_model}:generateContent?key={api_key}"
    )
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "tools": [{"google_search": {}}],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 8192,  # grounded call needs more room than standard calls
        },
    }
    data = json.dumps(payload).encode("utf-8")
    try:
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=GEMINI_TIMEOUT_SECONDS) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            detail = exc.read().decode("utf-8")[:500]
        except Exception:
            detail = str(exc)
        return None, f"HTTP {exc.code}: {detail}"
    except urllib.error.URLError as exc:
        return None, f"Network error: {exc.reason}"
    except TimeoutError:
        return None, "Request timed out."
    except json.JSONDecodeError:
        return None, "Non-JSON response from API."

    candidate = body.get("candidates", [{}])[0]
    finish_reason = candidate.get("finishReason", "")
    parts = candidate.get("content", {}).get("parts", [])
    text = "".join(part.get("text", "") for part in parts)
    usage = body.get("usageMetadata", {})
    print(
        f"[gemini_grounded] tokens — input: {usage.get('promptTokenCount', '?')}, "
        f"output: {usage.get('candidatesTokenCount', '?')}, "
        f"total: {usage.get('totalTokenCount', '?')}",
        flush=True,
    )
    if finish_reason == "MAX_TOKENS":
        return None, f"Gemini response truncated (MAX_TOKENS={GEMINI_MAX_TOKENS})."
    parsed = extract_json_object(text)
    if not isinstance(parsed, dict):
        print(f"[gemini_grounded] Could not parse JSON; finishReason={finish_reason!r}; raw: {text[:500]!r}", flush=True)
        return None, "Gemini grounded response did not contain a valid JSON object."
    return parsed, None


def _build_autofill_prompt(company_name):
    return f"""You are an expert startup analyst. Research "{company_name}" using current public information and return a JSON object with the fields below.

CRITICAL: Use ONLY the exact string values listed for each enum field. Do not paraphrase or invent values.

Return this JSON object filled in for {company_name}:
{{
  "startup_name": "{company_name}",
  "sector": <exactly one of: "Fintech", "Healthtech", "SaaS / Enterprise Software", "Deeptech / AI / Robotics", "Edtech", "D2C / Consumer Brands", "Logistics / Mobility", "Agritech / Foodtech", "Cleantech / Climatetech", "Gaming / Media / Content", "HRtech", "Legaltech", "Proptech", "Spacetech", "Insurtech", "Other">,
  "funding_stage": <exactly one of: "Pre-seed", "Seed", "Series A", "Series B+">,
  "team_size": <integer — full-time employees from latest public info>,
  "operations": <exactly one of: "Digital-only", "Hybrid (online+offline)", "Offline / Physical", "Hardware / IoT", "Marketplace">,
  "data_handled": <array, zero or more from exactly: ["Payments / financial transactions", "Health / medical records", "Personal identity data (KYC / Aadhaar)", "Employee / HR data (payroll, biometrics)", "Minors' / children's data", "Location / GPS tracking data", "Intellectual property / source code", "Customer behavioural / usage data", "Physical inventory / goods", "Sensitive personal data (DPDP Act)", "None of the above"]>,
  "regulatory": <array, zero or more from exactly: ["RBI / SEBI / IRDAI licensed", "FSSAI / food safety", "CDSCO / medical devices", "DPDP Act obligations", "DGCA / drone operations", "IT Act / CERT-In obligations", "Labour Codes / gig worker regulations", "BIS / QCO product certification", "NMC / telemedicine regulations", "MV Act / transport regulations", "SEBI BRSR / ESG reporting", "Competition Act / CCI", "EPR / environmental compliance", "None / minimal"]>,
  "physical_assets": <array, zero or more from exactly: ["Office / coworking space", "Warehouse / fulfilment centre", "Manufacturing plant / factory", "Lab / R&D equipment", "Medical devices / diagnostic equipment", "Vehicles / delivery fleet", "Drones / UAV equipment", "Kitchen / food processing", "Cold chain / refrigeration", "Solar / clean energy infrastructure", "Retail stores / kiosks", "Data centre / server room", "None - fully cloud"]>,
  "ai_in_product": <true or false>,
  "has_investors": <"Yes" or "No">,
  "annual_revenue_cr": <number — annual revenue in INR crores, best estimate from public sources, 0 if unknown>,
  "healthcare_operations": <true or false>,
  "payment_or_card_program": <true or false>,
  "contact_email": <best available public email — try in order: (1) founder/CEO email if publicly listed, (2) official contact like contact@, info@, hello@ + company domain, (3) construct from known pattern e.g. firstname@domain.com — return null only if nothing can be reasonably inferred>,
  "product_description": <one sentence max 160 chars — what the company does, where it operates, at what scale>,
  "biggest_fear": <max 120 chars — 2-3 top risk concerns this company likely faces, comma-separated, e.g. "Cyber attacks, Data privacy breaches, Regulatory penalties">
}}

Return ONLY the JSON object. No explanation, no markdown fences."""


_VERIFIED_JSON_PATH = ROOT / "startup_shield_web" / "verified_companies.json"


def _persist_verified_profile(profile: dict) -> None:
    """Append or update the profile in verified_companies.json and live COMPANY_PROFILES."""
    try:
        name = profile.get("startup_name", "").strip()
        if not name:
            return
        # Build a compact verified record from the autofilled profile
        record = {
            "startup_name": name,
            "sector": profile.get("sector", ""),
            "funding_stage": profile.get("funding_stage", ""),
            "team_size": profile.get("team_size", 0),
            "annual_revenue_cr": profile.get("annual_revenue_cr", 0),
            "operations": profile.get("operations", ""),
            "data_handled": profile.get("data_handled", []),
            "regulatory": profile.get("regulatory", []),
            "physical_assets": profile.get("physical_assets", []),
            "ai_in_product": bool(profile.get("ai_in_product", False)),
            "has_investors": profile.get("has_investors", "Unknown"),
            "healthcare_operations": bool(profile.get("healthcare_operations", False)),
            "payment_or_card_program": bool(profile.get("payment_or_card_program", False)),
            "contact_email": profile.get("contact_email", ""),
            "product_description": profile.get("product_description", ""),
            "biggest_fear": profile.get("biggest_fear", ""),
            "profile_source": "verified",
        }
        # Load existing, replace if name exists, else append
        json_path = ROOT / "verified_companies.json"
        existing: list = json.loads(json_path.read_text(encoding="utf-8")) if json_path.exists() else []
        updated = [e for e in existing if e.get("startup_name", "").strip().lower() != name.lower()]
        updated.append(record)
        json_path.write_text(json.dumps(updated, indent=None, ensure_ascii=False), encoding="utf-8")
        # Also update in-memory COMPANY_PROFILES and invalidate pipeline cache
        from company_profiles import COMPANY_PROFILES as _CP
        _CP[name] = record
        global _pipeline_cache
        _pipeline_cache = None
        print(f"[autofill] Persisted '{name}' to verified_companies.json ({len(updated)} total)", flush=True)
    except Exception as exc:
        print(f"[autofill] Failed to persist profile: {exc}", flush=True)


_CAPACITY_ERRORS = ("503", "429", "unavailable", "UNAVAILABLE", "high demand", "quota", "rate", "timed out", "timeout")

def autofill_and_analyze(company_name):
    if not gemini_enabled():
        return {"error": "Gemini API key not configured. Cannot auto-profile."}

    prompt = _build_autofill_prompt(company_name)

    # On Vercel, serverless functions have a 10s hard limit on the hobby plan.
    # Google Search grounding adds 8-15s of latency, blowing the budget.
    # Skip grounding on Vercel and go straight to the fast ungrounded call.
    on_vercel = bool(os.environ.get("VERCEL"))

    autofilled, err = None, None
    if not on_vercel:
        models_to_try = [GEMINI_MODEL] + GEMINI_FALLBACK_MODELS
        for i, model in enumerate(models_to_try):
            autofilled, err = call_gemini_grounded(prompt, model=model)
            if autofilled is not None:
                if i > 0:
                    print(f"[autofill] Succeeded with fallback model '{model}' after primary was busy.", flush=True)
                break
            is_capacity_error = err and any(kw in err for kw in _CAPACITY_ERRORS)
            if not is_capacity_error:
                break  # hard error (auth, parse, network) — fallbacks won't help
            if i < len(models_to_try) - 1:
                print(f"[autofill] '{model}' busy ({err[:80]}…); trying '{models_to_try[i+1]}'.", flush=True)

    if not isinstance(autofilled, dict):
        source = "ungrounded (Vercel fast-path)" if on_vercel else f"ungrounded fallback (grounded err: {err})"
        print(f"[autofill] Using {source}.", flush=True)
        autofilled, err = call_gemini_json(prompt)
        if isinstance(autofilled, dict):
            print("[autofill] Ungrounded inference succeeded.", flush=True)
        else:
            return {"error": err or "Auto-profile failed — all models unavailable."}

    profile_data = {**DEFAULT_PROFILE, **{k: v for k, v in autofilled.items() if v is not None}}

    for int_field in ("team_size", "fleet_count"):
        if int_field in profile_data:
            try:
                profile_data[int_field] = int(profile_data[int_field])
            except (TypeError, ValueError):
                pass
    for float_field in ("annual_revenue_cr", "total_insurable_asset_value_cr", "gross_profit_cr",
                        "investor_cn_hk_pct", "b2b_pct", "gig_headcount_pct"):
        if float_field in profile_data:
            try:
                profile_data[float_field] = float(profile_data[float_field])
            except (TypeError, ValueError):
                pass

    _persist_verified_profile(profile_data)

    result = analyze(profile_data)
    result["autofilled_fields"] = list(autofilled.keys())
    result["autofill_warning"] = "Pre-filled from public sources via Gemini + Google Search. Verify before underwriting."
    return result


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


def _compact_personalization_text(value, limit=220):
    text = _non_empty_profile_value(value)
    if not text:
        return ""
    text = re.sub(r"\s+", " ", str(text)).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def _profile_personalization_points(profile, product_name=None):
    """Copy-only context points for outreach and email preview; never used for scoring."""
    profile = profile or {}
    company = profile.get("startup_name") or "this startup"
    product_desc = _compact_personalization_text(profile.get("product_description"), 180)
    founder_concern = _compact_personalization_text(profile.get("biggest_fear"), 180)
    points = []
    if product_desc:
        points.append(f"What {company} does: {product_desc}")
    if founder_concern:
        points.append(f"Founder concern: {founder_concern}")
    if product_name and (product_desc or founder_concern):
        concern_ref = (founder_concern or "the operating risks described above").rstrip(". ")
        points.append(f"Why {product_name} is relevant: it connects the recommendation to {concern_ref}.")
    return points[:3]


def _plain_personalization_block(profile, product_name=None):
    points = _profile_personalization_points(profile, product_name)
    if not points:
        return ""
    company = (profile or {}).get("startup_name") or "this startup"
    return (
        f"Why this is relevant to {company}:\n"
        + "\n".join(f"- {point}" for point in points)
        + "\n\n"
    )


def profile_context_for_why(profile):
    """Compact only useful entered fields so GenAI copy stays specific."""
    fields_to_include = [
        ("What the company does", "product_description"),
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
        ("Founder concern", "biggest_fear"),
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
    "property_fire": "Protects premises, stock, furniture, fixtures, and business contents from fire and allied perils.",
    "burglary": "Protects inventory and business assets against burglary or theft from insured premises.",
    "money_insurance": "Covers loss of cash or money in transit where collections or retail handling exists.",
    "comprehensive_general_liability": "Covers third-party bodily injury, property damage, and personal injury claims.",
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
    product_desc = _compact_personalization_text(profile.get("product_description"), 180)
    founder_concern = _compact_personalization_text(profile.get("biggest_fear"), 180)

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
        f"- What the company does: {product_desc or 'not provided'}\n"
        f"- Founder concern: {founder_concern or 'not provided'}\n\n"
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
        "bundle": f"<one punchy stat-backed sentence on why {bundle_name} matters for this startup>",
        "bundle_covers": {
            key: f"<one punchy stat-backed sentence on why {key} matters inside {bundle_name}>"
            for key in fallback["bundle_covers"]
        },
        "companion_bundle": (
            f"<one punchy stat-backed sentence on why {companion.get('name')} should be reviewed alongside Group Safeguard>"
            if companion.get("name")
            else None
        ),
        "companion_covers": {
            key: f"<one punchy stat-backed sentence on why {key} matters inside {companion.get('name', 'the companion bundle')}>"
            for key in fallback["companion_covers"]
        },
        "products": {
            p["key"]: f"<one punchy stat-backed sentence on why {p['name']} matters>"
            for p in products
        },
    }
    template_str = json.dumps(template, indent=2, ensure_ascii=False)

    prompt = (
        "You are a concise insurance risk analyst for Indian startups. Fill the JSON template with "
        "one-sentence explanations that make each insurance cover feel urgent and relevant to a founder or RM.\n\n"
        f"Startup context:\n{profile_context_for_why(profile)}\n\n"
        "Rules:\n"
        "- Keep the exact JSON shape and all keys exactly as provided; do not add or remove keys.\n"
        "- Each non-null value must be exactly ONE sentence: engaging, specific to this startup, and anchored to a real business risk or stat where possible.\n"
        "- Weave in the startup's sector, stage, team size, data exposure, regulatory context, actual product description, or founder concern when supplied.\n"
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
    product_desc = _compact_personalization_text(profile.get("product_description"), 220)
    founder_concern = _compact_personalization_text(profile.get("biggest_fear"), 220)

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
- What the company does: {product_desc or "not provided"}
- Founder concern: {founder_concern or "not provided"}
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

Rules: no bullet points inside string values, no markdown, no technical terms like TAM/margin/multiplier, use the product description and founder concern when supplied, write as if explaining to a smart non-finance person."""

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


def _outreach_cover_label(key):
    labels = {
        "BHARAT_SOOKSHMA": "Bharat Sookshma Udyam Suraksha",
        "CYBER": "Cyber liability",
        "D_AND_O": "Directors and officers liability",
        "PI_TECH_EO": "Professional indemnity / Tech E&O",
        "CGL_I_ELITE": "Comprehensive general liability",
        "PUBLIC_LIABILITY": "Public liability",
        "EMPLOYERS_COMP": "Employees compensation",
        "EMPLOYMENT_PRACTICES": "Employment practices liability",
        "CRIME_FIDELITY": "Crime / fidelity",
        "GROUP_HEALTH": "Group health",
        "GROUP_PA": "Group personal accident",
        "PROPERTY_ALL_RISK": "Property all risk",
        "BUSINESS_INTERRUPTION": "Business interruption",
        "MACHINERY_BREAKDOWN": "Machinery breakdown",
        "ELECTRONIC_EQUIPMENT": "Electronic equipment",
        "PRODUCT_LIABILITY": "Product liability",
        "MARINE_CARGO": "Marine cargo",
        "SURETY": "Surety / contract bonds",
        "Drone_RPAS": "Drone RPAS",
        "property_fire": "Property fire and allied perils",
        "burglary": "Burglary and theft",
        "business_interruption": "Business interruption",
        "cyber_liability": "Cyber liability",
        "product_liability": "Product liability",
        "money_insurance": "Money insurance",
        "public_liability": "Public liability",
        "employees_comp": "Employees compensation",
        "machinery_breakdown": "Machinery breakdown",
        "electronic_equipment": "Electronic equipment",
        "comprehensive_general_liability": "Comprehensive general liability",
        "dno_liability": "Directors and officers liability",
        "professional_indemnity": "Professional indemnity / Tech E&O",
        "crime_fidelity": "Crime / fidelity",
        "marine_transit": "Marine cargo",
    }
    if key in labels:
        return labels[key]
    return str(key or "").replace("_", " ").replace("-", " ").title()


def _outreach_top_risks(scores, limit=3):
    return sorted((scores or {}).items(), key=lambda item: item[1], reverse=True)[:limit]


def _outreach_cover_facts(bundle):
    facts = []
    for key in _bundle_cover_keys(bundle):
        expanded = _outreach_expanded_component_facts(key)
        if expanded:
            facts.extend(expanded)
            continue
        facts.append({
            "key": key,
            "label": _outreach_cover_label(key),
            "summary": _fallback_cover_reason(bundle, key),
        })
    return facts


def _outreach_expanded_component_facts(key):
    expansions = {
        "BHARAT_SOOKSHMA": [
            {
                "key": "property_fire",
                "label": "Property fire and allied perils",
                "summary": "Protects the insured premises, contents, stock, furniture, fixtures, and fittings from fire and allied physical damage events.",
            },
            {
                "key": "stock_inventory",
                "label": "Stock and inventory protection",
                "summary": "Covers finished goods, raw materials, and packaging kept at the insured location, which is critical for a D2C brand.",
            },
            {
                "key": "plant_equipment",
                "label": "Plant, machinery, and equipment",
                "summary": "Protects operating equipment and business assets that would be expensive to replace after insured damage.",
            },
            {
                "key": "burglary",
                "label": "Burglary and theft extension",
                "summary": "Relevant where inventory or equipment is stored in offices, warehouses, or fulfilment locations.",
            },
            {
                "key": "business_interruption",
                "label": "Business interruption add-on",
                "summary": "Helps protect gross profit and continuing expenses if an insured property event disrupts fulfilment or sales.",
            },
        ],
        "Bharat_Sookshma": [
            {
                "key": "property_fire",
                "label": "Property fire and allied perils",
                "summary": "Protects the insured premises, contents, stock, furniture, fixtures, and fittings from fire and allied physical damage events.",
            },
            {
                "key": "stock_inventory",
                "label": "Stock and inventory protection",
                "summary": "Covers finished goods, raw materials, and packaging kept at the insured location, which is critical for a D2C brand.",
            },
            {
                "key": "plant_equipment",
                "label": "Plant, machinery, and equipment",
                "summary": "Protects operating equipment and business assets that would be expensive to replace after insured damage.",
            },
            {
                "key": "burglary",
                "label": "Burglary and theft extension",
                "summary": "Relevant where inventory or equipment is stored in offices, warehouses, or fulfilment locations.",
            },
            {
                "key": "business_interruption",
                "label": "Business interruption add-on",
                "summary": "Helps protect gross profit and continuing expenses if an insured property event disrupts fulfilment or sales.",
            },
        ],
    }
    return expansions.get(key) or expansions.get(str(key or "").upper())


def _outreach_fit_summary(profile, scores, bundle, cover_facts):
    company = (profile or {}).get("startup_name") or "this startup"
    sector = (profile or {}).get("sector") or "startup"
    stage = (profile or {}).get("funding_stage") or "current stage"
    risks = ", ".join(name for name, _ in _outreach_top_risks(scores))
    subproduct_reasons = _outreach_subproduct_fit_summary(cover_facts)
    if bundle:
        return (
            f"{bundle.get('name')} is relevant for {company} because its {sector} profile at {stage} "
            f"shows {risks or 'material operating risk'}. The fit comes from the bundle sub-products: "
            f"{subproduct_reasons or 'the included covers map to the startup exposures'}."
        )
    return (
        f"This cover fits {company} because its {sector} profile at {stage} "
        f"shows {risks or 'material operating risk'}."
    )


def _outreach_subproduct_fit_summary(cover_facts, max_items=4):
    parts = []
    for fact in (cover_facts or [])[:max_items]:
        label = fact.get("label")
        summary = _outreach_short_summary(fact.get("summary"))
        if label and summary:
            parts.append(f"{label} for {summary}")
        elif label:
            parts.append(label)
    remaining = len(cover_facts or []) - len(parts)
    if remaining > 0:
        parts.append(f"{remaining} additional cover{'s' if remaining != 1 else ''} for the remaining operating exposures")
    return "; ".join(parts)


def _outreach_short_summary(text, limit=86):
    value = str(text or "").strip().rstrip(".")
    if not value:
        return ""
    first_sentence = value.split(". ", 1)[0].strip()
    if len(first_sentence) <= limit:
        return first_sentence[:1].lower() + first_sentence[1:]
    return first_sentence[:limit].rsplit(" ", 1)[0].strip().lower() + "..."


def _format_cover_lines(cover_facts, max_items=8):
    lines = []
    for fact in cover_facts[:max_items]:
        lines.append(f"- {fact['label']}: {fact['summary']}")
    remaining = len(cover_facts) - len(lines)
    if remaining > 0:
        names = ", ".join(fact["label"] for fact in cover_facts[max_items:])
        lines.append(f"- Also included: {names}")
    return "\n".join(lines)


def _outreach_context(profile, scores, recommendations, bundle, size_bucket=None):
    bundle_cover_facts = _outreach_cover_facts(bundle) if bundle else []
    products = []
    if bundle:
        products.append({
            "key": "bundle",
            "name": bundle.get("name") or "Bundle recommendation",
            "fit_summary": _outreach_fit_summary(profile, scores, bundle, bundle_cover_facts),
            "coverage_facts": bundle_cover_facts,
            "description": bundle.get("description") or "",
        })
    for product in (recommendations or [])[:5]:
        key = product.get("key")
        name = product.get("name") or key
        if not key or not name:
            continue
        summary = product.get("what_it_covers") or product.get("nudge") or ""
        products.append({
            "key": key,
            "name": name,
            "fit_summary": _outreach_fit_summary(profile, scores, None, []),
            "coverage_facts": [{"key": key, "label": name, "summary": summary}] if summary else [],
            "description": summary,
        })
    return {
        "company": (profile or {}).get("startup_name", ""),
        "sector": (profile or {}).get("sector", ""),
        "stage": (profile or {}).get("funding_stage", ""),
        "team_size": (profile or {}).get("team_size", ""),
        "operations": (profile or {}).get("operations", ""),
        "data_sensitivity": (profile or {}).get("data_sensitivity", ""),
        "size_bucket": size_bucket,
        "top_risks": [name for name, _ in _outreach_top_risks(scores)],
        "products": [p for p in products[:6] if p.get("key") and p.get("name")],
    }


def _outreach_products_for_drafts(recommendations, bundle):
    products = []
    seen = set()

    def norm(value):
        return re.sub(r"[^a-z0-9]+", "", str(value or "").lower())

    def add_product(product, fallback_key="product"):
        if not isinstance(product, dict):
            return
        name = product.get("name") or product.get("key")
        if not name:
            return
        key = str(product.get("key") or fallback_key or name).strip()
        dedupe_key = norm(name) or norm(key)
        if not dedupe_key or dedupe_key in seen:
            return
        seen.add(dedupe_key)
        products.append({
            **product,
            "key": key,
            "name": name,
        })

    if bundle:
        add_product({
            "key": "bundle",
            "name": bundle.get("name") or "Bundle recommendation",
            "nudge": bundle.get("description", ""),
            "what_it_covers": bundle.get("description", ""),
        }, "bundle")

    for index, product in enumerate(recommendations or [], start=1):
        add_product(product, f"recommended_{index}")

    return products


def fallback_outreach_prompts(profile, scores, recommendations, bundle):
    contacts = load_contacts()
    top_scores = sorted(scores.items(), key=lambda item: item[1], reverse=True)[:3]
    risk_names = ", ".join(name for name, _ in top_scores)
    products = _outreach_products_for_drafts(recommendations, bundle)
    output = {}
    for product in products:
        key = product.get("key", "bundle")
        name = product.get("name", key)
        nudge = product.get("nudge") or product.get("what_it_covers") or ""
        personalized_points = _profile_personalization_points(profile, name)
        personalized_block = _plain_personalization_block(profile, name)
        contact_block = (
            f"Warm regards,\n{contacts.get('RM_NAME')}\n"
            f"{contacts.get('RM_PHONE')} | {contacts.get('RM_EMAIL')}\n"
            f"{contacts.get('RM_OFFICE')}"
        )
        output[key] = {
            "email_subject": f"A tailored coverage recommendation for {profile.get('startup_name')}",
            "email_body": (
                f"Dear {profile.get('startup_name')} team,\n\n"
                f"Greetings from ICICI Lombard!\n\n"
                f"Our expert underwriters have been closely studying risk profiles across the "
                f"{profile.get('sector')} landscape, and {profile.get('startup_name')} stood out. "
                f"Based on their assessment, your most significant risk dimensions — {risk_names} — "
                f"deserve proactive, well-structured coverage, especially at your current stage of growth.\n\n"
                f"We'd love to introduce you to {name}. {nudge} "
                f"It is thoughtfully designed for companies like yours and we believe it can give "
                f"your team real peace of mind as you scale.\n\n"
                f"We'd be delighted to walk you through how {name} fits your journey — no pressure, "
                f"just a friendly conversation at a time that works for you.\n\n"
                f"{personalized_block}"
                f"{contact_block}"
            ),
            "whatsapp": (
                f"Hi {profile.get('startup_name')} team! Greetings from ICICI Lombard. "
                f"Our underwriters flagged {risk_names} as key exposures for your stage. "
                f"{name} looks like a strong fit — happy to walk you through it whenever convenient. "
                f"{contacts.get('RM_NAME')} | {contacts.get('RM_PHONE')}"
            ),
            "personalized_points": personalized_points,
            "email_html_data": {
                "company": profile.get("startup_name", ""),
                "industry": profile.get("sector", ""),
                "product_name": name,
                "risk_names": [r for r, _ in top_scores[:3]],
                "body_para": nudge,
                "personalized_points": personalized_points,
                "rm_name": contacts.get("RM_NAME", "{{RM_NAME}}"),
                "rm_phone": contacts.get("RM_PHONE", "{{RM_PHONE}}"),
                "rm_email": contacts.get("RM_EMAIL", "{{RM_EMAIL}}"),
            },
        }
    return output


def outreach_prompt_payload(profile, scores, recommendations, bundle, size_bucket):
    contacts = load_contacts()
    top_scores = sorted(scores.items(), key=lambda item: item[1], reverse=True)[:3]
    products = _outreach_products_for_drafts(recommendations, bundle)
    product_lines = "\n".join(f"- {product['key']}: {product['name']}" for product in products)
    top_risk_names = ", ".join(name for name, _ in top_scores)
    product_desc = _compact_personalization_text(profile.get("product_description"), 220)
    founder_concern = _compact_personalization_text(profile.get("biggest_fear"), 220)
    profile_highlights = [
        f"Customer types: {', '.join(profile.get('customer_type') or ['not specified'])}",
        f"Data handled: {', '.join(profile.get('data_handled') or ['not specified'])}",
        f"Regulatory exposures: {', '.join(profile.get('regulatory') or ['not specified'])}",
        f"Operations: {profile.get('operations')}; data sensitivity: {profile.get('data_sensitivity')}",
        f"Size bucket: {size_bucket}",
    ]
    if product_desc:
        profile_highlights.insert(0, f"What the company does: {product_desc}")
    if founder_concern:
        profile_highlights.insert(1 if product_desc else 0, f"Founder concern: {founder_concern}")
    return f"""
You are a warm, knowledgeable ICICI Lombard Relationship Manager writing personalised outreach for
{profile.get('startup_name')} ({profile.get('sector')}, {profile.get('funding_stage')}, {profile.get('team_size')} people).

Their leading risk dimensions (mention by name only, NO scores or numbers): {top_risk_names}.
Their profile highlights:
{chr(10).join('- ' + item for item in profile_highlights)}
TONE RULES (strictly follow):
- Always open with: "Dear [Company] team," then "Greetings from ICICI Lombard!"
- Attribute risk insights to "our expert underwriters" — never cite numerical scores.
- Be warm, friendly, and gently persuasive — like a trusted advisor, not a salesperson.
- End emails with "Warm regards," and the contact block.
- Preserve the greeting, core body flow, soft CTA, and signature structure.
- Add a short final section near the end of the email body, just before the signature, titled "Why this is relevant to {profile.get('startup_name')}" when product description or founder concern is provided.
- That final section should contain 2-3 concise points: one from the product description when supplied, one from the founder concern when supplied, and one connecting the product to the stated concern.
- Also return the same points in personalized_points. Never alter product names or JSON keys.
- WhatsApp: casual, friendly, under 40 words.

Generate outreach drafts for the following {len(products)} products. For EACH product:
1. EMAIL VERSION: subject line + body in 100-130 words. Open with the greeting above. Mention risk dimensions by name. Close with the soft CTA, final personalization section when applicable, and contact block.
2. WHATSAPP VERSION: 30-40 words, friendly tone, same CTA.

Products to cover:
{product_lines}

Output ONLY valid JSON in this exact shape:
{{
  "product_key": {{
    "email_subject": "...",
    "email_body": "...",
    "whatsapp": "...",
    "personalized_points": ["...", "..."]
  }}
}}

Contact block to use:
Warm regards,
{contacts.get('RM_NAME')}
{contacts.get('RM_PHONE')} | {contacts.get('RM_EMAIL')}
{contacts.get('RM_OFFICE')}

Soft CTA text:
We'd be delighted to walk you through how [Product] fits your journey — no pressure, just a friendly conversation at a time that works for you.

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
        raw_points = item.get("personalized_points")
        if isinstance(raw_points, list):
            points = [_compact_personalization_text(point, 180) for point in raw_points]
            points = [point for point in points if point and point != "..."]
        else:
            points = fallback_item.get("personalized_points") or []
        if not points:
            points = fallback_item.get("personalized_points") or []
        html_data = dict(fallback_item.get("email_html_data") or {})
        html_data["personalized_points"] = points[:3]
        normalized[key] = {
            "email_subject": subject,
            "email_body": body,
            "whatsapp": whatsapp,
            "personalized_points": points[:3],
            "email_html_data": html_data,
        }
    return normalized, "gemini"


def outreach_prompts(profile, scores, recommendations, bundle, size_bucket):
    if not gemini_enabled():
        return fallback_outreach_prompts(profile, scores, recommendations, bundle), "fallback", None

    prompt = outreach_prompt_payload(profile, scores, recommendations, bundle, size_bucket)
    raw, error = call_gemini_json(prompt)
    prompts, source = normalize_outreach_response(raw, profile, scores, recommendations, bundle)
    return prompts, source, error


def _get_pitch_library_entry(bundle_match):
    """Return the matching library entry for the recommended bundle or None.
    Supports both schema versions:
      v1 (old): product_type.bundle / product_type.standalone
      v2 (new): bundle / standalone at root, shared_objection_library at root
    """
    import re as _re
    if not _PITCH_LIBRARY or not bundle_match:
        return None
    bundle_map = (
        _PITCH_LIBRARY.get("bundle")
        or _PITCH_LIBRARY.get("product_type", {}).get("bundle", {})
    )

    def _slug(s):
        s = _re.sub(r'\([^)]*\)', '', s or "")           # drop "(CAR)", "(EAR)" etc.
        s = s.replace('_', ' ')                           # underscores → spaces so \b fires on lib keys too
        s = _re.sub(r'\b(insurance|policy|cover|bundle|package|plan)\b', '', s, flags=_re.I)
        s = _re.sub(r'[^a-z0-9]+', '_', s.lower())
        s = _re.sub(r'_+', '_', s)                       # collapse consecutive underscores
        return s.strip('_')

    candidate = _slug(bundle_match.get("key") or bundle_match.get("name") or "")
    for lib_key, entry in bundle_map.items():
        norm_key = _slug(lib_key)
        if norm_key == candidate or norm_key in candidate or candidate in norm_key:
            return entry
    return None


def _resolve_objections(lib_entry):
    """Resolve objection IDs through shared_objection_library (v2 schema),
    or return raw objects (v1 schema). Returns up to 3 full objection dicts."""
    if not lib_entry:
        return []
    raw = lib_entry.get("objections", [])[:3]
    if not raw:
        return []
    # v2: list of string IDs
    if isinstance(raw[0], str):
        shared = _PITCH_LIBRARY.get("shared_objection_library", {})
        return [shared[k] for k in raw if k in shared]
    # v1: list of dicts
    return raw


def build_pitch_bullets(profile, bundle_match, scores, pricing_quote):
    """Return 3 consequence-first, company-specific pitch bullets. Zero tokens."""
    company    = profile.get("startup_name", "This company")
    sector     = profile.get("sector", "your sector")
    stage      = profile.get("funding_stage", "this stage")
    team       = int(profile.get("team_size", 0) or 0)
    records    = float(profile.get("data_records_lakhs", 0) or 0)
    revenue    = float(profile.get("revenue_cr", 0) or 0)
    regs       = profile.get("regulatory", []) or []
    data_types = profile.get("data_handled", []) or []
    b2b_pct    = int(profile.get("b2b_pct", 0) or 0)
    payment    = bool(profile.get("payment_or_card_program", False))
    ai_prod    = bool(profile.get("ai_in_product", False))
    health_ops = bool(profile.get("healthcare_operations", False))
    export_eu  = float(profile.get("export_eu_pct", 0) or 0)
    operations = profile.get("operations", "") or ""
    physical   = profile.get("physical_assets", "none") or "none"
    cust_type  = profile.get("customer_type", []) or []
    biz_model  = profile.get("business_model", "") or ""

    top_risks = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    risk1_key = top_risks[0][0] if top_risks else ""
    risk2_key = top_risks[1][0] if len(top_risks) > 1 else ""

    mandatory = (bundle_match or {}).get("mandatory_covers", []) or []
    optional  = (bundle_match or {}).get("optional_covers",  []) or []

    cover_labels = [_outreach_cover_label(k) for k in mandatory[:3]]
    founder_concern = _compact_personalization_text(profile.get("biggest_fear"), 180)
    product_desc = _compact_personalization_text(profile.get("product_description"), 140)

    is_early      = stage in ("Pre-seed", "Seed")
    is_growth     = stage == "Series A"
    is_late       = stage == "Series B+"
    has_payment   = payment or "payment_data" in data_types
    has_pii       = "PII" in data_types
    has_health    = health_ops or "health_data" in data_types
    is_b2b        = b2b_pct >= 50 or "B2B" in biz_model or any(c in ("SME", "enterprise", "B2B") for c in cust_type)
    is_physical   = "Physical" in operations or physical not in ("none", "", "no", "n/a")

    def _rl(key): return key.lower()

    def _risk_bucket(key):
        k = _rl(key)
        if any(w in k for w in ("cyber", "data", "privacy", "breach")):
            return "cyber"
        if any(w in k for w in ("d&o", "director", "officer", "governance")):
            return "dno"
        if any(w in k for w in ("pi", "professional", "tech e&o", "error", "omission", "indemnity")):
            return "pi"
        if any(w in k for w in ("employ", "epl", "hr", "workplace")):
            return "epl"
        if any(w in k for w in ("product", "recall", "defect")):
            return "product"
        if any(w in k for w in ("property", "fire", "asset", "machinery")):
            return "property"
        if any(w in k for w in ("crime", "fraud", "fidelity", "theft")):
            return "crime"
        if any(w in k for w in ("cargo", "marine", "transit", "logistics")):
            return "cargo"
        return "other"

    r1 = _risk_bucket(risk1_key)
    r2 = _risk_bucket(risk2_key)

    records_str = f"{int(records * 10):,}K+" if records else ""
    rev_str     = f"Rs. {int(revenue):,} Cr" if revenue else ""
    team_str    = f"{team:,}" if team else ""

    # ── BULLET 1: what's exposed and what happens without cover ─────────────────
    if r1 == "cyber" or r2 == "cyber":
        if has_payment and "RBI" in regs:
            bullet1 = (
                f"{company} processes payments -- without Cyber cover, a breach triggers "
                f"mandatory RBI/CERT-In notification, card network penalties, and customer "
                f"litigation with zero insurance backstop."
            )
        elif has_payment:
            bullet1 = (
                f"{company} runs a payment programme -- a PCI-DSS incident without Cyber cover "
                f"means forensics, card network fines, and class-action exposure all land on the balance sheet."
            )
        elif has_health:
            bullet1 = (
                f"{company} holds health records -- a breach without Cyber cover triggers DPDP "
                f"enforcement, patient litigation, and reputational collapse; health data breaches "
                f"carry the highest per-record cost under Indian law."
            )
        elif records:
            bullet1 = (
                f"{company} carries {records_str} personal records; without Cyber cover "
                f"a single breach means DPDP penalties (up to Rs. 250 Cr), notification costs, "
                f"and third-party claims hit the P&L directly."
            )
        else:
            bullet1 = (
                f"{sector} businesses without Cyber cover average 90+ days of operational disruption "
                f"per incident -- {company} has no transfer mechanism for that exposure today."
            )

    elif r1 == "dno" or r2 == "dno":
        if is_late:
            bullet1 = (
                f"At {stage}, investor disputes, SEBI/MCA enforcement, and shareholder actions "
                f"are personal liability for {company}'s directors -- D&O is the only legal transfer "
                f"mechanism, and it's absent today."
            )
        elif is_growth:
            bullet1 = (
                f"Series A boards face institutional investor scrutiny on every major decision; "
                f"without D&O, {company}'s founders carry personal liability if an investor "
                f"challenges a governance call in court."
            )
        else:
            bullet1 = (
                f"Without D&O in place, {company}'s next term sheet will require it as a closing "
                f"condition -- arriving uninsured at due diligence adds weeks of delay and "
                f"re-negotiation at a critical fundraising moment."
            )

    elif r1 == "pi" or r2 == "pi":
        if is_b2b and ai_prod:
            bullet1 = (
                f"{company} deploys AI in a B2B context -- without PI / Tech E&O, an AI model "
                f"error that causes client financial loss is an uninsured indemnity clause "
                f"waiting to be triggered."
            )
        elif is_b2b:
            bullet1 = (
                f"{company}'s B2B contracts carry indemnity clauses; without Professional "
                f"Indemnity / Tech E&O, a software failure or service dispute becomes an "
                f"uninsured court event with no defence budget."
            )
        else:
            bullet1 = (
                f"Without PI / Tech E&O, a platform error or service dispute at {company} "
                f"goes to court with the founder's personal assets as the only backstop."
            )

    elif r1 == "product" or r2 == "product":
        bullet1 = (
            f"Without Product Liability cover, a single defective-item claim or recall "
            f"at {company} freezes operations and triggers consumer-forum litigation "
            f"that runs 18-24 months with no insurer defending."
        )

    elif r1 == "epl" or r2 == "epl":
        if team >= 200:
            bullet1 = (
                f"With {team_str} employees, {company} faces statistical probability of "
                f"an employment dispute; without EPL cover, settlements and legal costs "
                f"are fully uninsured P&L events."
            )
        else:
            bullet1 = (
                f"Employment disputes are the fastest-growing liability category in {sector}; "
                f"without EPL cover, {company} absorbs settlements and legal fees directly."
            )

    elif r1 == "property" and is_physical:
        asset_word = physical if physical not in ("none", "") else "physical assets"
        bullet1 = (
            f"{company} operates {asset_word}; without Property cover, a fire, flood, "
            f"or equipment failure shuts operations with no recovery mechanism -- "
            f"business interruption costs typically exceed the asset loss."
        )

    elif r1 == "crime":
        bullet1 = (
            f"Internal fraud and vendor collusion are the leading undetected loss in "
            f"{sector} businesses at this scale; without Crime / Fidelity cover, "
            f"{company} absorbs 100% of any discovered fraud."
        )

    else:
        # Sector-aware fallback — use profile signals rather than ambiguous risk key names
        sec_l = sector.lower()
        if "fssai" in regs or any(w in sec_l for w in ("food", "fmcg", "d2c", "consumer", "brand", "agri")):
            bullet1 = (
                f"A product recall or consumer-forum claim without Product Liability cover "
                f"freezes {company}'s operations; FSSAI enforcement can compound the exposure "
                f"with regulatory penalties on top of civil claims."
            )
        elif any(w in sec_l for w in ("manufactur", "hardware", "industrial")):
            asset_word = physical if physical not in ("none", "") else "production assets"
            bullet1 = (
                f"Without Property and Product Liability cover, a machinery failure or "
                f"defective batch at {company} means uninsured downtime plus customer claims -- "
                f"manufacturing incidents average 3-6 months of disrupted revenue."
            )
        elif any(w in sec_l for w in ("logistics", "transport", "supply", "cargo", "fleet")):
            bullet1 = (
                f"Uninsured in-transit cargo loss at {company} hits the P&L directly; "
                f"without Marine Cargo and liability cover, a single lost or damaged consignment "
                f"opens both shipper claims and third-party liability."
            )
        elif any(w in sec_l for w in ("saas", "software", "tech", "platform", "developer")):
            bullet1 = (
                f"Without PI / Tech E&O, a platform outage or API failure at {company} "
                f"that causes client financial loss becomes an uninsured court event -- "
                f"B2B indemnity clauses activate faster than founders expect."
            )
        elif is_physical and physical not in ("none", ""):
            bullet1 = (
                f"Without Property cover, a fire, flood, or theft event at {company}'s "
                f"{physical} shuts operations with no recovery mechanism -- "
                f"business interruption costs typically exceed the physical asset loss."
            )
        else:
            covers_str = " + ".join(cover_labels[:2]) if cover_labels else "the mandatory covers"
            bullet1 = (
                f"Without {covers_str} in place, {company} carries {risk1_key.lower() or 'its core liability'} "
                f"as an entirely uninsured balance-sheet event today."
            )

    # ── BULLET 2: financial / personal / operational consequence, anchored to numbers ──
    if revenue >= 500:
        bullet2 = (
            f"At {rev_str} revenue, even a 3-5% uninsured liability event means "
            f"Rs. {int(revenue * 0.04):,}+ Cr off the P&L -- larger than most founders' "
            f"entire insurance budget for the year."
        )
    elif revenue >= 50:
        bullet2 = (
            f"At {rev_str} revenue with no cover in place, a single regulatory fine "
            f"or client indemnity claim can consume 6-12 months of operating surplus."
        )
    elif revenue >= 5:
        bullet2 = (
            f"{rev_str} revenue means {company} is past the stage where personal-assets "
            f"coverage is enough -- institutional claims at this scale target the company "
            f"entity, not just the founder."
        )
    elif team >= 500:
        bullet2 = (
            f"With {team_str} employees, an uninsured D&O or employment claim "
            f"in {sector} routinely runs Rs. 2-10 Cr in defence costs alone "
            f"before any settlement is reached."
        )
    elif team >= 100:
        bullet2 = (
            f"At {team_str} people, {company} has crossed the size threshold where "
            f"employment and director liability claims become statistically likely -- "
            f"none of that exposure is transferred today."
        )
    elif is_early:
        bullet2 = (
            f"{stage} founders carry full personal director liability until D&O is placed; "
            f"a single investor dispute or regulatory notice at this stage ends the "
            f"fundraising round while litigation runs."
        )
    else:
        bullet2 = (
            f"{stage} {sector} companies that skip insurance at this stage "
            f"typically face their first claim within 24 months -- "
            f"by then, retroactive cover is unavailable."
        )

    # ── BULLET 3: regulatory urgency with named acts, or optional add-on urgency ──
    reg_label = {
        "DPDP":  "DPDP (Rs. 250 Cr penalty ceiling, 2025 enforcement)",
        "SEBI":  "SEBI LODR director liability rules",
        "RBI":   "RBI PPI / PA licence conditions",
        "IRDAI": "IRDAI conduct and fit-and-proper rules",
        "FSSAI": "FSSAI food safety and recall liability",
        "GST":   "GST audit and penalty exposure",
        "MCA":   "MCA-21 director personal obligations",
    }
    named_regs = [reg_label[r] for r in regs if r in reg_label]

    if export_eu >= 5 and "DPDP" not in regs:
        named_regs.append("GDPR cross-border transfer rules")

    if named_regs and optional:
        reg_str = " and ".join(named_regs[:2])
        n_opt = len(optional)
        bullet3 = (
            f"{reg_str} are active obligations for {company}; "
            f"{n_opt} optional add-on{'s' if n_opt != 1 else ''} in this quote "
            f"close the remaining gaps -- confirm before submitting."
        )
    elif named_regs:
        reg_str = " + ".join(named_regs[:2])
        bullet3 = (
            f"Every mandatory cover in this bundle maps to a live {reg_str} obligation "
            f"-- this is the minimum defensible floor for a regulated {sector} business."
        )
    elif optional:
        n_opt = len(optional)
        opt_labels = [_outreach_cover_label(k) for k in optional[:2]]
        opt_str = " and ".join(opt_labels) if opt_labels else "the add-ons"
        bullet3 = (
            f"{opt_str} {'are' if n_opt > 1 else 'is'} pre-staged as optional "
            f"based on {company}'s {sector} exposure profile -- review with the founder "
            f"before finalising the quote."
        )
    elif ai_prod:
        bullet3 = (
            f"AI product liability is an emerging unwritten risk in Indian courts; "
            f"the PI / Tech E&O cover in this bundle is the current best-practice "
            f"transfer mechanism for {company}'s model-output exposure."
        )
    elif export_eu >= 5:
        bullet3 = (
            f"{company} exports to EU customers -- GDPR cross-border transfer liability "
            f"is not covered by Indian domestic policies; the Cyber cover here "
            f"includes international incident response."
        )
    else:
        bullet3 = (
            f"No filler covers included -- every mandatory line closes a specific "
            f"{sector} liability gap that {company} carries today uninsured."
        )

    if founder_concern:
        bundle_name = (bundle_match or {}).get("name") or "this bundle"
        cover_str = ", ".join(cover_labels[:3]) if cover_labels else "the recommended covers"
        concern_text = founder_concern.rstrip(". ")
        product_ref = (
            f"while staying tied to {company}'s stated product and operating model"
            if product_desc
            else f"for the way {company} operates"
        )
        bullet3 = (
            f"You flagged {concern_text} as the biggest concern; {bundle_name} turns that "
            f"into a practical cover conversation around {cover_str}, {product_ref}."
        )

    return [bullet1, bullet2, bullet3]


def build_pitch_meta(bundle_match):
    """Return trigger_question and best_timing from library. Zero tokens."""
    lib_entry = _get_pitch_library_entry(bundle_match)
    return {
        "trigger_question": (lib_entry or {}).get("trigger_question", ""),
        "best_timing": (lib_entry or {}).get("best_timing", ""),
    }


def generate_objection_handlers(profile, bundle_match, scores, triggers):
    """Gemini-personalized objection handlers using normalized library. ~900 tokens."""
    lib_entry = _get_pitch_library_entry(bundle_match)
    seed_objections = _resolve_objections(lib_entry)

    if not seed_objections:
        return []

    company = profile.get("startup_name", "this company")
    sector = profile.get("sector", "")
    stage = profile.get("funding_stage", "seed")
    team_size = profile.get("team_size", "")
    records_count = profile.get("records_count", 0)
    product_desc = _compact_personalization_text(profile.get("product_description"), 220)
    founder_concern = _compact_personalization_text(profile.get("biggest_fear"), 220)

    # Determine stage bucket for stage_sensitivity guidance
    stage_bucket = "series_b_plus" if any(s in (stage or "").lower() for s in ("series b", "series c", "growth", "ipo")) else "seed"

    top_risks = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
    top_risk_names = [r for r, _ in top_risks]

    trigger_labels = []
    for t in (triggers or [])[:3]:
        if isinstance(t, dict):
            trigger_labels.append(t.get("label") or t.get("trigger") or str(t))
        else:
            trigger_labels.append(str(t))

    if not gemini_enabled():
        return [{"underlying_fear": o.get("underlying_fear", ""), "scripted_response": o.get("scripted_response", "")} for o in seed_objections]

    # Build seed with stage_sensitivity hint inline
    enriched = []
    for o in seed_objections:
        sensitivity_hint = (o.get("stage_sensitivity") or {}).get(stage_bucket, "")
        enriched.append({
            "underlying_fear": o.get("underlying_fear", ""),
            "scripted_response": o.get("scripted_response", ""),
            "tone": o.get("tone", ""),
            "stage_guidance": sensitivity_hint,
        })

    prompt = f"""You are a senior ICICI Lombard RM coaching a colleague on handling pushback from {company} ({stage} {sector} startup, {team_size} employees{f', {int(records_count):,} data records' if records_count else ''}).

Company risk context:
- What the company does: {product_desc or 'not provided'}
- Founder concern: {founder_concern or 'not provided'}
- Top risk dimensions: {', '.join(top_risk_names)}
- Regulatory flags: {', '.join(trigger_labels) if trigger_labels else 'none identified'}
- Stage guidance: {stage_bucket.replace('_', ' ')}

For each objection below, rewrite scripted_response to be specific to {company}. Use their risk dimensions, scale, product description, founder concern, and the stage_guidance hint provided. Tone should match the tone field. Keep each response under 60 words. Sound like a trusted advisor, not a salesperson.

{json.dumps(enriched, indent=2, ensure_ascii=False)}

Return ONLY valid JSON:
{{
  "handlers": [
    {{
      "underlying_fear": "...",
      "scripted_response": "..."
    }}
  ]
}}""".strip()

    raw, _ = call_gemini_json(prompt)
    if raw and isinstance(raw, dict) and raw.get("handlers"):
        return raw["handlers"]

    return [{"underlying_fear": o.get("underlying_fear", ""), "scripted_response": o.get("scripted_response", "")} for o in seed_objections]


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
    global_ranked = get_top5_global(scores, profile["sector"], size_bucket, profile["team_size"], profile["funding_stage"], inp)
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
        "outreach_prompts": None,
        "outreach_source": "pending",
        "outreach_error": None,
        "pitch_bullets": build_pitch_bullets(profile, safe_bundle, rounded_scores, json_safe(pricing_quote)),
        "pitch_meta": build_pitch_meta(safe_bundle),
        "objection_handlers": [],
        "rm": {k: v for k, v in load_contacts().items()},
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

    payload["pitch_bullets"] = build_pitch_bullets(
        payload["profile"],
        payload.get("bundle_match"),
        payload["scores"],
        payload.get("pricing_engine_quote"),
    )
    payload["pitch_meta"] = build_pitch_meta(payload.get("bundle_match"))
    # Deterministic fallback included upfront so the client can render it
    # immediately if the lazy /api/outreach call ever fails (no Gemini cost).
    payload["outreach_fallback"] = json_safe(fallback_outreach_prompts(
        payload["profile"],
        payload["scores"],
        payload.get("recommendations", []),
        payload.get("bundle_match") or {},
    ))
    # Gemini-powered versions are deferred — fetched lazily via /api/outreach
    payload["outreach_prompts"] = None
    payload["outreach_source"] = "pending"
    payload["outreach_error"] = None
    payload["objection_handlers"] = []

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


def score(profile):
    if SPARC_ENGINE == "legacy":
        return _legacy_score(profile)
    payload_v2 = _v2_score(profile)
    if SPARC_ENGINE == "shadow":
        payload_legacy = _legacy_score(profile)
        _log_diff(payload_legacy, payload_v2)
        return payload_legacy
    return payload_v2


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
        "seedCompanyProfiles": company_profile_count(),
    }


# ─── PIPELINE ENRICHMENT HELPERS ─────────────────────────────────────────────
_SECTOR_INCUMBENT = {
    "Fintech": "HDFC Ergo", "Healthtech": "Star Health",
    "SaaS / Enterprise Software": "Bajaj Allianz", "Deeptech / AI / Robotics": "Bajaj Allianz",
    "D2C / Consumer Brands": "New India Assurance", "Logistics / Mobility": "Tata AIG",
    "Edtech": "Oriental Insurance", "Agritech / Foodtech": "Agriculture Insurance Co.",
    "Cleantech / Climatetech": "New India Assurance", "Gaming / Media / Content": "Bajaj Allianz",
    "HRtech": "HDFC Ergo", "Legaltech": "Tata AIG", "Spacetech": "New India Assurance",
}
_STAGE_SIGNALS = {
    "preseed": [
        "Founder registered company — no insurance footprint",
        "MVP launched, first liability exposure window open",
        "LinkedIn activity spike — team building phase",
    ],
    "untapped": [
        "Seed round closed — institutional investor pressure for D&O",
        "First 20+ employees hired — IRDAI health mandate triggered",
        "Product live, first enterprise prospect requesting E&O proof",
    ],
    "strike_now": [
        "Series A closed — VC term sheet requires policy proof within 90 days",
        "SEBI/RBI regulatory filing submitted — compliance window open",
        "Enterprise contract pipeline — client mandating cover certificate",
    ],
    "covered": [
        "Policy renewal in 45 days — competitor pitch already circulating",
        "New product line — existing cover may have exclusion gaps",
        "Funding round imminent — D&O upgrade likely required",
    ],
}
_SECTOR_PITCHES = {
    "Fintech": "RBI mandates cyber + D&O — close before their Series B due-diligence window.",
    "Healthtech": "Clinical liability gap is real; ABDM compliance adds new exposure every quarter.",
    "SaaS / Enterprise Software": "Enterprise contracts require E&O proof of cover — we make it frictionless.",
    "Deeptech / AI / Robotics": "IP infringement + product liability — the two risks VCs always flag.",
    "D2C / Consumer Brands": "Product recall + warehouse fire is one event away from wiping working capital.",
    "Logistics / Mobility": "Fleet + gig-worker accident liability — largest claim category in our book.",
    "Edtech": "Student data breach exposure is real; DPDP Act makes this urgent now.",
    "Agritech / Foodtech": "Cold chain + crop failure — multi-line bundle in one RM conversation.",
    "Cleantech / Climatetech": "Infrastructure risk + regulatory liability — build trust before the cap raise.",
    "Gaming / Media / Content": "IP + cyber + D&O — three risks, one conversation, one bundle.",
    "HRtech": "PII data + employer liability — DPDP Act puts fines on the table now.",
    "Legaltech": "Professional indemnity is table stakes; make this their first policy.",
    "Spacetech": "Space + product liability — rare expertise, high trust opportunity.",
}
_COVER_NAMES = {
    "cyber_liability": "Cyber Liability", "dno_liability": "D&O Liability",
    "professional_indemnity": "Professional Indemnity", "property_fire": "Property & Fire",
    "business_interruption": "Business Interruption", "employee_health": "Group Health",
    "group_pa": "Group Personal Accident", "public_liability": "Public Liability",
    "employees_comp": "Workmen\'s Compensation", "burglary": "Burglary & Theft",
    "product_liability": "Product Liability", "key_person": "Keyman Insurance",
    "marine_transit": "Marine Transit", "employment_practices": "Employment Practices",
    "crime_fidelity": "Crime & Fidelity", "property_all_risk": "Property All Risk",
    "electronic_equipment": "Electronic Equipment", "trade_credit": "Trade Credit",
    "engineering": "Engineering Insurance", "contractors_all_risk": "Contractors All Risk",
    "event_production": "Event Production",
}


def _incumbent(stage: str, sector: str) -> str:
    if stage in ("Pre-seed", "Seed"):
        return ""
    return _SECTOR_INCUMBENT.get(sector, "")


def _signal(tap: str, name: str) -> dict:
    texts = _STAGE_SIGNALS.get(tap, ["Company milestone detected — outreach window open"])
    h = abs(hash(name)) % len(texts)
    days = [7, 14, 21, 30, 45][abs(hash(name + "_days")) % 5]
    return {"text": texts[h], "daysAgo": days}


def _pitch_angle(sector: str, incumbent: str) -> str:
    base = _SECTOR_PITCHES.get(sector, "Right cover for your stage — one conversation to close.")
    if not incumbent:
        return "Greenfield opportunity — " + base[0].lower() + base[1:]
    return base


def _bundle_lines(bm: dict, max_lakh: float) -> list:
    covers = bm.get("mandatory_covers") or []
    if not covers or max_lakh <= 0:
        return [[bm.get("name", "Bundle"), max_lakh]] if max_lakh > 0 else []
    per = round(max_lakh / len(covers), 1)
    return [[_COVER_NAMES.get(c, c.replace("_", " ").title()), per] for c in covers]


def _opp_score(row: dict) -> int:
    stage_wt = {"Pre-seed": 5, "Seed": 20, "Series A": 55, "Series B+": 65}.get(
        row.get("funding_stage", ""), 10
    )
    prem_norm = min(25, int(row.get("max_lakh", 0) / 6))
    risk_norm = min(15, int(row.get("overall_score", 0) / 7))
    inc_bonus = 0 if row.get("incumbent") else 15
    return min(100, stage_wt + prem_norm + risk_norm + inc_bonus)


# --- Signal Radar: public-trigger intelligence MVP -------------------------
try:
    from signal_rules import SIGNAL_RULES  # standalone server.py run
except ImportError:
    from startup_shield_web.signal_rules import SIGNAL_RULES  # Vercel import path

EXCLUDED_SIGNAL_SOURCES = {
    "facebook.com",
    "facebook",
    "instagram.com",
    "instagram",
    "linkedin.com",
    "linkedin",
    "twitter.com",
    "twitter",
    "x.com",
    "x",
    "youtube.com",
    "youtube",
}

SIGNAL_WATCHLIST_QUERIES = [
    "Rapido 240M funding Prosus WestBridge Accel",
    "Scapia 63M General Catalyst funding",
    "Anscer Robotics warehouse factory deployments Series A",
    "Apollyon Dynamics UAV drone manufacturing funding",
    "Garuda Aerospace IPO drone park",
    "MobiKwik NBFC RBI licence lending business",
    "Paytm Payments Bank RBI licence cancelled",
    "Paramotor Digital confidential IPO SEBI fintech",
    "Practo healthcare AI GMV US",
    "Legend of Toys manufacturing international markets funding",
    "HrdWyr semiconductor funding AI processors",
    "Adda247 layoffs IPO listing",
    "Zetwerk Razorpay Kissht DRHP IPO",
    "Armory counter UAS MoD order defence startup",
    "GalaxEye satellite OptoSAR orbit",
    "quick commerce dark store expansion India",
    # ── Regulatory news queries (feed the 122 regulation-driven rules) ────────
    "DPDP Act compliance India startup data protection",
    "Significant Data Fiduciary DPO appointment India",
    "Data Protection Board India DPB inquiry notice",
    "DPDP rules consent manager India fintech",
    "RBI digital lending guidelines fintech NBFC compliance",
    "RBI multi-lender impartiality matching loan India",
    "RBI CIMS portal digital lending app compliance",
    "RBI dynamic authentication non-card-present India",
    "ONDC seller reputation ledger network participant",
    "ONDC grievance redressal ODR dispute India",
    "ONDC logistics dispute cargo India",
    "DGCA drone type certification India NPNT",
    "DGCA Digital Sky eGCA drone India",
    "DGCA UIN drone certification India",
    "Karnataka gig worker welfare cess GMV bill",
    "Karnataka platform worker IDRC labour tribunal",
    "Karnataka gig worker GSTN welfare board",
    "GSTN dark store ONDC serviceability India",
    "BVLOS drone India type certification",
    "MeitY SDF designation data fiduciary India",
]

FALLBACK_SIGNAL_ARTICLES = [
    {
        "title": "Razorpay receives RBI payment aggregator licence and expands regulated payments operations",
        "url": "",
        "source": "Fallback demo signal",
        "seendate": "20260521T090000Z",
    },
    {
        "title": "Ather Energy opens new manufacturing facility as electric scooter demand rises",
        "url": "",
        "source": "Fallback demo signal",
        "seendate": "20260521T083000Z",
    },
    {
        "title": "ideaForge expands drone platform for enterprise and defence UAV operations",
        "url": "",
        "source": "Fallback demo signal",
        "seendate": "20260521T080000Z",
    },
    {
        "title": "Pristyn Care adds new clinics and healthcare capacity across Indian cities",
        "url": "",
        "source": "Fallback demo signal",
        "seendate": "20260521T073000Z",
    },
    {
        "title": "Zepto expands dark-store warehouse network after fresh funding round",
        "url": "",
        "source": "Fallback demo signal",
        "seendate": "20260521T070000Z",
    },
    {
        "title": "boAt plans pre-IPO governance preparation after consumer electronics scale-up",
        "url": "",
        "source": "Fallback demo signal",
        "seendate": "20260521T063000Z",
    },
    {
        "title": "Razorpay flagged as Significant Data Fiduciary; appoints Data Protection Officer under DPDP Act obligations",
        "url": "",
        "source": "Fallback demo signal",
        "seendate": "20260521T060000Z",
    },
    {
        "title": "Swiggy hit by GSTN-Welfare Board mismatch under Karnataka gig welfare cess audit",
        "url": "",
        "source": "Fallback demo signal",
        "seendate": "20260521T055000Z",
    },
    {
        "title": "ideaForge faces DGCA Type Certification rejection on new VTOL drone after NPNT test failure",
        "url": "",
        "source": "Fallback demo signal",
        "seendate": "20260521T053000Z",
    },
    {
        "title": "MobiKwik triggers RBI CIMS portal mismatch notice on Digital Lending App compliance certification",
        "url": "",
        "source": "Fallback demo signal",
        "seendate": "20260521T051000Z",
    },
    {
        "title": "Zepto dark store GST registration surge as quick commerce fulfilment hubs scale across India",
        "url": "",
        "source": "Fallback demo signal",
        "seendate": "20260521T050000Z",
    },
]


def _article_text(article: dict) -> str:
    return " ".join(str(article.get(k) or "") for k in ("title", "description", "source")).lower()


def _classify_signal(article: dict) -> dict:
    text = _article_text(article)
    best = None
    best_hits = 0
    best_score = 0
    for rule in SIGNAL_RULES:
        hits = sum(1 for kw in rule["keywords"] if kw in text)
        score_value = hits * 10 + int(rule.get("priority", 0))
        if hits and score_value > best_score:
            best = rule
            best_hits = hits
            best_score = score_value
    if best:
        # Honour the rule's calibrated confidence (per-rule false-positive weight),
        # then add a small uplift when more than one keyword matched.
        base = int(best.get("confidence", 50))
        uplift = min(10, max(0, (best_hits - 1) * 4))
        confidence = min(96, base + uplift)
        return {**best, "confidence": confidence}
    return {
        "id": "market_news",
        "label": "Market news",
        "why": "Company activity may create a new risk conversation",
        "angle": "Run SPARC assessment",
        "keywords": [],
        "profile": {},
        "confidence": 42,
    }


def _verified_profiles():
    try:
        from company_profiles import COMPANY_PROFILES
        return {name: prof for name, prof in COMPANY_PROFILES.items() if prof.get("profile_source") == "verified"}
    except Exception:
        return {}


def _match_signal_company(article: dict, profiles: dict) -> tuple[str, dict | None]:
    title = str(article.get("title") or "")
    title_core = re.split(r"\s[-|]\s", title, maxsplit=1)[0]
    lower_title = title_core.lower()
    for name, profile in sorted(profiles.items(), key=lambda item: len(item[0]), reverse=True):
        name_l = name.lower()
        if len(name_l) <= 4:
            if re.search(rf"(?<![a-z0-9]){re.escape(name_l)}(?![a-z0-9])", lower_title):
                return name, profile.copy()
        elif name_l in lower_title:
            return name, profile.copy()

    splitters = [
        " raises ", " raised ", " secures ", " gets ", " receives ", " opens ",
        " plans ", " expands ", " adds ", " launches ", " files ", " wins ",
        " bags ", " partners ", " declines ", " surges ", " jumps ", " drops ",
        " to ", " after ", " as ",
    ]
    candidate = title_core
    for token in splitters:
        idx = lower_title.find(token)
        if idx > 0:
            candidate = title[:idx]
            break
    candidate = re.sub(r"[^A-Za-z0-9&.\- ]+", " ", candidate).strip()
    candidate = re.sub(r"^(exclusive|exclusive interview|exclusive:)\s+", "", candidate, flags=re.IGNORECASE).strip()
    words = candidate.split()
    if len(words) > 5:
        candidate = " ".join(words[:5])
    candidate = re.sub(
        r"^(fintech|payments|healthcare|ev|ai|tech|entertainment|deeptech|saas)\s+(firm|company|startup|platform)\s+",
        "",
        candidate,
        flags=re.IGNORECASE,
    )
    startup_match = re.search(r"\bstartup\s+(.+)$", candidate, flags=re.IGNORECASE)
    if startup_match:
        candidate = startup_match.group(1)
    candidate = re.sub(r"^startup\s+", "", candidate, flags=re.IGNORECASE)
    return candidate or "Unmatched startup", None


def _looks_generic_signal_article(article: dict) -> bool:
    title = str(article.get("title") or "").lower()
    generic_patterns = [
        "india deal review",
        "startup funding:",
        "startup funding surges",
        "startup funding declines",
        "startup funding drops",
        "startup funding jumps",
        "startup funding report",
        "startup funding round-up",
        "startup funding roundup",
        "funding report",
        "funding roundup",
        "bengaluru leads india",
        "raised over $",
        "raised more than $",
        "startups raised",
        "indian startups raised",
        "this week",
        "weekly funding",
        "month in review",
        "q1 2026",
        "from oil shock",
        "how ",
        "why ",
        "what ",
        "startup funding, exits",
        "funding support strengthens ecosystem",
        "investors demand profitability",
        "rbi proposes",
        "launches rs",
        "launches inr",
        "secondaries fund",
        "with ₹",
        " corpus",
        "bharat tech fund",
        "ace fund",
        "startup ipo tracker",
        "ipo tracker 2026",
        "indian startup ipo tracker",
        "startups have filed drhps",
        "startup news and updates",
    ]
    return any(pattern in title for pattern in generic_patterns)


_HEADLINE_VERBS = {
    "becomes", "become", "moves", "move", "cuts", "cut", "lays", "lay", "hires",
    "expands", "expand", "launches", "launch", "raises", "raise", "files", "file",
    "bags", "bag", "wins", "win", "plans", "plan", "adds", "add", "opens", "open",
    "drops", "drop", "surges", "surge", "jumps", "jump", "declines", "decline",
    "trails", "trail", "catches", "leads", "lead", "beats", "beat", "slashes",
}


def _looks_generic_signal_company(company: str) -> bool:
    text = company.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text).strip()
    if len(company.split()) > 4:
        return True
    if not re.search(r"[a-z]", text):
        return True
    # block any word that is a common headline verb — real company names don't contain them
    words_set = set(text.split())
    if words_set & _HEADLINE_VERBS:
        return True
    generic_terms = [
        "funding",
        "funding declines",
        "funding surges",
        "funding bengaluru",
        "bengaluru leads",
        "india deal review",
        "deal review",
        "q1",
        "q2",
        "q3",
        "q4",
        "april",
        "may",
        "june",
        "july",
        "between may",
        "as many as",
        "diverse sectors",
        "five startups",
        "secure initial funding",
        "government",
        "raised over",
        "startup ipo tracker",
        "startup funding",
        "funding and acquisitions",
        "indian startup",
        "ai dhamaka",
        "innovation day",
        "startup news",
        "this week",
        "weekly",
        " news",
        "technology news",
        "tech news",
    ]
    return any(term in text for term in generic_terms)


def _is_plausible_signal_company(company: str, base_profile: dict | None) -> bool:
    if base_profile is not None:
        return True
    candidate = str(company or "").strip()
    if not candidate or _looks_generic_signal_company(candidate):
        return False
    words = candidate.split()
    if len(words) > 4:
        return False
    generic_words = {
        "india", "indian", "startup", "startups", "funding", "round", "report",
        "review", "sector", "sectors", "bengaluru", "delhi", "mumbai",
        "weekly", "monthly", "q1", "q2", "q3", "q4", "news", "unicorn",
    }
    words_lower = [re.sub(r"[^a-z0-9]+", "", w.lower()) for w in words]
    if all(w in generic_words for w in words_lower):
        return False
    if any(w in _HEADLINE_VERBS for w in words_lower):
        return False
    if not re.match(r"^[A-Z0-9][A-Za-z0-9&.\-]*(?:\s+[A-Z0-9][A-Za-z0-9&.\-]*){0,3}$", candidate):
        return False
    return True


def _rss_item_datetime(value: str):
    if not value:
        return None
    try:
        dt = parsedate_to_datetime(value)
    except Exception:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _within_signal_window(value: str, window_days: int) -> bool:
    if window_days <= 0:
        return True
    dt = _rss_item_datetime(value)
    if dt is None:
        return True
    return dt >= (datetime.now(timezone.utc) - timedelta(days=window_days))


def _merge_signal_profile(company: str, base: dict | None, rule: dict) -> dict:
    profile = DEFAULT_PROFILE.copy()
    if base:
        profile.update(base)
    profile["startup_name"] = company
    if rule.get("sector"):
        profile["sector"] = rule["sector"]
    if rule.get("stage"):
        profile["funding_stage"] = rule["stage"]
    profile.update(rule.get("profile") or {})
    return profile


def _fetch_gdelt_signal_articles(limit: int = 18) -> list[dict]:
    queries = [
        '"Indian startup" India',
        'startup India funding',
        'startup India RBI',
        'startup India warehouse factory',
        'startup India IPO',
    ]
    timeout = float(os.environ.get("SIGNAL_RADAR_TIMEOUT_SECONDS", "12"))
    maxrecords = max(10, min(limit * 2, 50))
    rows = []
    seen_urls = set()

    for query in queries:
        params = urllib.parse.urlencode({
            "query": query,
            "mode": "ArtList",
            "format": "json",
            "maxrecords": maxrecords,
            "sort": "HybridRel",
        })
        url = f"https://api.gdeltproject.org/api/v2/doc/doc?{params}"
        req = urllib.request.Request(url, headers={"User-Agent": "SPARC-SignalRadar/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8", errors="ignore") or "{}")

        for art in payload.get("articles") or []:
            source_url = art.get("url") or ""
            dedupe_key = source_url or art.get("title") or ""
            if not dedupe_key or dedupe_key in seen_urls:
                continue
            seen_urls.add(dedupe_key)
            row = {
                "title": art.get("title") or "",
                "url": source_url,
                "source": art.get("domain") or art.get("sourceCountry") or "GDELT",
                "seendate": art.get("seendate") or "",
                "description": art.get("snippet") or "",
            }
            if row["title"]:
                rows.append(row)
        if len(rows) >= limit:
            break

    matched = [r for r in rows if _classify_signal(r).get("id") != "market_news"]
    return (matched or rows)[:limit]


def _fetch_google_news_signal_articles(limit: int = 18, window_days: int = 30) -> list[dict]:
    window_days = max(1, min(int(window_days or 30), 30))
    queries = [
        f"Indian startup funding when:{window_days}d",
        f"Indian startup RBI licence fintech NBFC when:{window_days}d",
        f"Indian startup warehouse factory manufacturing deployment when:{window_days}d",
        f"Indian startup healthcare clinic hospital AI GMV when:{window_days}d",
        f"Indian startup drone robotics UAV defence DGCA when:{window_days}d",
        f"Indian startup IPO DRHP SEBI confidential filing when:{window_days}d",
        f"Indian startup layoffs restructuring IPO when:{window_days}d",
        f"Indian startup dark store quick commerce expansion when:{window_days}d",
        f"site:reuters.com India startup RBI NBFC fintech when:{window_days}d",
        f"site:timesofindia.indiatimes.com startup funding IPO drone fintech when:{window_days}d",
        f"site:business-standard.com startup robotics healthcare defence funding when:{window_days}d",
    ]
    queries.extend(f"{q} when:{window_days}d" for q in SIGNAL_WATCHLIST_QUERIES)
    timeout = float(os.environ.get("SIGNAL_RADAR_TIMEOUT_SECONDS", "12"))
    rows = []
    seen_titles = set()

    for query in queries:
        params = urllib.parse.urlencode({
            "q": query,
            "hl": "en-IN",
            "gl": "IN",
            "ceid": "IN:en",
        })
        url = f"https://news.google.com/rss/search?{params}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 SPARC-SignalRadar/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                root = ET.fromstring(resp.read())
        except Exception:
            continue

        channel = root.find("channel")
        items = channel.findall("item") if channel is not None else []
        for item in items[:20]:
            title = item.findtext("title") or ""
            if not title or title in seen_titles:
                continue
            seen_titles.add(title)
            pub_date = item.findtext("pubDate") or ""
            if not _within_signal_window(pub_date, window_days):
                continue
            source = item.find("{*}source")
            source_name = (source.text if source is not None else "") or "Google News"
            if source_name.lower() in EXCLUDED_SIGNAL_SOURCES:
                continue
            rows.append({
                "title": title,
                "url": item.findtext("link") or "",
                "source": source_name,
                "seendate": pub_date,
                "description": item.findtext("description") or "",
            })
        if len(rows) >= limit * 4:
            break

    matched = [r for r in rows if _classify_signal(r).get("id") != "market_news"]
    return (matched or rows)[:limit]


def _fetch_direct_rss_signal_articles(limit: int = 18, window_days: int = 30) -> list[dict]:
    window_days = max(1, min(int(window_days or 30), 30))
    feeds = [
        ("Inc42", "https://inc42.com/feed/"),
        ("YourStory", "https://yourstory.com/feed"),
        ("Economic Times Startups", "https://economictimes.indiatimes.com/small-biz/startups/rssfeeds/70591255.cms"),
        ("Trak.in", "https://trak.in/feed/"),
    ]
    timeout = float(os.environ.get("SIGNAL_RADAR_TIMEOUT_SECONDS", "8"))
    rows = []
    seen_titles = set()

    for source_name, feed_url in feeds:
        req = urllib.request.Request(feed_url, headers={"User-Agent": "Mozilla/5.0 SPARC-SignalRadar/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                root = ET.fromstring(resp.read())
        except Exception:
            continue

        channel = root.find("channel")
        items = channel.findall("item") if channel is not None else root.findall(".//item")
        for item in items[:25]:
            title = (item.findtext("title") or "").strip()
            if not title or title in seen_titles:
                continue
            seen_titles.add(title)
            pub_date = item.findtext("pubDate") or item.findtext("{*}date") or ""
            if not _within_signal_window(pub_date, window_days):
                continue
            rows.append({
                "title": title,
                "url": item.findtext("link") or feed_url,
                "source": source_name,
                "seendate": pub_date,
                "description": item.findtext("description") or "",
            })
            if len(rows) >= limit * 3:
                break
        if len(rows) >= limit * 3:
            break

    matched = [r for r in rows if _classify_signal(r).get("id") != "market_news"]
    return (matched or rows)[:limit]


_TELEMETRY_BY_REGULATION = {
    "DPDP": "MeitY DPDP audit registry, SDF designations gazette, CERT-In incident reports",
    "RBI":  "RBI circulars, NBFC database, Digital Lending Guidelines updates, SRO-FT bulletins",
    "ONDC": "ONDC reputation ledger, network seller compliance reports, dispute resolution data",
    "DGCA": "DGCA NPNT firmware registry, drone Type Certification database, RPAS operator permits",
    "KGW":  "Karnataka Labour Department portal, gig worker welfare cess filings, GSTN reconciliation",
    "GST":  "GSTN reconciliation portal, e-invoice mismatch reports, ITC denial notices",
    "MeitY":"MeitY SDF notifications, IT Rules gazette, CERT-In incident registry",
}


def _telemetry_source_for(rule: dict, source_domain: str) -> str:
    reg = rule.get("regulation") or ""
    if reg in _TELEMETRY_BY_REGULATION:
        return _TELEMETRY_BY_REGULATION[reg]
    return f"Public news monitoring ({source_domain or 'multiple sources'})"


def _contact_status_for_signal(profile: dict | None) -> dict:
    # MVP deliberately avoids personal email guessing. Official company email discovery
    # can be added behind this status when a compliant source is available.
    if profile and profile.get("website"):
        return {"status": "Official domain available", "detail": profile.get("website")}
    return {"status": "Needs source review", "detail": "Use official company email or CRM contact only"}


def _signal_task_from_article(article: dict, profiles: dict) -> dict | None:
    if _looks_generic_signal_article(article):
        return None
    rule = _classify_signal(article)
    company, base_profile = _match_signal_company(article, profiles)
    if not company or company.lower() in ("india", "indian startup", "startup"):
        return None
    if not _is_plausible_signal_company(company, base_profile):
        return None

    profile = _merge_signal_profile(company, base_profile, rule)
    try:
        result = score(profile)
    except Exception:
        result = {}
    bundle = result.get("bundle_match") or {}
    premium = result.get("premium_summary") or {}
    scores = result.get("scores") or {}
    score_vals = [v for v in scores.values() if isinstance(v, (int, float))]
    avg_score = round(sum(score_vals) / len(score_vals), 1) if score_vals else 0
    source_url = article.get("url") or ""
    parsed_domain = urllib.parse.urlparse(source_url).netloc.replace("www.", "") if source_url else ""
    source_domain = article.get("source", "") if parsed_domain == "news.google.com" else (parsed_domain or article.get("source", ""))
    contact = _contact_status_for_signal(base_profile)
    profile_delta = []
    for key in sorted((rule.get("profile") or {}).keys()):
        profile_delta.append(key)
    if rule.get("sector"):
        profile_delta.append("sector")
    if rule.get("stage"):
        profile_delta.append("funding_stage")

    return {
        "company": company,
        "signal_id": rule["id"],
        "signal": rule["label"],
        "signal_indicator": rule["label"],
        "telemetry_source": _telemetry_source_for(rule, source_domain),
        "underwriting_rationale": rule["why"],
        "target_products": f"{bundle.get('name') or 'SPARC bundle'} — {rule['angle']}",
        "why_it_matters": rule["why"],
        "insurance_angle": rule["angle"],
        "headline": article.get("title") or "",
        "source_url": source_url,
        "source": source_domain or "Public source",
        "seen_at": article.get("seendate") or "",
        "confidence": rule.get("confidence", 50),
        "regulation_tag": rule.get("regulation", ""),
        "review_status": "Needs RM review",
        "contact_status": contact["status"],
        "contact_detail": contact["detail"],
        "profile_delta": profile_delta,
        "sector": profile.get("sector"),
        "funding_stage": profile.get("funding_stage"),
        "recommended_bundle": bundle.get("name") or "Run SPARC assessment",
        "premium_min_lakh": premium.get("min_lakh", 0),
        "premium_max_lakh": premium.get("max_lakh", 0),
        "overall_score": avg_score,
        "rm_action": f"Review {rule['label'].lower()} trigger, validate source, then approach with {bundle.get('name') or 'SPARC assessment'}.",
    }


def get_signal_radar(limit: int = 30, live: bool = True, window_days: int = 30) -> dict:
    window_days = max(1, min(int(window_days or 30), 30))
    profiles = _verified_profiles()
    source_status = "fallback"
    source_error = ""
    articles = []
    seen_article_keys = set()

    def add_articles(new_articles: list[dict]) -> int:
        added = 0
        for article in new_articles:
            key = (article.get("url") or article.get("title") or "").strip().lower()
            if not key or key in seen_article_keys:
                continue
            seen_article_keys.add(key)
            articles.append(article)
            added += 1
            if len(articles) >= max(limit * 4, 80):
                break
        return added

    if live:
        from concurrent.futures import ThreadPoolExecutor
        fetch_limit = max(limit * 4, 80)
        live_sources = []
        with ThreadPoolExecutor(max_workers=3) as _ex:
            futures = {
                "rss":         _ex.submit(_fetch_direct_rss_signal_articles, limit=fetch_limit, window_days=window_days),
                "google_news": _ex.submit(_fetch_google_news_signal_articles, limit=fetch_limit, window_days=window_days),
                "gdelt":       _ex.submit(_fetch_gdelt_signal_articles, limit=fetch_limit),
            }
            for name in ("rss", "google_news", "gdelt"):
                try:
                    if add_articles(futures[name].result()):
                        live_sources.append(name)
                except Exception as exc:
                    source_error = source_error or type(exc).__name__
        if live_sources:
            source_status = "live_multi" if len(live_sources) > 1 else f"live_{live_sources[0]}"
            source_error = "" if articles else source_error
    if not articles:
        articles = FALLBACK_SIGNAL_ARTICLES

    def _article_dt(article: dict):
        seendate = article.get("seendate") or ""
        dt = _rss_item_datetime(seendate)
        if dt is None and len(seendate) >= 15:
            try:
                dt = datetime.strptime(seendate[:15], "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc)
            except Exception:
                pass
        return dt or datetime.min.replace(tzinfo=timezone.utc)

    articles.sort(key=_article_dt, reverse=True)

    def _norm_company(name):
        s = re.sub(r"\s+", " ", str(name or "").lower().strip())
        for suffix in (" pvt ltd", " private limited", " pvt. ltd.", " pvt. ltd", " ltd.", " ltd",
                       " technologies", " technology", " solutions", " services", " digital",
                       " robotics", " systems", " ventures", " labs", " ai", " fintech"):
            if s.endswith(suffix):
                s = s[: -len(suffix)].strip()
        return s

    best_by_company: dict = {}
    _saved_key = os.environ.get("GEMINI_API_KEY", "")
    os.environ["GEMINI_API_KEY"] = ""
    try:
        for article in articles:
            task = _signal_task_from_article(article, profiles)
            if not task:
                continue
            nc = _norm_company(task["company"])
            prev = best_by_company.get(nc)
            if prev is None or task.get("confidence", 0) > prev.get("confidence", 0):
                best_by_company[nc] = task
    finally:
        if _saved_key:
            os.environ["GEMINI_API_KEY"] = _saved_key
        else:
            os.environ.pop("GEMINI_API_KEY", None)

    def _task_sort_key(t):
        seendate = t.get("seen_at") or ""
        dt = _rss_item_datetime(seendate)
        if dt is None and len(seendate) >= 15:
            try:
                dt = datetime.strptime(seendate[:15], "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc)
            except Exception:
                pass
        ts = dt.timestamp() if dt else 0
        return (ts, t.get("confidence", 0))

    tasks = sorted(best_by_company.values(), key=_task_sort_key, reverse=True)[:limit]

    high_conf = [t for t in tasks if t.get("confidence", 0) >= 70]
    premium_pool = round(sum(float(t.get("premium_max_lakh") or 0) for t in tasks) / 100, 1)
    signal_counts = {}
    for task in tasks:
        signal_counts[task["signal"]] = signal_counts.get(task["signal"], 0) + 1
    top_signal = max(signal_counts, key=signal_counts.get) if signal_counts else ""

    return {
        "signals": tasks,
        "kpis": {
            "total": len(tasks),
            "high_confidence": len(high_conf),
            "premium_pool_cr": premium_pool,
            "top_signal": top_signal,
        },
        "source_status": source_status,
        "source_error": source_error,
        "window_days": window_days,
        "window_label": f"Last {window_days} days",
        "source_policy": "Public news signals only. Use official company email or CRM contact after human review.",
    }


_pipeline_cache: list[dict] | None = None


def _balanced_pipeline_rows(rows: list[dict], limit: int) -> list[dict]:
    """Keep the default opportunity list stage-balanced instead of Series B+ dominated."""
    if limit <= 0:
        return []

    stage_order = ["Pre-seed", "Seed", "Series A", "Series B+"]
    buckets = {stage: [r for r in rows if r.get("funding_stage") == stage] for stage in stage_order}
    other_rows = [r for r in rows if r.get("funding_stage") not in buckets]

    balanced = []
    for stage in stage_order:
        balanced.extend(buckets[stage])
    balanced.extend(other_rows)
    return balanced[:limit]


def get_pipeline(sector_filter: str = "", stage_filter: str = "", limit: int = 500) -> dict:
    global _pipeline_cache
    if _pipeline_cache is None:
        from company_profiles import COMPANY_PROFILES as _CP
        rows = []
        _saved_key = os.environ.get("GEMINI_API_KEY", "")
        os.environ["GEMINI_API_KEY"] = ""  # force deterministic — no Gemini during pipeline scoring
        try:
            for name, prof in _CP.items():
                try:
                    raw_src = prof.get("profile_source", "")
                    if raw_src != "verified":
                        continue
                    result = score(prof)
                    bm = result.get("bundle_match") or {}
                    ps = result.get("premium_summary") or {}
                    sc = result.get("scores") or {}
                    top_risks = result.get("top_risks") or []
                    scores_vals = [v for v in sc.values() if isinstance(v, (int, float))]
                    avg_score = round(sum(scores_vals) / len(scores_vals), 1) if scores_vals else 0
                    src = "verified"
                    stage = prof.get("funding_stage", "")
                    if stage == "Pre-seed":
                        tap = "preseed"
                    elif stage == "Seed":
                        tap = "untapped"
                    elif stage == "Series A":
                        tap = "strike_now"
                    else:
                        tap = "covered"
                    sector = prof.get("sector", "")
                    inc = _incumbent(stage, sector)
                    max_l = ps.get("max_lakh", 0)
                    _stage_yr = {"Pre-seed": 1, "Seed": 2, "Series A": 4, "Series B+": 7}
                    rows.append({
                        "startup_name": name,
                        "sector": sector,
                        "funding_stage": stage,
                        "bundle_name": bm.get("name", ""),
                        "min_lakh": ps.get("min_lakh", 0),
                        "max_lakh": max_l,
                        "overall_score": avg_score,
                        "top_risk": top_risks[0].get("name", "") if top_risks else "",
                        "profile_source": src,
                        "tap_status": tap,
                        # enriched fields
                        "city": (prof.get("state_footprint") or ["India"])[0],
                        "founded": max(2012, 2024 - _stage_yr.get(stage, 3)),
                        "team": prof.get("team_size", 0),
                        "revenue": prof.get("annual_revenue_cr", 0),
                        "operations": ", ".join((prof.get("physical_assets") or [])[:2]) or "Digital-first",
                        "incumbent": inc,
                        "signal": _signal(tap, name),
                        "opp": 0,
                        "bundle_lines": _bundle_lines(bm, max_l),
                        "pitch": _pitch_angle(sector, inc),
                        "drivers": [tr.get("name", "") for tr in (top_risks or [])[:3]],
                    })
                except Exception as _exc:
                    print(f"[pipeline] skip '{name}': {_exc}", flush=True)
        finally:
            if _saved_key:
                os.environ["GEMINI_API_KEY"] = _saved_key
            else:
                os.environ.pop("GEMINI_API_KEY", None)
        for row in rows:
            row["opp"] = _opp_score(row)
        stage_rank = {"Pre-seed": 0, "Seed": 1, "Series A": 2, "Series B+": 3}
        rows.sort(key=lambda r: (stage_rank.get(r["funding_stage"], 9), -r["max_lakh"], r["startup_name"].lower()))
        _pipeline_cache = rows

    filtered = _pipeline_cache
    if sector_filter:
        sf = sector_filter.lower()
        filtered = [r for r in filtered if sf in r["sector"].lower()]
    if stage_filter:
        stf = stage_filter.lower()
        filtered = [r for r in filtered if r["funding_stage"].lower() == stf]

    displayed = filtered[:limit] if stage_filter else _balanced_pipeline_rows(filtered, limit)

    total_pool_cr = round(sum(r["max_lakh"] for r in displayed) / 100, 1)
    untapped = [r for r in displayed if r["tap_status"] in ("untapped", "strike_now")]
    untapped_pool_cr = round(sum(r["max_lakh"] for r in untapped) / 100, 1)
    sectors = [r["sector"] for r in displayed if r["sector"]]
    top_sector = max(set(sectors), key=sectors.count) if sectors else ""
    avg_score = round(sum(r["overall_score"] for r in displayed) / len(displayed), 1) if displayed else 0

    return {
        "companies": displayed,
        "total": len(displayed),
        "kpis": {
            "total_companies": len(displayed),
            "total_pool_cr": total_pool_cr,
            "untapped_pool_cr": untapped_pool_cr,
            "untapped_count": len(untapped),
            "top_sector": top_sector,
            "avg_risk_score": avg_score,
        },
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
            limit = clean_int((params.get("limit") or ["25"])[0], 25)
            if name:
                profile = get_company_profile(name)
                if not profile:
                    self.send_json(404, {"error": "Company profile not found"})
                else:
                    self.send_json(200, {"profile": profile})
                return
            self.send_json(200, {"count": company_profile_count(), "matches": search_company_profiles(query, limit=limit)})
            return
        if path == "/api/pipeline/clear-cache":
            global _pipeline_cache
            _pipeline_cache = None
            self.send_json(200, {"ok": True, "message": "Pipeline cache cleared"})
            return
        if path == "/api/pipeline":
            sector_filter = (params.get("sector") or [""])[0].strip()
            stage_filter = (params.get("stage") or [""])[0].strip()
            limit = clean_int((params.get("limit") or ["500"])[0], 500)
            self.send_json(200, get_pipeline(sector_filter, stage_filter, limit))
            return
        if path == "/api/signals":
            limit = clean_int((params.get("limit") or ["30"])[0], 30)
            days = clean_int((params.get("days") or ["30"])[0], 30)
            live_raw = (params.get("live") or ["1"])[0].strip().lower()
            live = live_raw not in ("0", "false", "no")
            self.send_json(200, get_signal_radar(
                limit=max(1, min(limit, 50)),
                live=live,
                window_days=max(1, min(days, 30)),
            ))
            return
        return super().do_GET()

    def do_POST(self):
        if self.path not in ("/api/analyze", "/api/policy/compare", "/api/autofill", "/api/outreach", "/api/pricing"):
            self.send_json(404, {"error": "Not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            if self.path == "/api/policy/compare":
                result = analyze_policy_wording(payload)
                self.send_json(200 if result.get("ok") else 400, result)
            elif self.path == "/api/pricing":
                self.send_json(200, make_pricing_response(payload))
            elif self.path == "/api/autofill":
                company_name = (payload.get("company_name") or "").strip()
                if not company_name:
                    self.send_json(400, {"error": "company_name is required."})
                    return
                result = autofill_and_analyze(company_name)
                self.send_json(200 if not result.get("error") else 500, result)
            elif self.path == "/api/outreach":
                profile = payload.get("profile") or {}
                scores = payload.get("scores") or {}
                recommendations = payload.get("recommendations") or []
                bundle_match = payload.get("bundle_match") or {}
                triggers = (
                    payload.get("display_regulatory_triggers")
                    or payload.get("regulatory_triggers_fired")
                    or []
                )
                size_bucket = profile.get("size_bucket", "mid")
                try:
                    out_prompts, out_source, out_error = outreach_prompts(
                        profile, scores, recommendations, bundle_match, size_bucket
                    )
                    handlers = json_safe(generate_objection_handlers(
                        profile, bundle_match, scores, triggers
                    ))
                except Exception:
                    out_prompts = fallback_outreach_prompts(profile, scores, recommendations, bundle_match)
                    out_source = "fallback"
                    out_error = None
                    handlers = []
                self.send_json(200, {
                    "outreach_prompts": json_safe(out_prompts),
                    "outreach_source": out_source,
                    "outreach_error": out_error,
                    "objection_handlers": handlers,
                })
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
