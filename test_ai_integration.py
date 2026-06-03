"""Test AI recommender on both NeuralPay (Fintech) and 3ev (Manufacturing)."""
import json, os, sys
sys.path.insert(0, ".")

def _v(value): return {"value": value, "source": "test"}

NEURALPAY = {
    "extraction_summary": {
        "revenue_cr": _v(18.2), "net_profit_cr": _v(-3.27), "ebitda_cr": _v(-1.85),
        "equity_cr": _v(4.0), "debt_cr": _v(3.0), "employee_benefit_cr": _v(7.4),
        "fixed_assets_cr": _v(2.8), "trade_receivables_cr": _v(3.65),
    },
    "categorical_inferences": {
        "sector": "Fintech", "operations": "Digital-only",
        "data_sensitivity": "High", "ai_in_product": True,
        "regulatory_flags": ["GST", "PCI-DSS", "RBI"],
    },
    "verified_assessment": {"financial_ratios": {
        "net_profit_margin_pct": {"value": -18.0, "band": "burn"},
        "debt_equity":           {"value": 0.75,  "band": "moderate"},
        "current_ratio":         {"value": 1.09,  "band": "tight"},
        "payroll_rev_pct":       {"value": 40.7,  "band": "people_heavy"},
    }},
    "documents_extracted": {
        "vapt_report":    {"critical_count": _v(4), "mfa_enabled": _v(False), "endpoint_protection_deployed": _v(False), "backup_rto_hours": _v(96), "third_party_access_count": _v(7)},
        "client_contract":{"retroactive_required": _v(True), "foreign_jurisdiction_flag": _v(True), "data_processor_role": _v(True), "third_party_indemnity_flag": _v(True)},
        "prior_policy":   {"lob": _v("Cyber Liability"), "policy_number": _v("ILCY-2024-MH-0041293"), "cyber_si": _v(2), "cyber_claims_3yr": _v(1), "lapsed": _v(True)},
        "gst_returns":    {"state_count": _v(8), "b2b_concentration_top3": _v(0.962), "has_us_uk_export": _v(True)},
        "asset_register": {"total_replacement_cr": _v(2.1), "oem_service_contracts": _v(False)},
    },
}

EV_3EV = {
    "extraction_summary": {
        "revenue_cr": _v(28.52), "net_profit_cr": _v(-9.68), "ebitda_cr": _v(-6.88),
        "equity_cr": _v(4.3), "debt_cr": _v(8.95), "employee_benefit_cr": _v(5.85),
        "fixed_assets_cr": _v(10.3), "trade_receivables_cr": _v(2.1), "inventory_cr": _v(6.4),
    },
    "categorical_inferences": {
        "sector": "Manufacturing", "operations": "Physical-only",
        "data_sensitivity": "Low", "ai_in_product": False,
        "regulatory_flags": ["GST"],
    },
    "verified_assessment": {"financial_ratios": {
        "net_profit_margin_pct": {"value": -33.9, "band": "burn"},
        "debt_equity":           {"value": 2.08,  "band": "leveraged"},
        "current_ratio":         {"value": 0.68,  "band": "liquidity_stress"},
        "asset_intensity_pct":   {"value": 45.2,  "band": "asset_heavy"},
    }},
    "documents_extracted": {
        "prior_policy":   {"lob": _v("Fire/Property"), "policy_number": _v("IL-IAR-KA-2024-009873"), "property_si": _v(23.6), "property_claims_3yr": _v(2), "premium_lakh": _v(22.24), "lapsed": _v(True)},
        "vapt_report":    {"critical_count": _v(4), "high_count": _v(13), "mfa_enabled": _v(False), "endpoint_protection_deployed": _v(False), "backup_rto_hours": _v(96), "third_party_access_count": _v(9)},
        "gst_returns":    {"state_count": _v(6), "b2b_concentration_top3": _v(0.575), "b2b_invoices_cr": _v(25.97)},
        "asset_register": {"total_replacement_cr": _v(18.15), "location_count": _v(1), "oem_service_contracts": _v(False)},
    },
}

def run(label, payload):
    from api.ai_recommender import recommend
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    r = recommend(
        payload["extraction_summary"],
        payload["categorical_inferences"],
        payload.get("verified_assessment", {}),
        payload["documents_extracted"],
    )
    if not r:
        print("FAILED"); return
    u = r.get("_usage", {})
    print(f"Tokens: in={u.get('input_tokens')} out={u.get('output_tokens')}  cost=${u.get('cost_usd',0):.5f}")
    b = r.get("bundle", {})
    print(f"\nBUNDLE: {b.get('key')} ({b.get('fit_pct')}%)")
    print(f"  {b.get('why')}")
    print("\nTOP 5 ADDITIONAL:")
    for p in r.get("additional", []):
        print(f"  {p.get('rank')}. [{p.get('urgency'):8s}] {p.get('product')} — {p.get('why')}")
    print("\nCRITICAL GAPS:")
    for g in r.get("critical_gaps", []):
        print(f"  ✗ {g.get('cover')} ({g.get('issue')}) — {g.get('evidence')}")

run("NeuralPay — Fintech, Digital-only", NEURALPAY)
run("3ev Industries — EV Manufacturing, Physical-only", EV_3EV)
