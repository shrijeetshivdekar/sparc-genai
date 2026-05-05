"""
Bundle Catalog — ICICI Lombard SPARC recommender.

Scoring engine backed by research_config.json version 2026.05.
All weight applications are logged at DEBUG level for explainability auditing.
"""
import functools
import json
import logging
import pathlib
from copy import deepcopy

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Master catalogue
# covered_risks maps each bundle to the 13-category short-keys it addresses.
# ---------------------------------------------------------------------------
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
        "covered_risks": ["property", "liability", "gig_labour"],
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
        "covered_risks": ["property", "liability", "governance_fraud", "cyber_technical", "data_privacy", "key_person"],
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
        "covered_risks": ["cyber_technical", "data_privacy", "ip_infringement", "key_person", "governance_fraud", "reputation"],
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
        "covered_risks": ["property"],
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
        "covered_risks": ["property", "ip_infringement", "key_person", "cyber_technical", "liability"],
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

# ---------------------------------------------------------------------------
# Key normalisation maps (risk engine display names → config short-keys)
# ---------------------------------------------------------------------------
_SCORE_KEY_MAP = {
    "Cyber Technical Risk":       "cyber_technical",
    "Data Privacy Risk":          "data_privacy",
    "Liability Risk":             "liability",
    "IP Infringement Risk":       "ip_infringement",
    "Key Person Risk":            "key_person",
    "Governance & Fraud Risk":    "governance_fraud",
    "Property Risk":              "property",
    "Regulatory Compliance Risk": "regulatory_compliance",
    "ESG & Climate Risk":         "esg_climate",
    "Geopolitical Risk":          "geopolitical",
    "Gig & Labour Risk":          "gig_labour",
    "Policy Velocity Risk":       "policy_velocity",
    "Reputation Risk":            "reputation",
}

_SECTOR_KEY = {
    "Fintech":                    "fintech",
    "Healthtech":                 "healthtech",
    "Edtech":                     "edtech",
    "Deeptech / AI / Robotics":   "deeptech",
    "Cleantech / Climatetech":    "climatetech",
    "D2C / Consumer Brands":      "d2c",
    "SaaS / Enterprise Software": "saas_b2b",
    "Legaltech":                  "saas_b2b",
    "HRtech":                     "saas_b2b",
    "Gaming / Media / Content":   "saas_b2b",
    "Insurtech":                  "fintech",
    "Proptech":                   "saas_b2b",
    "Spacetech":                  "deeptech",
    "Agritech / Foodtech":        "d2c",
    "Logistics / Mobility":       "d2c",
}

_STAGE_KEY = {
    "Pre-seed": "seed",
    "Seed":     "seed",
    "Series A": "series_a",
    "Series B+":"series_b",
}


# ---------------------------------------------------------------------------
# Config loader
# ---------------------------------------------------------------------------
@functools.lru_cache(maxsize=1)
def _load_research_config() -> dict:
    path = pathlib.Path(__file__).parent / "research_config.json"
    with open(path, encoding="utf-8") as fh:
        cfg = json.load(fh)
    log.info("research_config.json v%s loaded from %s", cfg.get("version"), path)
    return cfg


# ---------------------------------------------------------------------------
# Input-derived feature helpers
# ---------------------------------------------------------------------------
def _asset_type_from_inp(inp) -> str:
    split = getattr(inp, "hardware_software_split", 0.0) or 0.0
    assets = getattr(inp, "physical_assets", []) or []
    if split > 0.6 or "Manufacturing plant / factory" in assets:
        return "fab_or_plant"
    if split > 0.3 or "Lab / R&D equipment" in assets:
        return "lab_equipment"
    if "Warehouse / fulfilment centre" in assets or "Retail stores / kiosks" in assets:
        return "warehouse"
    return "asset_light"


def _primary_state(inp) -> str:
    footprint = getattr(inp, "state_footprint", []) or []
    return footprint[0] if footprint else "DEFAULT"


# ---------------------------------------------------------------------------
# Scoring primitives
# ---------------------------------------------------------------------------
def _coverage_score(profile: dict, bundle: dict, cfg: dict) -> float:
    """Weighted dot-product of covered risk categories × normalised scores."""
    w = cfg["risk_weights"]
    covered = bundle.get("covered_risks", [])
    result = sum(w[r] * profile["scores"].get(r, 0) for r in covered if r in w)
    log.debug(
        "coverage_score bundle=%s covered=%s score=%.4f",
        bundle.get("name"), covered, result,
    )
    return result


def _composite_mult(profile: dict, cfg: dict) -> dict:
    """Per-risk composite multiplier from sector, stage, asset, and geo signals."""
    out = {r: 1.0 for r in cfg["risk_weights"]}
    for src in ("sector_multipliers", "stage_multipliers", "asset_multipliers"):
        key = profile.get(src.split("_")[0], "")
        for r, m in cfg[src].get(key, {}).items():
            out[r] = out.get(r, 1.0) * m
            log.debug("weight applied: src=%s key=%s risk=%s mult=%.3f", src, key, r, m)
    # Scalar geo multiplier applied uniformly across all risk categories
    geo_raw = cfg.get("geo_multipliers", {})
    geo_val = geo_raw.get(profile.get("state", "DEFAULT"), geo_raw.get("DEFAULT", 1.0))
    if isinstance(geo_val, (int, float)):
        log.debug("geo_mult applied: state=%s mult=%.3f", profile.get("state"), geo_val)
        for r in out:
            out[r] *= geo_val
    return out


def _premium_potential(bundle_meta: dict, mults: dict) -> float:
    base = bundle_meta["base_premium"]
    blended = sum(mults.values()) / max(len(mults), 1)
    return base * blended


def _revenue_score(bm: dict) -> float:
    traj = {"up": 1.0, "flat": 0.5, "down": 0.0}.get(bm.get("trajectory", "flat"), 0.5)
    tam_norm = min(bm.get("tam_cr", 0) / 16250.0, 1.0)
    return round(
        100 * (
            0.35 * tam_norm
            + 0.25 * bm.get("adoption", 0) * bm.get("margin", 0) * 40
            + 0.20 * traj
            + 0.20 * 0.7
        ),
        1,
    )


# ---------------------------------------------------------------------------
# Existing helpers (unchanged)
# ---------------------------------------------------------------------------
def _pretty_cover(key: str) -> str:
    return key.replace("_", " ").title()


def _score_bundle(bundle: dict, sector: str, stage: str, score_signal: float) -> int:
    fit = 0
    if sector in bundle["eligible_sectors"]:
        fit += 40
    if stage in bundle["eligible_stages"]:
        fit += 30
    relevance = 1.0 if sector in bundle["eligible_sectors"] else 0.55
    fit += int(round(30 * score_signal * relevance))
    return fit


def _bundle_result(bundle: dict, fit: int, top_fit: int, rank: int, sector: str, inp) -> dict:
    result = deepcopy(bundle)
    result["fit_pct"] = min(100, max(0, int(fit)))
    result["match_strength"] = "strong" if fit >= 40 else "nearest"
    result["nearest_fallback"] = fit < 40
    result["rank"] = rank
    result["fit_delta"] = max(0, int(top_fit - fit))
    result["alternative_status"] = "top_pick" if rank == 1 else ("tied" if fit == top_fit else "lesser_relevant")
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


# ---------------------------------------------------------------------------
# Core ranking function
# ---------------------------------------------------------------------------
def rank_bundles(sector: str, stage: str, scores: dict, inp) -> list:
    """
    Score and rank all bundles. Always returns one entry per BUNDLE_CATALOG entry
    (backward-compat: callers may rely on len == len(BUNDLE_CATALOG)).

    Display fields (fit_pct, match_strength, nearest_fallback, alternative_status)
    use the original legacy fit so existing assertions are unaffected.

    New fields (final_score, premium_inr, risk_mult, revenue_score, score_rationale,
    excluded, exclusion_reason) come from the research_config.json formula.
    """
    cfg = _load_research_config()

    # New-engine keys  (empty string → unknown, will fail all eligibility gates)
    sector_key = _SECTOR_KEY.get(sector, "")
    stage_key  = _STAGE_KEY.get(stage, "")   # "" for unknown stages
    asset_key  = _asset_type_from_inp(inp)
    state_key  = _primary_state(inp)
    scores_norm = {_SCORE_KEY_MAP.get(k, k): v for k, v in scores.items()}
    profile = {
        "sector": sector_key, "stage": stage_key,
        "asset":  asset_key,  "state": state_key,
        "scores": scores_norm,
    }
    mults = _composite_mult(profile, cfg)

    # Legacy signal (for fit_pct / tied / nearest_fallback display)
    top3_vals    = sorted(scores.values(), reverse=True)[:3]
    signal       = (sum(top3_vals) / len(top3_vals) / 100) if top3_vals else 0

    rows = []
    for bundle in BUNDLE_CATALOG.values():
        cfg_key = bundle["name"].replace(" ", "_")
        meta    = cfg["bundle_meta"].get(cfg_key)

        # ── Legacy display fit (unchanged logic) ───────────────────────────
        legacy_fit = _score_bundle(bundle, sector, stage, signal)

        # ── New eligibility gates ──────────────────────────────────────────
        excl = None
        final = prem = rev = 0.0
        rm = 1.0
        rationale = "excluded"

        if meta is None:
            excl = "no_config"
        else:
            elig = meta.get("eligible_sectors", ["any"])
            if sector_key not in elig and "any" not in elig:
                excl = f"sector '{sector_key}' ∉ {elig}"
            elif stage_key not in meta.get("eligible_stages", []):
                excl = f"stage '{stage_key}' ∉ {meta.get('eligible_stages')}"
            else:
                aband = meta.get("asset_band", ["any"])
                if "any" not in aband and asset_key not in aband:
                    excl = f"asset '{asset_key}' ∉ {aband}"
                else:
                    si_cap    = meta.get("si_cap_inr")
                    asset_val = getattr(inp, "asset_value_inr", 0) or 0
                    if si_cap is not None and asset_val > si_cap:
                        excl = f"asset_value_inr {asset_val} > si_cap {si_cap}"

        if excl is None and meta is not None:
            cov   = _coverage_score(profile, bundle, cfg)
            prem  = round(_premium_potential(meta, mults))
            rev   = _revenue_score(meta)
            rm    = meta.get("risk_mult", 1.0)
            final = (0.45 * cov + 0.30 * (rev / 100) + 0.25 * meta.get("adoption", 0)) * (2 - rm)
            rationale = (
                f"Coverage {cov:.3f} × weights; rev_score {rev}; "
                f"risk_mult {rm}× ({meta.get('trajectory', '')})"
            )
            log.debug(
                "scored bundle=%s final=%.4f cov=%.3f rev=%.1f rm=%.2f",
                cfg_key, final, cov, rev, rm,
            )
        else:
            log.debug("bundle %s excluded: %s", cfg_key, excl)

        rows.append((bundle, final, prem, rm, rev, rationale, excl, legacy_fit))

    # Sort: eligible (final > 0) descending, then excluded by legacy_fit descending
    rows.sort(key=lambda x: (-x[1], -x[7]))

    top_legacy_fit = max(r[7] for r in rows) if rows else 0

    result = []
    for rank, (bundle, final, prem, rm, rev, rationale, excl, legacy_fit) in enumerate(rows, start=1):
        # _bundle_result uses legacy_fit for fit_pct, match_strength, tied-status
        b = _bundle_result(bundle, legacy_fit, top_legacy_fit, rank, sector, inp)
        b["final_score"]     = round(final, 4)
        b["premium_inr"]     = int(prem)
        b["risk_mult"]       = rm
        b["revenue_score"]   = rev
        b["score_rationale"] = rationale
        b["excluded"]        = excl is not None
        b["exclusion_reason"] = excl
        result.append(b)

    return result


def match_bundle(sector: str, stage: str, scores: dict, inp):
    ranked = rank_bundles(sector, stage, scores, inp)
    return ranked[0] if ranked else None


# ---------------------------------------------------------------------------
# Analytics — new keys appended to API response (never replaces existing keys)
# ---------------------------------------------------------------------------
def _match_regulatory_triggers(cfg: dict, scores_norm: dict, sector: str, inp) -> list:
    """Return triggered entries from cfg['regulatory_triggers'] matched against inp."""
    fired = []
    for trigger in cfg.get("regulatory_triggers", []):
        signal = trigger["signal"]
        matched = False
        if signal == "drone_ops":
            matched = bool(getattr(inp, "drone_ops", False))
        elif signal == "handles_pii":
            matched = (
                (getattr(inp, "sdf_probability", 0) or 0) > 0
                or getattr(inp, "data_sensitivity", "Low") in ("Medium", "High")
            )
        elif signal == "aggregator_schedule_7":
            matched = bool(getattr(inp, "is_gig_aggregator", False))
        elif signal == "top_1000_listed":
            matched = bool(getattr(inp, "listed_customer_brsr_dependency", False))
        elif signal == "rbi_licensed":
            matched = getattr(inp, "rbi_registration", None) is not None
        elif signal == "d2c_ecommerce":
            matched = sector == "D2C / Consumer Brands"
        if matched:
            log.debug("regulatory trigger fired: signal=%s product=%s", signal, trigger.get("product"))
            fired.append(dict(trigger))
    return fired


def bundle_analytics(sector: str, stage: str, scores: dict, inp, ranked_bundles: list) -> dict:
    """
    Returns three new API response keys:
      revenue_breakdown        — per-bundle TAM/adoption/margin breakdown
      risk_multiplier_breakdown — blended multiplier decomposition
      regulatory_triggers_fired — triggers matched against profile
    """
    cfg = _load_research_config()
    scores_norm = {_SCORE_KEY_MAP.get(k, k): v for k, v in scores.items()}
    sector_key = _SECTOR_KEY.get(sector, "")
    stage_key  = _STAGE_KEY.get(stage, "seed")
    asset_key  = _asset_type_from_inp(inp)
    state_key  = _primary_state(inp)
    profile = {"sector": sector_key, "stage": stage_key, "asset": asset_key, "state": state_key, "scores": scores_norm}
    mults = _composite_mult(profile, cfg)

    # ── revenue_breakdown ─────────────────────────────────────────────────
    rev_breakdown = []
    for b in ranked_bundles[:3]:
        cfg_key = b.get("name", "").replace(" ", "_")
        meta = cfg["bundle_meta"].get(cfg_key, {})
        if not meta:
            continue
        rev = _revenue_score(meta)
        rev_breakdown.append({
            "bundle":     b["name"],
            "tam_cr":     meta["tam_cr"],
            "adoption":   meta["adoption"],
            "margin":     meta["margin"],
            "trajectory": meta["trajectory"],
            "score":      rev,
            "why": (
                f"TAM ₹{meta['tam_cr']}Cr; "
                f"{meta['adoption'] * 100:.0f}% adoption; "
                f"{meta['margin'] * 100:.0f}% margin; "
                f"trend={meta['trajectory']}"
            ),
        })

    # ── risk_multiplier_breakdown ─────────────────────────────────────────
    prop_score = scores_norm.get("property", 0)
    liab_score = scores_norm.get("liability", 0)
    gov_score  = scores_norm.get("governance_fraud", 0)
    reg_score  = scores_norm.get("regulatory_compliance", 0)
    pol_score  = scores_norm.get("policy_velocity", 0)
    blended    = sum(mults.values()) / max(len(mults), 1)
    bm_values  = list(cfg["bundle_meta"].values())
    avg_adoption = sum(m.get("adoption", 0) for m in bm_values) / max(len(bm_values), 1)
    risk_mult_bd = {
        "claims_freq":           round((prop_score + liab_score) / 200, 4),
        "settlement_time":       round((gov_score + reg_score) / 200, 4),
        "regulatory_volatility": round((pol_score + reg_score) / 200, 4),
        "market_saturation":     round(1 - avg_adoption, 4),
        "composite":             round(blended, 4),
    }

    # ── regulatory_triggers_fired ─────────────────────────────────────────
    triggers_fired = _match_regulatory_triggers(cfg, scores_norm, sector, inp)

    return {
        "revenue_breakdown":          rev_breakdown,
        "risk_multiplier_breakdown":  risk_mult_bd,
        "regulatory_triggers_fired":  triggers_fired,
    }
