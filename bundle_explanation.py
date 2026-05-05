"""
bundle_explanation.py — Human-readable explanation layer for bundle_recommender_v2.

Generates:
  - Plain-English narrative for each BundleRecommendation
  - Coverage gap alerts (what this bundle does NOT cover)
  - Hard gate summaries (why certain products were excluded)
  - Selection rationale for variant choice within a family
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from bundle_recommender_v2 import BundleOutput, BundleRecommendation
from bundle_scoring_utils import BundleInputV2
from product_catalogue_v2 import PRODUCT_CATALOGUE_V2


# ---------------------------------------------------------------------------
# COVERAGE GAP LIBRARY
# ---------------------------------------------------------------------------
# Maps canonical_family → list of (gap_condition, gap_message) pairs.
# gap_condition is a lambda(BundleInputV2) -> bool
# gap_message is the warning to emit when the condition is True.

_COVERAGE_GAPS: Dict[str, List] = {
    "property_fire": [
        (
            lambda i: i.has_workforce and i.headcount_blue_collar > 0,
            "Property fire cover does not include Workers' Compensation. "
            "Add Employer's Liability / EC cover for blue-collar workers."
        ),
        (
            lambda i: i.domestic_shipments or i.export_shipments,
            "Fire cover does not extend to goods in transit. "
            "Add Marine Transit Insurance for shipment exposure."
        ),
    ],
    "cyber": [
        (
            lambda i: i.has_workforce,
            "Cyber Liability does not cover employee-driven fraud. "
            "Add Crime / Fidelity cover if internal fraud risk is material."
        ),
        (
            lambda i: i.any_physical_presence,
            "Cyber cover does not replace property insurance for physical damage to servers or network hardware. "
            "Ensure Property / EEI cover is also in place."
        ),
    ],
    "general_or_modular_liability": [
        (
            lambda i: i.has_workforce,
            "CGL / Public Liability does not satisfy the Employees' Compensation Act obligation. "
            "Place EC / WC separately for all workers."
        ),
        (
            lambda i: i.handles_personal_data or i.handles_financial_data,
            "CGL does not cover data breach or cyber incident liability. "
            "Add Cyber Liability for data-handling operations."
        ),
    ],
    "employee_health": [
        (
            lambda i: i.headcount_blue_collar > 0,
            "Group Health does not replace the statutory Workmen's Compensation obligation. "
            "Add Employee's Compensation for blue-collar workers."
        ),
    ],
    "employers_liability": [
        (
            lambda i: i.headcount_total >= 5,
            "Employee's Compensation is a statutory cover but does not provide healthcare benefits. "
            "Add Group Health Insurance for employee welfare and retention."
        ),
    ],
    "engineering_project": [
        (
            lambda i: i.domestic_shipments or i.import_dependency,
            "CAR/EAR policies typically exclude cargo in transit to the site. "
            "Add Marine Transit Insurance for equipment shipments."
        ),
        (
            lambda i: i.headcount_blue_collar > 0 or i.contractors_count > 0,
            "CAR third-party liability covers visitors but not the contractor's own workforce. "
            "Maintain separate EC / WC for construction workers."
        ),
    ],
    "marine_logistics_credit": [
        (
            lambda i: i.goods_vehicle_count > 0,
            "Marine Transit Insurance does not cover damage to the vehicle itself. "
            "Add a GCV / Fleet Motor policy for the goods-carrying vehicle fleet."
        ),
    ],
    "commercial_motor_fleet": [
        (
            lambda i: i.domestic_shipments,
            "Motor fleet policies cover vehicle damage and third-party liability, "
            "but goods carried are typically excluded. "
            "Add Marine Transit Insurance for cargo-in-transit cover."
        ),
    ],
}


# ---------------------------------------------------------------------------
# VARIANT SELECTION RATIONALE
# ---------------------------------------------------------------------------

_VARIANT_RATIONALE: Dict[str, str] = {
    "sookshma": "Selected the Sookshma (micro) variant because total insurable asset value is ≤ ₹5 Cr.",
    "laghu": "Selected the Laghu (small) variant because total insurable asset value is between ₹5 Cr and ₹50 Cr.",
    "industrial_all_risk": "Selected IAR because industrial premises with sum insured ≥ ₹50 Cr require industrial all-risk cover.",
    "mega": "Selected Fire Mega Risk for very large industrial risk (sum insured ≥ ₹100 Cr).",
    "all_risk": "Selected Property All Risk (broader accidental-damage cover) for electronics, labs, or R&D assets.",
    "elite_claims_made": "I-Elite CGL (claims-made) selected for high-headcount, high-regulatory-intensity businesses.",
    "elite_occurrence": "I-Elite CGL (occurrence) selected for businesses with long-tail physical-product liability.",
    "wc_ec": "Employee's Compensation / WC selected because of blue-collar or field headcount.",
    "gpa": "Group Personal Accident selected for broader workforce accident cover at low cost.",
    "floater": "Group Health Floater selected — dependants included, important for talent retention.",
    "super_top_up": "Super Top Up selected to augment an existing base Group Health policy.",
    "open_cover": "Marine Export/Import Open Cover selected for regular cross-border cargo shipments.",
    "inland_transit": "Marine Inland Transit selected for domestic goods movement.",
    "trade_credit": "Trade Credit Insurance selected due to material receivables on credit terms.",
    "healthcare_pi": "Healthcare Professional Indemnity selected for clinical / diagnostic operations.",
    "fs_pi": "Financial Services Professional Indemnity selected for RBI/SEBI-regulated fintech.",
    "drone": "RPA Insurance selected because DGCA mandates third-party liability for commercial drone ops.",
    "rw": "Representation & Warranty Insurance selected because an M&A/transaction context is flagged.",
    "title": "Title Insurance selected because real-estate development activity is present.",
    "surety": "Surety Insurance selected because a contract bid or performance bond requirement is indicated.",
    "alop": "ALOP (Advance Loss of Profit) selected because high capex project value implies material delay risk.",
    "advance": "MSME Suraksha Kavach Advance selected for startups with physical ops and inventory.",
    "package": "Entertainment Production Package selected for event / media production operations.",
    "card_commercial": "Card Package Commercial selected for a card-issuing or ATM programme.",
    "payment_protection_commercial": "Consumer Payment Protection Commercial selected for payment instrument operators.",
    "telecom": "Cellular Network Insurance selected because telecom network assets are declared.",
}


def _variant_rationale(variant_type: str) -> Optional[str]:
    return _VARIANT_RATIONALE.get(variant_type)


# ---------------------------------------------------------------------------
# NARRATIVE GENERATOR
# ---------------------------------------------------------------------------

def generate_bundle_narrative(
    rec: BundleRecommendation,
    inp: BundleInputV2,
) -> str:
    """
    Return a single paragraph narrative explaining a recommendation.
    """
    pm = PRODUCT_CATALOGUE_V2.get(rec.product_key, {})
    variant = pm.get("variant_type", "standard")
    rationale = _variant_rationale(variant)

    lines = [
        f"**{rec.product_name}** — confidence: {rec.confidence.upper()} (score {rec.score:.0f}/100)."
    ]

    if rec.reasons:
        lines.append("Why recommended: " + " ".join(rec.reasons))

    if rationale:
        lines.append(f"Variant selected: {rationale}")

    if rec.paired_with:
        lines.append(
            "Complement with: " + ", ".join(rec.paired_with) + "."
        )

    if rec.missing_inputs:
        lines.append(
            "To refine this recommendation, provide: "
            + "; ".join(rec.missing_inputs)
        )

    return " ".join(lines)


# ---------------------------------------------------------------------------
# COVERAGE GAP ALERTS
# ---------------------------------------------------------------------------

def generate_gap_alerts(
    recs: List[BundleRecommendation],
    inp: BundleInputV2,
) -> List[str]:
    """
    For each recommended family, emit coverage gap warnings where relevant.
    """
    alerts: List[str] = []
    families_recommended = {r.canonical_family for r in recs}

    for family in families_recommended:
        for condition, message in _COVERAGE_GAPS.get(family, []):
            try:
                if condition(inp):
                    alerts.append(f"[{family}] {message}")
            except Exception:
                pass

    return alerts


# ---------------------------------------------------------------------------
# HARD GATE SUMMARY
# ---------------------------------------------------------------------------

def generate_gate_summary(
    recs: List[BundleRecommendation],
) -> Dict[str, List[str]]:
    """
    Return a dict of family → list of products blocked by hard gates,
    so the caller can explain to users why certain products were not offered.
    """
    gate_summary: Dict[str, List[str]] = {}
    for rec in recs:
        if rec.hard_gate_blocks:
            gate_summary[rec.canonical_family] = rec.hard_gate_blocks
    return gate_summary


# ---------------------------------------------------------------------------
# FULL EXPLANATION BUNDLE
# ---------------------------------------------------------------------------

def explain_bundle_output(
    output: BundleOutput,
    inp: BundleInputV2,
) -> Dict[str, Any]:
    """
    Produce a fully-explained output dict wrapping BundleOutput with:
      - narrative per recommendation
      - coverage gap alerts
      - hard gate summary
    """
    all_recs = output.primary_bundles + output.secondary_bundles
    narratives_primary = [
        generate_bundle_narrative(r, inp) for r in output.primary_bundles
    ]
    narratives_secondary = [
        generate_bundle_narrative(r, inp) for r in output.secondary_bundles
    ]
    gaps = generate_gap_alerts(all_recs, inp)
    gate_summary = generate_gate_summary(all_recs)

    return {
        "primary_bundles": [
            {**r.to_dict(), "narrative": narratives_primary[i]}
            for i, r in enumerate(output.primary_bundles)
        ],
        "secondary_bundles": [
            {**r.to_dict(), "narrative": narratives_secondary[i]}
            for i, r in enumerate(output.secondary_bundles)
        ],
        "coverage_gap_alerts": gaps,
        "gate_summary": gate_summary,
    }
