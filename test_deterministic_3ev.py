"""Test: run 3ev Industries through the deterministic analyze() engine."""
import sys, json
sys.path.insert(0, "startup_shield_web")

from server import analyze

profile = {
    "startup_name": "3ev Industries Private Limited",
    "sector": "Manufacturing",
    "funding_stage": "Series A",
    "team_size": 98,
    "operations": "Physical-only",
    "data_sensitivity": "Low",
    "ai_in_product": False,
    "ai_tier": "None",
    "annual_revenue_cr": 28.52,
    "total_insurable_asset_value_cr": 18.15,   # asset register replacement value
    "gross_profit_cr": 6.73,
    "has_investors": "Yes",
    "regulatory": ["Labour Codes / gig worker regulations"],
    "physical_assets": ["Manufacturing / factory", "Warehouse / fulfilment centre", "Office / coworking space"],
    "data_handled": [],
    "customer_type": ["B2B"],
    "has_manufacturing": True,
    "has_inventory": True,
    "inventory_cr": 6.4,
}

result = analyze(profile)

bundle = result.get("bundle_match") or {}
recs   = result.get("recommendations") or []
alts   = result.get("bundle_alternatives") or []

print(f"\n=== BUNDLE ===")
print(f"  {bundle.get('name')} — fit {bundle.get('fit_pct')}%")
print(f"  mandatory: {bundle.get('mandatory_covers')}")
print(f"  optional:  {bundle.get('optional_covers', [])[:5]}")

print(f"\n=== ALTERNATIVES (top 3) ===")
for a in alts[:3]:
    print(f"  {a.get('name')} — fit {a.get('fit_pct')}%  mandatory: {a.get('mandatory_covers')}")

print(f"\n=== ALL RECOMMENDATIONS (by score) ===")
for r in sorted(recs, key=lambda x: -float(x.get('score') or 0))[:12]:
    print(f"  {r.get('key'):35s}  score={r.get('score')}  priority={r.get('priority')}")
