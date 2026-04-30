CUSTOM_PRODUCT_TRIGGERS = {
    "ai_model_performance_parametric": {
        "trigger_conditions": {
            "ai_tier": ["Foundational", "Applied"],
            "min_score": {"IP Infringement Risk": 75, "Liability Risk": 70},
        },
        "description": "Parametric AI model performance warranty that pays on measurable accuracy degradation, hallucination liability, training-data IP claims, or algorithmic bias claims.",
        "global_precedent": "Armilla AI Warranty (Lloyd's) / Munich Re aiSure",
        "irdai_path": "IRDAI Sandbox or Lloyd's India placement",
        "estimated_market_size": "INR 200-500 cr TAM by 2027",
        "sectors": ["Deeptech / AI / Robotics", "SaaS / Enterprise Software", "Healthtech", "Fintech"],
    },
    "quantum_cryptographic_liability": {
        "trigger_conditions": {
            "min_score": {"Cyber Technical Risk": 80, "IP Infringement Risk": 75},
            "ai_tier": ["Foundational"],
        },
        "description": "Covers cryptographic obsolescence and harvest-now-decrypt-later liability once quantum computing weakens current encryption.",
        "global_precedent": "IBM Quantum Risk Advisory / UK NCSC post-quantum guidance",
        "irdai_path": "Lloyd's India or IRDAI Sandbox",
        "estimated_market_size": "INR 50-150 cr TAM by 2028",
        "sectors": ["Fintech", "Healthtech", "Deeptech / AI / Robotics", "SaaS / Enterprise Software"],
    },
    "cbam_carbon_levy_parametric": {
        "trigger_conditions": {
            "min_score": {"ESG & Climate Risk": 70, "Geopolitical Risk": 65},
            "export_eu_pct_min": 0.10,
        },
        "description": "Parametric cover paying when EU CBAM levies materially exceed projected rates.",
        "global_precedent": "Kita Carbon Insurance / Oka carbon credit covers",
        "irdai_path": "IRDAI Sandbox parametric structure",
        "estimated_market_size": "INR 100-300 cr TAM by 2027",
        "sectors": ["Cleantech / Climatetech", "D2C / Consumer Brands", "Agritech", "Logistics / Mobility"],
    },
    "gig_platform_wage_protection": {
        "trigger_conditions": {
            "min_score": {"Gig & Labour Risk": 75, "Regulatory Compliance Risk": 70},
            "gig_headcount_pct_min": 0.30,
        },
        "description": "Income replacement cover for gig/platform workers when illness, accident, or platform suspension prevents work.",
        "global_precedent": "Deliveroo x Zurich / Uber x AXA / Stride Health",
        "irdai_path": "IRDAI Sandbox or micro-insurance route",
        "estimated_market_size": "INR 300-800 cr TAM by 2027",
        "sectors": ["Logistics / Mobility", "Foodtech / Cloud Kitchen", "HRtech", "Agritech"],
    },
    "carbon_credit_invalidation": {
        "trigger_conditions": {
            "min_score": {"ESG & Climate Risk": 75},
            "export_eu_pct_min": 0.05,
        },
        "description": "Covers carbon-credit invalidation from additionality failures, double-counting, registry fraud, or retroactive decertification.",
        "global_precedent": "Kita Carbon Credit Invalidation Cover / Oka Re",
        "irdai_path": "Lloyd's India syndicate placement or IRDAI Sandbox",
        "estimated_market_size": "INR 50-200 cr TAM by 2027",
        "sectors": ["Cleantech / Climatetech", "Agritech"],
    },
}


def _name_from_key(key: str) -> str:
    return key.replace("_", " ").title()


def check_custom_triggers(scores: dict, inp) -> list[dict]:
    triggered = []
    for key, trigger in CUSTOM_PRODUCT_TRIGGERS.items():
        cond = trigger["trigger_conditions"]
        reasons = []
        if inp.sector not in trigger.get("sectors", []):
            continue
        if not all(scores.get(cat, 0) >= minimum for cat, minimum in cond.get("min_score", {}).items()):
            continue
        for cat, minimum in cond.get("min_score", {}).items():
            reasons.append(f"{cat}: {scores.get(cat, 0):.0f} >= trigger threshold {minimum}")
        if "ai_tier" in cond and getattr(inp, "ai_tier", "None") not in cond["ai_tier"]:
            continue
        if "export_eu_pct_min" in cond:
            if getattr(inp, "export_eu_pct", 0.0) < cond["export_eu_pct_min"]:
                continue
            reasons.append(f"EU revenue {inp.export_eu_pct * 100:.0f}% >= threshold {cond['export_eu_pct_min'] * 100:.0f}%")
        if "gig_headcount_pct_min" in cond:
            if getattr(inp, "gig_headcount_pct", 0.0) < cond["gig_headcount_pct_min"]:
                continue
            reasons.append(f"Gig workforce {inp.gig_headcount_pct * 100:.0f}% >= threshold {cond['gig_headcount_pct_min'] * 100:.0f}%")
        triggered.append({
            "key": key,
            "name": _name_from_key(key),
            "description": trigger["description"],
            "global_precedent": trigger["global_precedent"],
            "irdai_path": trigger["irdai_path"],
            "estimated_market_size": trigger["estimated_market_size"],
            "triggered_by": reasons,
        })
    return triggered
