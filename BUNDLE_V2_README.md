# Bundle Recommender V2 — Architecture Guide

## Overview

`bundle_recommender_v2` is a purpose-built multi-bundle recommendation engine that evaluates the full ICICI Lombard commercial, group, and specialty product catalogue relevant to startups, SMEs, and operating businesses.

It runs **alongside** (not instead of) the existing `bundle_catalog.match_bundle()` and `risk_engine.recommend_products()` logic. Both engines can be called from `server.py`; their outputs are additive.

---

## File Layout

| File | Purpose |
|---|---|
| `bundle_scoring_utils.py` | `BundleInputV2` dataclass, sigmoid, `extract_exposure_features`, `check_hard_gates`, `compute_z_score` |
| `product_catalogue_v2.py` | Master catalogue (80+ products), `FAMILY_SCORING_PARAMS`, `PAIR_RULES`, `TREND_PRIORS` |
| `bundle_recommender_v2.py` | Main engine — `recommend_bundles_v2(inp)` and bridge `get_bundle_recommendations_v2()` |
| `bundle_explanation.py` | Narrative generator, gap alerts, gate summaries |
| `tests/test_bundle_v2.py` | 18 test classes, 40+ assertions |
| `BUNDLE_V2_README.md` | This file |
| `MIGRATION_NOTE.md` | How to wire v2 into the existing `server.py` |

---

## Canonical Families

| Family Key | Coverage Plane |
|---|---|
| `core_business_package` | SME/commercial package policies |
| `property_fire` | Fire, all-risk, IAR, Bharat Udyam products |
| `employee_health` | Group health, hospital cash, critical illness |
| `employers_liability` | WC/EC, Group Personal Accident |
| `general_or_modular_liability` | CGL, public liability, I-Select |
| `cyber` | Cyber Secure, Commercial Cyber, I-Elite Cyber |
| `professional_or_sector_liability` | Healthcare PI, FS PI, product recall, RPA, R&W, title, surety |
| `engineering_project` | CAR, EAR, CECR, ALOP |
| `marine_logistics_credit` | Marine cargo, hull, trade credit, political risk |
| `commercial_motor_fleet` | GCV, miscellaneous vehicle, trailer, two-wheeler |
| `payment_card_network_specialty` | Card/payment protection, cellular network |

---

## Scoring Formula

For each bundle family **b**:

```
z_b = intercept_b
    + Σ (risk_score_i / 100 × risk_weight_b_i)        [risk engine contribution]
    + Σ (exposure_feature_j × exposure_weight_b_j)     [intake exposure contribution]
    + trend_prior_b                                     [macro trend baseline]
    + Σ (wording_feature_k × wording_weight_b_k)       [wording fit bonus]
    - Σ (penalty_feature_l × penalty_weight_b_l)       [contraindication deduction]

score_b = 100 × sigmoid(z_b)
```

### Intercept calibration

Intercepts are set so that a company with **zero** relevant exposure scores below 20 (very low) and a company with **full** exposure scores above 70 (high confidence).

| Family | Intercept |
|---|---|
| `core_business_package` | -2.5 |
| `property_fire` | -2.5 |
| `employee_health` | -2.5 |
| `employers_liability` | -2.5 |
| `general_or_modular_liability` | -2.0 |
| `cyber` | -2.5 |
| `professional_or_sector_liability` | -2.5 |
| `engineering_project` | -3.5 (requires explicit project trigger) |
| `marine_logistics_credit` | -3.0 |
| `commercial_motor_fleet` | -3.0 |
| `payment_card_network_specialty` | -4.0 (requires payment/card hard gate) |

### Trend priors

Small non-overriding additive constants reflecting multi-year risk trends in the Indian market:

| Family | Prior | Rationale |
|---|---|---|
| `cyber` | +0.30 | Rising CERT-In breach frequency; DPDPA 2023 penalties |
| `employee_health` | +0.20 | Talent retention benchmark for funded startups |
| `marine_logistics_credit` | +0.10 | Trade credit adoption growing in B2B India |
| `property_fire` | +0.10 | Climate zone losses driving take-up in Tier 2/3 |
| `payment_card_network_specialty` | +0.10 | UPI/card fraud trends |

Trend priors are **additive constants** — they can never override a zero-evidence score to produce a high recommendation.

---

## Hard Gates

Hard gates are binary eligibility checks applied **before** scoring. A product failing a hard gate is excluded from the family's eligible pool; this is not reflected in the score — the product simply does not appear.

| Gate | Products Affected |
|---|---|
| `max_total_insurable_value: 5` | Bharat Sookshma (all asset values ≤ ₹5Cr) |
| `min_total_insurable_value: 5` | Bharat Laghu (asset values > ₹5Cr) |
| `max_total_insurable_value: 50` | Bharat Laghu (asset values ≤ ₹50Cr) |
| `min_total_insurable_value: 50` | IAR / Industrial All Risk (≥ ₹50Cr) |
| `min_total_insurable_value: 100` | Fire Mega Risk (≥ ₹100Cr) |
| `min_headcount: 5` | All group health / GPA products |
| `min_headcount: 25` | I-Elite CGL variants |
| `requires_drone_ops` | RPA Insurance, Aviation Insurance |
| `requires_payment_or_card_program` | Card/payment protection products |
| `requires_real_estate_development` | Title Insurance |
| `requires_ma_transaction` | R&W Insurance |
| `requires_port_maritime` | Port Package, Marine Hull, P&I |
| `requires_telecom_network` | Cellular Network Insurance |
| `requires_jewellery_inventory` | All Jeweller's Package variants |
| `requires_fuel_forecourt` | Petrol Station Package |
| `requires_project_or_installation` | All engineering/project products |
| `requires_vehicles` | All motor fleet products |
| `requires_healthcare_ops` | Healthcare Professional Indemnity |
| `requires_event_production` | Entertainment Production Package |
| `requires_workforce` | All employee/employer covers |
| `requires_food_pharma` | Total Recall, Product Recall |
| `requires_surety_or_construction` | Surety Insurance |

---

## Variant Selection Logic

Within each family, multiple product variants compete. The engine selects the **best eligible** variant by:

1. Filtering hard gates (ineligible variants removed).
2. Computing a variant-adjusted z-score (family params + product-level `exposure_weights`).
3. Adding a **sector match bonus** (+0.2 z) if the startup's sector is in the product's `sector_tags`.
4. Among near-ties: prefer the **most specific** product (fewer sector_tags = more niche).

### Asset tier routing (property_fire family)

```
total_assets = owned_assets_value + stock_value + machinery_value + electronics_value

if total_assets <= 5Cr    → Bharat Sookshma
if 5Cr < total_assets <= 50Cr → Bharat Laghu
if total_assets >= 50Cr   → IAR / Property All Risk / Commercial IAR
if total_assets >= 100Cr  → Fire Mega Risk eligible
```

---

## Pairing Rules

Post-scoring pair boosts are applied when a **trigger family** scores above 50 and a specified exposure condition is met. The boost adds `delta_z` to the paired family's z-score, which is then re-ranked.

| Trigger Family | Boosted Family | Condition | delta_z | Reason |
|---|---|---|---|---|
| `general_or_modular_liability` | `employers_liability` | `has_workforce` | +0.6 | CGL does not replace EC Act obligation |
| `general_or_modular_liability` | `property_fire` | `asset_tier > 0` | +0.4 | Premises liability implies insurable assets |
| `engineering_project` | `marine_logistics_credit` | `has_project` | +0.5 | Construction projects have marine transit + ALOP exposure |
| `employee_health` | `employers_liability` | `blue_collar_tier > 0` | +0.5 | Group health does not satisfy WC obligation |
| `marine_logistics_credit` | `commercial_motor_fleet` | `goods_vehicle_tier > 0` | +0.4 | Transit exposure pairs with fleet motor cover |
| `cyber` | `professional_or_sector_liability` | `regulatory_intensity_tier > 0` | +0.5 | Regulated sector cyber + PI exposure are correlated |
| `employers_liability` | `employee_health` | `headcount_tier > 0` | +0.4 | EC pairs with group health for complete workforce protection |
| `commercial_motor_fleet` | `employers_liability` | `has_workforce` | +0.3 | Fleet drivers have EC obligations |
| `engineering_project` | `professional_or_sector_liability` | `surety_bond_need > 0` | +0.6 | EPC projects need CAR + Surety |

---

## Output Format

```python
BundleOutput(
    primary_bundles=[   # top 3 ranked by score
        BundleRecommendation(
            product_name="Cyber Secure",
            canonical_family="cyber",
            product_key="cyber_secure",
            score=89.6,          # 0–100
            confidence="high",   # high | medium | low | very_low
            reasons=[
                "Risk engine flags high cyber technical risk (score 80/100).",
                "Intake signals financial data handling.",
            ],
            missing_inputs=[
                "handles_personal_data: providing this would refine cyber score."
            ],
            paired_with=[
                "Financial Services / Institutions Professional Indemnity",
            ],
        ),
        ...
    ],
    secondary_bundles=[...]   # next 2
)
```

---

## BundleInputV2 Fields

All fields are optional (default zero/False). Providing more context improves recommendation accuracy.

| Field | Type | Description |
|---|---|---|
| `industry` | str | Primary sector (matches SECTOR_PROFILES keys) |
| `funding_stage` | str | Pre-seed \| Seed \| Series A \| Series B+ |
| `headcount_total` | int | Total employees |
| `headcount_blue_collar` | int | Factory/warehouse/manual workers |
| `headcount_field` | int | Field/delivery/sales workers |
| `contractors_count` | int | External contractors |
| `gig_workers_count` | int | Gig workers |
| `office_presence` | bool | Has office/coworking space |
| `warehouse_presence` | bool | Has warehouse/fulfilment centre |
| `factory_presence` | bool | Has manufacturing plant |
| `owned_assets_value` | float | ₹ crores — fixed assets |
| `stock_value` | float | ₹ crores — inventory/stock |
| `machinery_value` | float | ₹ crores — plant and machinery |
| `electronics_value` | float | ₹ crores — electronics/servers |
| `handles_personal_data` | bool | Processes personal data (DPDPA) |
| `handles_financial_data` | bool | Processes financial data |
| `handles_medical_data` | bool | Processes health/medical records |
| `payment_or_card_program` | bool | Issues cards or payment instruments |
| `drone_operations` | bool | Operates commercial drones |
| `healthcare_operations` | bool | Runs clinic/hospital/diagnostics |
| `event_or_production_operations` | bool | Runs events or media productions |
| `jewellery_inventory` | bool | Holds jewellery inventory |
| `project_under_construction` | bool | Active construction project |
| `capex_project_value` | float | ₹ crores — project sum insured |
| `M_and_A_or_secondary_transaction` | bool | M&A or secondary transaction in progress |
| `contract_bid_or_performance_bond_need` | bool | Needs bid/performance bond |
| `risk_scores` | dict | Output of `risk_engine.compute_risk_scores()` (0–100 per category) |

---

## Running Tests

```bash
# From project root
python -m pytest tests/test_bundle_v2.py -v
```

All 18 test classes and 40+ assertions should pass.

---

## Integration with Existing `server.py`

See `MIGRATION_NOTE.md` for the minimal code change to add `bundles_v2` to the existing `analyze()` response.
