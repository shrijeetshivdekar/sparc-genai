"""Quick test — Gully Labs D2C sneaker brand."""
import sys; sys.path.insert(0, ".")
def _v(val): return {"value": val, "source": "test"}
from api.ai_recommender import recommend

extracts = {
    "revenue_cr": _v(30.0), "net_profit_cr": _v(-3.0), "equity_cr": _v(6.7),
    "debt_cr": _v(2.7), "employee_benefit_cr": _v(5.85),
    "fixed_assets_cr": _v(2.35), "trade_receivables_cr": _v(2.1), "inventory_cr": _v(4.2),
}
inferences = {
    "sector": "D2C / Consumer Brands", "operations": "Hybrid",
    "data_sensitivity": "Medium", "ai_in_product": False,
    "regulatory_flags": ["GST", "PF/ESI"],
}
verified = {"financial_ratios": {
    "net_profit_margin_pct": {"value": -10.0, "band": "burn"},
    "debt_equity":           {"value": 0.40,  "band": "conservative"},
    "current_ratio":         {"value": 1.22,  "band": "tight"},
}}
docs = {
    "prior_policy":    {"policy_number": _v("ILCGL-2024-UP-0091842-SAMPLE"), "lob": _v("Fire/Property"), "property_si": _v(4.75), "property_claims_3yr": _v(1), "lapsed": _v(True)},
    "client_contract": {"retroactive_required": _v(True), "foreign_jurisdiction_flag": _v(True), "data_processor_role": _v(True), "third_party_indemnity_flag": _v(True), "governing_law": _v("New York")},
    "vapt_report":     {"critical_count": _v(3), "mfa_enabled": _v(False), "endpoint_protection_deployed": _v(True)},
    "gst_returns":     {"state_count": _v(8), "b2b_concentration_top3": _v(0.9), "has_us_uk_export": _v(True)},
    "asset_register":  {"total_replacement_cr": _v(2.168), "location_count": _v(5), "oem_service_contracts": _v(False)},
}

r = recommend(extracts, inferences, verified, docs)
u = r.get("_usage", {})
print(f"Tokens: {u.get('input_tokens')} in / {u.get('output_tokens')} out  cost=${u.get('cost_usd',0):.5f}\n")
b = r.get("bundle", {})
print(f"BUNDLE: {b.get('key')} ({b.get('fit_pct')}%)")
print(f"  {b.get('why')}\n")
print("TOP 5:")
for p in r.get("additional", []):
    print(f"  {p['rank']}. [{p['urgency']:8}] {p['product']} — {p['why']}")
print("\nGAPS:")
for g in r.get("critical_gaps", []):
    print(f"  x {g['cover']} ({g['issue']}) — {g['evidence']}")
