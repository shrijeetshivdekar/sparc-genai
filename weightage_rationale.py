from risk_engine import RISK_CATEGORY_STATS, SECTOR_PROFILES


WEIGHT_KEY_TO_CATEGORY = {
    "cyber_technical": "Cyber Technical Risk",
    "data_privacy_regulatory": "Data Privacy Risk",
    "liability": "Liability Risk",
    "ip_infringement": "IP Infringement Risk",
    "key_person": "Key Person Risk",
    "governance_fraud": "Governance & Fraud Risk",
    "property": "Property Risk",
    "compliance": "Regulatory Compliance Risk",
    "esg_climate": "ESG & Climate Risk",
    "geopolitical": "Geopolitical Risk",
    "gig_labour": "Gig & Labour Risk",
    "policy_velocity": "Policy Velocity Risk",
    "reputation": "Reputation Risk",
    "tax_tp": "Tax / Transfer Pricing Risk",
}

CATEGORY_TO_WEIGHT_KEY = {category: key for key, category in WEIGHT_KEY_TO_CATEGORY.items()}


def _entry(sector: str, weight_key: str, weight: float) -> dict:
    category = WEIGHT_KEY_TO_CATEGORY.get(weight_key)
    stats = RISK_CATEGORY_STATS.get(category, {})
    note = stats.get("sector_notes", {}).get(sector)
    headline = stats.get("headline") or "Sector baseline calibrated from SPARC risk engine weights."
    return {
        "weight": weight,
        "stat": note or headline,
        "forecast": stats.get("forecast") or "Pending underwriter calibration.",
        "source": stats.get("source") or "Pending underwriter calibration.",
    }


WEIGHTAGE_RATIONALE = {
    sector: {key: _entry(sector, key, weight) for key, weight in weights.items()}
    for sector, weights in SECTOR_PROFILES.items()
}

MULTIPLIER_RATIONALE = {
    "sdf_adjuster": {
        "formula": "1 + sdf_probability * 0.5",
        "stat": "Significant Data Fiduciary probability increases privacy and breach-notification exposure.",
        "forecast": "First SDF designations are expected to focus on large fintech, healthtech, HRtech, and edtech datasets.",
        "source": "DPDPA 2023; DPDP Rules 2025; SPARC calibration",
    },
    "stage_multiplier": {
        "formula": "Pre-seed 0.70 | Seed 0.90 | Series A 1.10 | Series B+ 1.30",
        "stat": "Later-stage startups face larger contracts, investors, governance duties, and potential damages.",
        "forecast": "Late-stage startups will face deeper compliance diligence from investors and enterprise customers.",
        "source": "SPARC risk_engine.py stage multipliers",
    },
    "data_sensitivity_multiplier": {
        "formula": "Low/Medium/High category multipliers on cyber, privacy, and compliance",
        "stat": "Higher sensitivity data increases breach cost, regulator attention, and fiduciary obligations.",
        "forecast": "DPDP enforcement will make sensitive-data controls more visible during vendor onboarding.",
        "source": "DPDPA 2023; IBM Cost of Data Breach India 2024; SPARC calibration",
    },
    "gig_adjuster": {
        "formula": "1 + gig_headcount_pct * 1.2, with state-footprint uplift",
        "stat": "Aggregator and platform-worker rules increase statutory and welfare obligations.",
        "forecast": "State gig worker acts and labour-code implementation will increase cover demand.",
        "source": "Social Security Code 2020; state gig worker legislation; SPARC calibration",
    },
    "hardware_adjuster": {
        "formula": "1 + hardware_software_split * 0.6",
        "stat": "Hardware, inventory, lab, and equipment exposure increases property and compliance risk.",
        "forecast": "BIS/QCO and product-safety enforcement will keep rising for hardware-linked startups.",
        "source": "BIS/QCO notifications; SPARC calibration",
    },
    "cbam_adjuster": {
        "formula": "1 + export_eu_pct * 1.5",
        "stat": "EU-export exposure increases CBAM, climate, and geopolitical compliance pressure.",
        "forecast": "CBAM and EU AI Act enforcement increase cross-border obligations through 2026.",
        "source": "EU CBAM; EU AI Act; SPARC calibration",
    },
    "ai_adjuster": {
        "formula": "1.3 if AI is in product, else 1.0",
        "stat": "AI features increase policy velocity, model-liability, and compliance uncertainty.",
        "forecast": "AI-specific governance rules will become more operational during 2026-27.",
        "source": "MeitY AI advisories; EU AI Act; SPARC calibration",
    },
    "governance_adjuster": {
        "formula": "1 + founder_concentration_index * 0.5 + fundraising-scale uplift",
        "stat": "Founder concentration and large fundraising increase governance and fraud exposure.",
        "forecast": "Investor diligence and board liability expectations will keep increasing.",
        "source": "SPARC risk_engine.py governance adjustment",
    },
    "brsr_adjuster": {
        "formula": "1.2 if listed-customer BRSR dependency is present",
        "stat": "Top listed customers push ESG evidence requirements down to suppliers.",
        "forecast": "Value-chain ESG diligence will expand in enterprise procurement.",
        "source": "SEBI BRSR value-chain guidance; SPARC calibration",
    },
    "climate_adjuster": {
        "formula": "Low 1.0 | Medium 1.2 | High 1.5 | Extreme 1.8",
        "stat": "Facility flood, heat, cyclone, and landslide exposure affects property and continuity risk.",
        "forecast": "Climate zoning will increasingly affect underwriting and pricing.",
        "source": "IMD/NDMA hazard frameworks; SPARC calibration",
    },
    "b2b_adjuster": {
        "formula": "1 + b2b_pct * 0.4",
        "stat": "Enterprise contracts create SLAs, indemnity obligations, and PI/E&O prerequisites.",
        "forecast": "B2B vendor insurance requirements will keep becoming standard in procurement.",
        "source": "SPARC risk_engine.py B2B adjustment",
    },
}


def get_score_rationale(sector: str, category_name: str) -> dict | None:
    key = CATEGORY_TO_WEIGHT_KEY.get(category_name)
    if not key:
        return None
    return WEIGHTAGE_RATIONALE.get(sector, {}).get(key)
