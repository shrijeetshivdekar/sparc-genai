import sys
sys.path.insert(0, ".")
from quote_prefill import suggest_quote_inputs
from pricing_engine import price_output_stage, infer_underwriting_inputs

profile = {
    "sector": "D2C / Consumer Brands",
    "stage": "Series B+",
    "team_size": "51-200",
    "revenue_cr": 320,
    "data_sensitivity": "Medium",
    "b2b_pct": 0.1,
    "physical_assets": ["Office / co-working space", "Warehouse / fulfilment centre"],
    "data_handled": ["Customer PII (name, email, phone)", "Payment card data"],
}

print("=== suggest_quote_inputs (key fields) ===")
s = suggest_quote_inputs(profile)
for k in ("cyber_limit_cr", "pi_limit_cr", "cargo_turnover_cr", "payroll_cr"):
    v = s.get(k, {})
    print(f"  {k}: {v.get('value')} (confidence={v.get('confidence')})")

print()
print("=== infer_underwriting_inputs ===")
inp = infer_underwriting_inputs(profile)
for k, v in inp.items():
    if not k.startswith("_"):
        print(f"  {k}: {v}")

print()
# Build full profile with inferred inputs merged for full pricing
profile_full = dict(profile)
profile_full["quote_requested"] = True
# Merge all inferred inputs so _missing_required_inputs is satisfied
for k, v in inp.items():
    if not k.startswith("_"):
        profile_full[k] = v
# Also provide data_records_lakhs explicitly
profile_full["data_records_lakhs"] = 50
profile_full["annual_revenue_cr"] = 320
profile_full["claims_last_3_years"] = False

scores = {
    "Cyber Technical Risk": 55,
    "Legal & Liability Exposure": 60,
    "Operational Continuity Risk": 50,
    "Physical Asset Risk": 40,
    "Regulatory & Compliance Risk": 45,
    "People & HR Risk": 35,
    "Financial Crime & Fraud Risk": 40,
}
bundle = {
    "name": "D2C Seller Shield",
    "mandatory_covers": ["cyber_liability", "product_liability", "marine_transit", "directors_officers"],
    "optional_covers": ["commercial_general_liability"],
}
recs = [
    {"key": "cyber_liability"},
    {"key": "product_liability"},
    {"key": "marine_transit"},
    {"key": "directors_officers"},
    {"key": "commercial_general_liability"},
]

from pricing_engine import _missing_required_inputs, _select_covers
covers = _select_covers(recs, bundle)
print("Covers selected:", covers)
missing = _missing_required_inputs(profile_full, covers, profile_full)
print("Still missing:", [m["key"] for m in missing])

print("=== price_output_stage ===")
q = price_output_stage(profile_full, scores, recs, bundle)
print(f"  Status: {q.get('quote_type')}")
covers_priced = q.get("covers_priced", [])
for c in covers_priced:
    print(f"  {c.get('cover_key')}: SI={c.get('sum_insured_cr')}Cr  Prem={c.get('premium_lakh')}L  Rate={c.get('final_rate_pct')}%")
print(f"  Net total: {q.get('net_premium_lakh')} L")
print(f"  Gross total: {q.get('gross_premium_lakh')} L")
