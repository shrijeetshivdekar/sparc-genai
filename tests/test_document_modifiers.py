"""Phase 9 unit tests — bundle-mapping invariant + trigger evaluation +
per-cover narrowing math.

Run: python -m pytest tests/test_document_modifiers.py -v
Or:  python tests/test_document_modifiers.py    (standalone)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pricing.document_modifier_engine import (
    evaluate_document_modifiers,
    aggregate_per_cover,
    evaluate_and_aggregate,
)
from pricing.financial_ratio_engine import (
    compute_per_cover_confidence,
    rank_global_upload_next,
)
from pricing.model import load_params


def _load_research_config() -> dict:
    return json.loads((ROOT / "research_config.json").read_text(encoding="utf-8"))


def _load_affinity() -> dict:
    return json.loads((ROOT / "pricing" / "cover_document_affinity.json").read_text(encoding="utf-8"))


def _all_cover_keys_from_bundles() -> set:
    cfg = _load_research_config()
    out: set = set()
    for bundle in (cfg.get("bundle_meta") or {}).values():
        for c in (bundle.get("components") or []):
            out.add(c)
    return out


def _all_standalone_cover_keys() -> set:
    """Covers exposed as standalone products via _BUNDLE_KEY_TO_PREMIUM_KEY."""
    from api.verified_analyze import _BUNDLE_KEY_TO_PREMIUM_KEY
    return set(_BUNDLE_KEY_TO_PREMIUM_KEY.keys())


# Existing short-LOB codes used in the pre-existing manual loadings catalog.
# These are intentionally distinct from bundle component keys and route via
# pricing.quote() / line_of_business. Our invariant only enforces that NEW
# trigger-bearing entries map to bundle keys.
_PRE_EXISTING_LOB_CODES = {"DO", "Cyber", "PI", "CGL", "EC", "GH", "GPA", "Crime", "Property", "MB"}


# ─── Test 1: Bundle-mapping invariant ────────────────────────────────────────

def test_doc_triggered_loadings_map_to_real_covers():
    """Every cover in a doc-triggered loading's `applies_to` must exist in at
    least one bundle's `components` list (research_config.json)."""
    params = load_params()
    catalog = params["loadings_discounts"]
    bundle_covers = _all_cover_keys_from_bundles()
    standalone_covers = _all_standalone_cover_keys()
    valid_covers = bundle_covers | standalone_covers

    orphans: list[tuple[str, str]] = []
    triggered_count = 0
    for key, entry in catalog.items():
        if not entry.get("trigger"):
            continue
        triggered_count += 1
        for cover in entry.get("applies_to") or []:
            if cover in _PRE_EXISTING_LOB_CODES:
                continue  # pre-existing namespace, allowed
            if cover not in valid_covers:
                orphans.append((key, cover))

    assert triggered_count >= 50, f"Expected >=50 doc-triggered loadings, got {triggered_count}"
    assert not orphans, (
        f"Doc-triggered loadings targeting phantom cover keys (not in any bundle):\n"
        + "\n".join(f"  - {k}: '{c}'" for k, c in orphans[:20])
    )
    print(f"✓ All {triggered_count} doc-triggered loadings target real bundle covers")


# ─── Test 2: Trigger evaluation ──────────────────────────────────────────────

def test_trigger_evaluator_fires_on_prior_cyber_claim():
    params = load_params()
    docs = {"prior_policy": {"cyber_claims_3yr": {"value": 1, "confidence": "extracted"}}}
    applied, agg = evaluate_and_aggregate(docs, {}, params["loadings_discounts"])
    keys = {m["key"] for m in applied}
    assert "policy_prior_cyber_claim_3yr" in keys
    assert agg["CYBER"]["multiplier"] == 1.5
    print(f"✓ Prior cyber claim → +50% CYBER loading")


def test_trigger_evaluator_fires_on_vapt_critical():
    params = load_params()
    docs = {"vapt_report": {"critical_count": {"value": 5}}}
    applied, agg = evaluate_and_aggregate(docs, {}, params["loadings_discounts"])
    keys = {m["key"] for m in applied}
    assert "vapt_critical_unpatched_3plus" in keys
    assert abs(agg["CYBER"]["multiplier"] - 1.4) < 0.001
    print(f"✓ VAPT 5 criticals → +40% CYBER loading")


def test_si_floor_override_from_unlimited_contract():
    params = load_params()
    docs = {"client_contract": {"unlimited_liability_flag": {"value": True}}}
    applied, agg = evaluate_and_aggregate(docs, {}, params["loadings_discounts"])
    keys = {m["key"] for m in applied}
    assert "contract_unlimited_liability" in keys
    assert agg["PI_TECH_EO"]["si_floor_inr"] == 100000000
    print(f"✓ Unlimited liability contract → ₹10 Cr SI floor on PI_TECH_EO")


def test_discount_fires_on_iso27001():
    params = load_params()
    docs = {"vapt_report": {"iso27001_or_soc2_active": {"value": True}}}
    applied, agg = evaluate_and_aggregate(docs, {}, params["loadings_discounts"])
    keys = {m["key"] for m in applied}
    assert "vapt_iso27001_or_soc2" in keys
    assert agg["CYBER"]["multiplier"] == 0.8  # 1 - 0.2 discount
    print(f"✓ ISO 27001/SOC 2 → −20% CYBER discount")


def test_mca_director_signal_fires():
    docs = {}
    mca_snap = {
        "director_resignations_24mo": 4,
        "directors_associated_struck_off_count": 0,
        "auditor_opinion_modified": False,
        "company_type": "private",
        "net_worth_cr": 15.0,
    }
    params = load_params()
    applied, agg = evaluate_and_aggregate(docs, mca_snap, params["loadings_discounts"])
    keys = {m["key"] for m in applied}
    assert "mca_director_serial_resigner" in keys
    assert abs(agg["D_AND_O"]["multiplier"] - 1.15) < 0.001
    print(f"✓ MCA serial resigner → +15% D_AND_O loading")


# ─── Test 3: Per-cover confidence narrowing ──────────────────────────────────

def test_confidence_narrows_as_docs_added():
    """Bands monotonically narrow as documents are added."""
    aff = _load_affinity()

    # Tier 1: nothing
    t1 = compute_per_cover_confidence({}, {}, aff)
    # Tier 2: financials
    t2 = compute_per_cover_confidence({
        "pl": {"revenue_cr": {"value": 10}, "net_profit_cr": {"value": 1}, "payroll_cr": {"value": 2}, "gross_profit_cr": {"value": 5}, "cogs_cr": {"value": 5}},
        "balance_sheet": {"total_assets_cr": {"value": 8}, "fixed_assets_cr": {"value": 3}, "equity_cr": {"value": 4}, "debt_cr": {"value": 2}, "current_assets_cr": {"value": 5}, "receivables_cr": {"value": 2}, "inventory_cr": {"value": 1}, "total_liabilities_cr": {"value": 4}},
    }, {}, aff)
    # Tier 3: + prior policy + client contract
    t3 = compute_per_cover_confidence({
        "pl": {"revenue_cr": {"value": 10}, "net_profit_cr": {"value": 1}, "payroll_cr": {"value": 2}, "gross_profit_cr": {"value": 5}, "cogs_cr": {"value": 5}},
        "balance_sheet": {"total_assets_cr": {"value": 8}, "fixed_assets_cr": {"value": 3}, "equity_cr": {"value": 4}, "debt_cr": {"value": 2}, "current_assets_cr": {"value": 5}, "receivables_cr": {"value": 2}, "inventory_cr": {"value": 1}, "total_liabilities_cr": {"value": 4}},
        "prior_policy": {"cyber_si": {"value": 2}, "cyber_claims_3yr": {"value": 0}, "cyber_ncd_years": {"value": 2}, "pi_si": {"value": 3}, "pi_claims_3yr": {"value": 0}, "pi_ncd_years": {"value": 2}, "pi_retroactive_years": {"value": 4}},
        "client_contract": {"liability_cap_inr": {"value": 50000000}, "unlimited_liability_flag": {"value": False}, "data_processor_role": {"value": True}, "sla_penalty_per_day_inr": {"value": 100000}, "foreign_jurisdiction_flag": {"value": False}, "retroactive_required": {"value": True}, "pii_volume_est": {"value": 50000}, "third_party_indemnity_flag": {"value": False}},
    }, {}, aff)

    for cover in ("CYBER", "PI_TECH_EO"):
        w1 = t1[cover]["width_pct"]
        w2 = t2[cover]["width_pct"]
        w3 = t3[cover]["width_pct"]
        assert w2 <= w1, f"{cover}: T2 ({w2}) should be ≤ T1 ({w1})"
        assert w3 <= w2, f"{cover}: T3 ({w3}) should be ≤ T2 ({w2})"
        print(f"✓ {cover}: T1=±{w1/2:.1f}% → T2=±{w2/2:.1f}% → T3=±{w3/2:.1f}%")


def test_upload_next_ranks_by_total_impact():
    aff = _load_affinity()
    conf = compute_per_cover_confidence({}, {}, aff)
    ranked = rank_global_upload_next(conf, aff, top_n=3)
    assert len(ranked) == 3
    # Prior policy or asset register should top the list (highest cross-cover impact)
    top = ranked[0]["doc_type"]
    assert top in {"prior_policy", "asset_register", "mca_filings"}, f"Unexpected top doc: {top}"
    print(f"✓ Top 3 upload-next: {[r['doc_type'] for r in ranked]}")


# ─── Test 4: Aggregation handles multi-cover loadings ────────────────────────

def test_aggregation_multiplies_per_cover():
    """A loading with applies_to=[A,B] should multiply both A and B."""
    catalog = {
        "test_load_AB": {
            "label": "Test", "value": 0.5, "direction": "loading",
            "applies_to": ["A", "B"],
            "trigger": {"source_doc": "x", "field": "f", "operator": "==", "value": True},
        }
    }
    docs = {"x": {"f": {"value": True}}}
    applied, agg = evaluate_and_aggregate(docs, {}, catalog)
    assert agg["A"]["multiplier"] == 1.5
    assert agg["B"]["multiplier"] == 1.5
    print("✓ Multi-cover applies_to fans out correctly")


if __name__ == "__main__":
    test_doc_triggered_loadings_map_to_real_covers()
    test_trigger_evaluator_fires_on_prior_cyber_claim()
    test_trigger_evaluator_fires_on_vapt_critical()
    test_si_floor_override_from_unlimited_contract()
    test_discount_fires_on_iso27001()
    test_mca_director_signal_fires()
    test_confidence_narrows_as_docs_added()
    test_upload_next_ranks_by_total_impact()
    test_aggregation_multiplies_per_cover()
    print("\nAll tests passed.")
