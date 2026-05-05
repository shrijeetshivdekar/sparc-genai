# Migration Note — Bundle Recommender V2

## What changed

A new bundle engine (`bundle_recommender_v2`) has been added **alongside** the existing system.
No existing files were modified. Both engines can coexist.

## What was NOT changed

- `risk_engine.py` — standalone product recommender untouched
- `bundle_catalog.py` — existing `match_bundle()` untouched
- `startup_shield_web/server.py` — not modified (see optional integration below)
- `api/analyze.py` — not modified
- `premium_estimator.py`, `risk_appetite.py`, `b2b2b_map.py` — untouched

## New files

| File | Role |
|---|---|
| `bundle_scoring_utils.py` | Scoring primitives + `BundleInputV2` dataclass |
| `product_catalogue_v2.py` | 80+ products across 11 families with full metadata |
| `bundle_recommender_v2.py` | Main engine + bridge function |
| `bundle_explanation.py` | Narrative + gap alert layer |
| `tests/test_bundle_v2.py` | 18 test classes |
| `BUNDLE_V2_README.md` | Formula, hard gates, pair rules |
| `MIGRATION_NOTE.md` | This file |

## Optional: add `bundles_v2` to the existing `analyze()` response

In `startup_shield_web/server.py`, inside the `analyze()` function, after the existing
`match_bundle(...)` call, add:

```python
# --- Bundle Recommender V2 (additive) ---
from bundle_recommender_v2 import get_bundle_recommendations_v2

# Build extra fields from the frontend payload (all optional)
extra_fields = {
    "headcount_blue_collar":              int(profile.get("headcount_blue_collar", 0)),
    "headcount_field":                    int(profile.get("headcount_field", 0)),
    "contractors_count":                  int(profile.get("contractors_count", 0)),
    "gig_workers_count":                  int(profile.get("gig_workers_count", 0)),
    "office_presence":                    bool(profile.get("office_presence", False)),
    "warehouse_presence":                 bool(profile.get("warehouse_presence", False)),
    "factory_presence":                   bool(profile.get("factory_presence", False)),
    "store_presence":                     bool(profile.get("store_presence", False)),
    "lab_presence":                       bool(profile.get("lab_presence", False)),
    "owned_assets_value":                 float(profile.get("owned_assets_value", 0)),
    "stock_value":                        float(profile.get("stock_value", 0)),
    "machinery_value":                    float(profile.get("machinery_value", 0)),
    "electronics_value":                  float(profile.get("electronics_value", 0)),
    "domestic_shipments":                 bool(profile.get("domestic_shipments", False)),
    "export_shipments":                   bool(profile.get("export_shipments", False)),
    "import_dependency":                  bool(profile.get("import_dependency", False)),
    "receivables_on_credit":              float(profile.get("receivables_on_credit", 0)),
    "average_invoice_cycle_days":         int(profile.get("average_invoice_cycle_days", 0)),
    "owned_vehicle_count":                int(profile.get("owned_vehicle_count", 0)),
    "goods_vehicle_count":                int(profile.get("goods_vehicle_count", 0)),
    "miscellaneous_vehicle_count":        int(profile.get("miscellaneous_vehicle_count", 0)),
    "two_wheeler_count":                  int(profile.get("two_wheeler_count", 0)),
    "trailer_count":                      int(profile.get("trailer_count", 0)),
    "project_under_construction":         bool(profile.get("project_under_construction", False)),
    "installation_or_commissioning":      bool(profile.get("installation_or_commissioning", False)),
    "capex_project_value":                float(profile.get("capex_project_value", 0)),
    "handles_personal_data":              bool(profile.get("handles_personal_data", False)),
    "handles_financial_data":             bool(profile.get("handles_financial_data", False)),
    "handles_medical_data":               bool(profile.get("handles_medical_data", False)),
    "stores_customer_documents":          bool(profile.get("stores_customer_documents", False)),
    "uptime_dependency":                  bool(profile.get("uptime_dependency", False)),
    "online_transaction_volume":          int(profile.get("online_transaction_volume", 0)),
    "payment_or_card_program":            bool(profile.get("payment_or_card_program", False)),
    "healthcare_operations":              bool(profile.get("healthcare_operations", False)),
    "food_or_pharma_manufacturing":       bool(profile.get("food_or_pharma_manufacturing", False)),
    "warranty_or_service_contract_obligation": bool(profile.get("warranty_or_service_contract_obligation", False)),
    "event_or_production_operations":     bool(profile.get("event_or_production_operations", False)),
    "drone_operations":                   bool(profile.get("drone_operations", False)),
    "jewellery_inventory":                bool(profile.get("jewellery_inventory", False)),
    "fuel_or_forecourt_operations":       bool(profile.get("fuel_or_forecourt_operations", False)),
    "port_or_maritime_operations":        bool(profile.get("port_or_maritime_operations", False)),
    "telecom_network_assets":             bool(profile.get("telecom_network_assets", False)),
    "real_estate_development":            bool(profile.get("real_estate_development", False)),
    "M_and_A_or_secondary_transaction":   bool(profile.get("M_and_A_or_secondary_transaction", False)),
    "contract_bid_or_performance_bond_need": bool(profile.get("contract_bid_or_performance_bond_need", False)),
    "regulatory_intensity":               int(profile.get("regulatory_intensity", 0)),
    "annual_revenue":                     float(profile.get("annual_revenue", 0)),
    "locations_count":                    int(profile.get("locations_count", 0)),
}

result["bundles_v2"] = get_bundle_recommendations_v2(
    sector=sector,
    stage=funding_stage,
    risk_scores=scores,
    inp_legacy=inp,
    extra=extra_fields,
)
```

This adds a `bundles_v2` key to the existing response JSON without modifying any
existing keys or breaking backward compatibility.

## Frontend integration (optional)

Display `result.bundles_v2.primary_bundles` and `result.bundles_v2.secondary_bundles`
in a new "Full Bundle Catalogue" section of the UI alongside the existing bundle card.
Each entry carries `product_name`, `score`, `confidence`, `reasons`, and `paired_with`.

## Rollback

To remove v2 entirely, delete the 7 new files and remove the optional integration block
from `server.py`. All existing behaviour is preserved.
