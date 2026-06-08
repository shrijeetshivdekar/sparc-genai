# SPARC Pricing Engine Audit and Redesign for Indicative Startup Insurance Pricing

## Evidence base and scope

This review is grounded in two evidence streams. First, the uploaded repository shows that SPARC is already a deterministic, auditable pre-underwriting engine with separate quote-input suggestion logic, benchmark premium tables, and cover-level pricing logic. The strongest repo signals are: a hard-coded three-bucket benchmark table in `premium_estimator.py` (`micro`, `small`, `growth`) with static min/max premiums by product; quote-input suggestions in `quote_prefill.py` that infer revenue, limits, records, property SI, cargo turnover and other inputs from stage, team size, sector and selected assets/data types; and a pricing engine in `pricing_engine.py` that prices covers using either base-rate-times-exposure with multiplicative loadings or enterprise liability ROL bands, then applies bundle discount and GST (`premium_estimator.py`, lines 1–199; `quote_prefill.py`, lines 13–223 and 274–431; `pricing_engine.py`, especially the cover specs/constants, `_referral_flags`, `_pricing_scale`, and `price_output_stage`, lines 1092–1228). The frontend explicitly tells the user that the benchmark card is “not a quote”, excludes selected SI, GST, bundle discount, claims loadings and underwriter checks, and suppresses benchmark ranges only when the backend’s enterprise-scale flag trips (`startup_shield_web/app.js`, around lines 2220–2229 and 2865–2878). The tests also show that the repo has already moved enterprise cyber and enterprise liability lines toward regressive ROL behavior, and that group health is currently treated as a per-head burning-cost matrix (`tests/test_pricing_engine.py`, around lines 210–356).  

Second, public Indian insurance and regulatory sources show that many commercial lines in India are structurally underwritten on exposures that are more granular than SPARC currently uses. IRDAI de-notified all tariffs effective 1 April 2024, so property/fire/engineering pricing is no longer a tariff lookup and now depends materially on occupancy, location, protections and underwriting appetite. IRDAI’s standard Bharat Sookshma Udyam Suraksha wording applies where value at risk at one location does not exceed ₹5 crore, while Bharat Laghu Udyam Suraksha applies where value at risk at one location exceeds ₹5 crore but does not exceed ₹50 crore. Cyber proposal forms in India ask for revenue, record counts, data types, governance roles, audits, vulnerability management, physical access and network controls. D&O proposal forms ask whether the risk is claims-made, ownership structure, securities exposure, M&A/IPO/restatement activity, auditor issues, prior notices and known circumstances. Group health proposal forms require employee/dependent census, age, gender, sum insured, existing diseases, claims history and optional benefits such as maternity/PED coverage. Product liability, public liability, machinery breakdown, CAR/EAR, marine and trade credit forms likewise ask for turnover, products, premises, hazardous materials, prior claims, inspections, project details, annual transit turnover, buyer profile and payment terms rather than just startup stage or headcount. citeturn5search2turn5search10turn4search2turn4search5turn20view0turn21view2turn21view3turn21view4turn19view0turn23view0turn23view3turn19view5turn6search2turn6search3turn18view0turn22view0turn19view1turn19view2turn12search6turn12search11turn11search0

For clarity in the recommendations below, I use three labels:

- **[R] Repo-derived**: grounded directly in the uploaded files.
- **[E] Evidence-backed**: supported by public Indian regulatory/product/proposal-form sources.
- **[H] Heuristic**: commercially sensible for an indicative engine, but not directly provable from public Indian tariff data because exact insurer rate curves are not public.

## Executive diagnosis

This section is **Part A**.

The core architectural problem is not that SPARC is deterministic; it is that it mixes **suggested exposure selection**, **benchmark marketing ranges**, and **indicative quote calculation** too tightly, while using variable sets that are often too coarse for Indian commercial insurance. In the repo, `quote_prefill.py` derives not only helper suggestions but also commercially consequential inputs such as cyber limit, D&O limit, PI limit, product liability limit, public liability limit, cargo turnover and even claims defaults from stage, team, revenue proxy, sector and data/asset tags. Those inferred inputs then flow into pricing if the user “confirms” them, even though the file itself says these are deterministic suggestions to reduce blank-form friction rather than verified underwriting submissions. That is workable for prefill, but dangerous when the same inferred values drive a precise-looking premium. [R] (`quote_prefill.py`, lines 1–6, 13–223; `company_profiles.py`, lines 1–6, 313–330.)

The second problem is **overcompounding on startup-style proxy variables**. On SME covers, the pricing engine multiplies exposure by multiple loadings—risk, stage, sector, controls, claims, revenue, record count and so on—while only partially capping loadings. The repo’s own quote methodology string describes this: “base rate x exposure x capped loadings” for SME covers, with enterprise liability lines separately using regressive ROL bands. The result is that large suggested limits, high record counts, bigger team size, revenue proxies and sector multipliers can stack in ways that feel actuarially neat but commercially wrong, especially for cyber, PI, D&O and public/product liability. The fact that `MAX_RISK_LOADING` is capped in code helps, but it does not solve the broader issue that too many multiplicative levers remain live at once. [R] (`pricing_engine.py`, constants and cover specs near the top; `price_output_stage`, lines 1206–1210; tests around enterprise-liability behavior in `tests/test_pricing_engine.py`, lines 210–334.)

The third problem is **benchmark-vs-quote inconsistency**. The current benchmark layer in `premium_estimator.py` is a static matrix keyed only to stage/team bucket and product. It is not built from the quote calculator and does not share the same exposure assumptions. The frontend correctly warns that benchmark pricing does not include selected SI, GST, bundle discount, claims loadings or underwriter checks, but the user still sees both cards next to each other. Because benchmark suppression only happens when the backend’s enterprise threshold is reached—currently revenue at least ₹500 crore, team size at least 1,000, or aggregate liability limit above ₹150 crore—users can still receive startup benchmark ranges for risks that have already become specialty or enterprise-style from an underwriting perspective. That threshold is far too late for cyber, D&O, PI, product liability, engineering and marine. [R] (`premium_estimator.py`, lines 1–199; `pricing_engine.py`, lines 1140–1160; `startup_shield_web/app.js`, lines 2220–2229 and 2865–2878.)

The fourth problem is **line-of-business mis-specification**. Some lines are currently priced on variables that matter only weakly relative to the true Indian underwriting basis. Public liability and CGL are primarily about premises, footfall, operations, hazard, site conditions and neighbouring exposures; product liability is about the product, jurisdictions, distribution footprint, QA/traceability and recall history; trade credit is about B2B turnover, buyer spread, payment terms and country risk; marine open/annual-turnover policies are based on transit turnover and limit-per-sending, not startup stage. Public proposal forms in India make this plain. SPARC’s current variable set partially captures some of this, but not enough to support precise quotes across all lines. citeturn22view0turn18view0turn11search0turn12search6turn12search11turn19view2turn19view1

The fifth problem is **confidence overstatement**. The repo currently returns one quote type, one precise gross premium in INR, and one set of underwriter referral flags. It does not yet tell the user whether the displayed number is merely directional, technically priced within a calibrated operating box, or so assumption-heavy that the engine should refuse precision altogether. That is a product risk as much as a pricing risk. Public sources show that Indian commercial products are proposal-form-led, claims-made on several liability lines, and underwriter-discretionary on acceptance; the engine should mirror that reality by expressing confidence and escalation explicitly. citeturn19view0turn20view0turn19view5turn22view0turn19view2

The sixth problem is **UI language risk**. Because the frontend shows a benchmark card, a quote card and product labels together, unsupported language can easily drift into “market benchmark”, “expected premium” or even “mandatory cover” positioning when the actual public/legal basis is weaker. In India, employers may have statutory obligations under the Employees’ Compensation Act and ESIC/ESI rules for eligible establishments and wage bands, but that does not translate into a universal statutory mandate for generic group mediclaim for all startups. Likewise, the insurer and broker pages reviewed position EPLI as protection against employee claims, not as a generally mandatory statutory policy. So SPARC should be disciplined about what it calls compulsory, standard, optional or “underwriter required”. citeturn16search1turn3search0turn3search3turn3search4turn3search16

## Redesigned pricing framework

This section is **Part B**.

The right redesign is a **four-layer deterministic architecture**:

### Benchmark layer

The benchmark layer should be a **separate catalog**, not a by-product of the quote formula. Its purpose is commercial orientation, not technical pricing. Each benchmark cell should be keyed to:

`product_line × startup_segment × sector_cluster × standard_assumption_pack`

A standard assumption pack must be explicit. For example:

- Cyber: “₹5 crore limit, digital-first startup, basic controls, no prior claims, India-only.”
- D&O: “₹5 crore limit, institutional investors, unlisted Indian company, no merger/IPO, no known circumstances.”
- PI/Tech E&O: “₹5 crore limit, B2B software/services, standard contract wording, no prior claims.”
- Group Health: “₹5 lakh employee-only, metro/non-metro, average age band, no maternity, no dependents.”
- Property: “one location, reinstatement basis, standard office/light stock occupancy, ordinary protections.”
- Marine: “annual domestic transit turnover band, standard packed non-hazardous goods, ordinary routes.”

Benchmark outputs should always be ranges, never point estimates, and should be shown only where the risk remains inside the startup-scale benchmark box. Anything outside that box should display: **“Startup benchmark not comparable; enterprise/specialty validation required.”** [R][H]

### Quote layer

The quote layer should use an explicit **pricing basis per line**, chosen before any rating happens:

- `limit_based_liability`
- `turnover_based_liability`
- `employee_benefit_census`
- `asset_value_property`
- `project_value_engineering`
- `annual_transit_turnover`
- `credit_turnover_or_receivables`
- `fidelity_limit_with_controls`

This avoids misusing the same `base_rate × exposure × multipliers` template everywhere. It also lets the engine explain itself more honestly to the user. [H]

### Referral layer

The referral layer should replace large parts of today’s “inflate until uncomfortable” behavior. When a risk steps outside the engine’s calibrated box, the engine should not continue compounding penalities until the quote becomes absurd. It should instead do one of three things:

- **Directional only**: show a broad premium range, not a point estimate.
- **Technically priced**: show a point estimate or narrow range with clear assumptions.
- **Underwriter required**: suppress precision and show only a benchmark or referral message.

This is how real commercial underwriting behaves. Proposal forms define the risk; acceptance and final rating remain subject to underwriting approval. citeturn19view0turn20view0turn22view0turn19view2

### Explanation layer

Every quote response should carry:

```json
{
  "quote_confidence": {
    "band": "directional_only | technically_priced | underwriter_required",
    "score": 0,
    "reason_codes": []
  },
  "calibration_basis": [
    "public_benchmark",
    "confirmed_customer_inputs",
    "heuristic_rate_curve",
    "proposal_form_proxy"
  ],
  "precision_mode": "suppressed | range | point_estimate",
  "benchmark_comparison": {
    "status": "comparable | not_comparable | suppressed",
    "explanation": ""
  }
}
```

That is deterministic, explainable and auditable. [H]

### Target pricing mechanics

For liability lines, the target structure should be:

\[
\text{Premium} = \max(\text{floor}, \sum \text{limit tranche} \times \text{ROL tranche} \times \text{modifier band})
\]

with **regressive ROL by tranche**, not a single all-in multiplier on the entire selected limit. Modifier bands should be few, clipped and explainable. The safest pattern is:

- one **hazard band**
- one **controls/governance band**
- one **claims/prior-incidents band**

Do **not** separately multiply by stage, revenue, headcount, records and sector once the base limit or turnover already reflects scale. Instead, use those variables either to choose the starting limit/turnover band or to trigger referral. [H]

A practical deterministic modifier ladder is:

| Composite modifier band | Trigger logic | Multiplier |
|---|---|---:|
| Preferred | strong controls / clean claims / simple exposure | 0.85–0.95 |
| Standard | ordinary risk | 1.00 |
| Elevated | one meaningful concern | 1.15–1.25 |
| High | two meaningful concerns | 1.35–1.50 |
| Referral | more than two major concerns or outside appetite | stop precision |

This is materially safer than multiplying six or seven loadings together. [H]

## Product-line rules table

This section is **Part C**.

Before the table, the main evidence-backed underwriting inputs are worth stating plainly. Indian proposal forms and insurer documents ask for much richer inputs than SPARC currently prices off. Cyber asks for revenue, data records, privacy/compliance governance, audits, vulnerability management and network/physical controls. D&O asks for claims-made exposure, ownership, listing/securities activity, financial restatements, prior notices and known circumstances. Group health asks for census, age, gender, sum insured, disease disclosures, claims experience and optional benefits. Product liability and public liability ask for products/activities, turnover, geographies, hazardous content, complaints/recalls, claims history and requested limits. Machinery breakdown and CAR/EAR ask about maintenance, prior defects, project details and catastrophe/site perils. Marine and trade credit depend on annual turnover, credit terms, buyer spread, routes and commodity characteristics. citeturn20view0turn21view2turn21view3turn21view4turn19view0turn23view0turn23view3turn19view5turn18view0turn22view0turn19view1turn19view2turn12search6turn12search11turn11search0

### Product-line rules

| Product line | Pricing basis | Target indicative structure | Sensible floors / ceilings | Variables that should mainly affect price | Variables that should mostly trigger referral, not huge inflation | Target behaviour by stage / sector / geography / claims / controls | Support |
|---|---|---|---|---|---|---|---|
| Cyber | Selected limit, priced with regressive ROL tranches | For startup-scale risks, tranche ROL on ₹1–5Cr, ₹5–10Cr, ₹10–25Cr. Above ₹25Cr: broad range only; above ₹50Cr: underwriter required. | Floor around ₹0.60L–₹1.50L depending minimum limit; effective ROL should fall as limit rises. | Confirmed limit, records/data count, type of data, outsourced processing, controls maturity, prior incidents, sector hazard. | Very large record counts, cross-border sensitive data, regulator actions, weak incident response, critical infrastructure / space systems. | Stage should mainly influence suggested limit, not direct price. Fintech/healthtech/payments may start one hazard band higher. Controls can reduce meaningfully. Prior claims/incidents can move one or two bands up. CERT-In and privacy obligations justify more focus on controls and governance than on raw headcount. citeturn2search0turn20view0turn21view2turn21view3turn21view4turn1search1turn1search5 | E/H |
| D&O | Selected limit, claims-made management liability logic | Regressive ROL by tranche. Startup precision only up to ~₹10Cr–₹15Cr. ₹15–₹25Cr directional. Above ₹25Cr or securities events: underwriter required. | Floor around ₹0.75L–₹1.50L. Keep effective ROL lower than cyber and PI at larger limits. | Confirmed limit, investor profile, governance maturity, financial stress signals, prior notices/claims, cap-table complexity. | IPO/listing plans, M&A, restated financials, auditor disputes, known circumstances, foreign securities exposure. | Stage/fundraise matter because they change governance and litigation profile, but not as crude multipliers. Seed/Series A can stay in low single-digit limits unless specific investor/board requirements exist. Public/IPO/M&A scenarios should immediately degrade confidence. D&O is explicitly claims-made in proposal forms. citeturn19view0turn23view0turn23view3turn7search11 | E/H |
| PI / Tech E&O | Selected limit with service/contract hazard bands | ROL tranches similar to D&O but slightly above D&O when service dependence and indemnity language are aggressive. | Floor around ₹0.50L–₹1.25L. Suppress precision above ~₹25Cr. | Service type, share of B2B/enterprise work, contract indemnities, SLA credits, retro/past acts, claims history, jurisdiction, client concentration. | Medtech/clinical advice, regulated financial advising, mission-critical systems, US/Canada contracts, uncapped indemnities. | Stage should not directly increase premium once client/service profile is known. SaaS with standard low-liability contracts should not price like regulated advisory firms. Deeptech software to industrial customers may need higher hazard band but not unlimited inflation. | H |
| CGL / Public Liability | Premises/operations-led, optionally turnover-assisted | Use requested limit with hazard class and site/perimeter variables; do not let startup stage drive price. | Floor around ₹0.35L–₹0.75L for low-hazard premises; suppress benchmark above ~₹10Cr for non-industrial startup accounts. | Site count, footfall, warehousing, public interface, hazard sources, neighbouring property, transport extension, requested limit. | Hazardous substances, explosive/toxic storage, transport of dangerous goods, pollution extension, multi-site industrial operations. | For digital SaaS, PL/CGL should stay low and often referral should depend more on client contract requirements than revenue. For logistics, kitchens, warehousing, light manufacturing or battery/chemical operations, hazard rises fast. Indian public-liability proposal forms ask for surrounding areas, hazardous materials, wages, staff and turnover. citeturn22view0 | E/H |
| Product Liability | Turnover-plus-limit hybrid | Use product turnover and selected limit jointly. For many startup manufacturers, turnover is a better severity proxy than stage. | Floor around ₹0.75L–₹1.50L. Underwriter referral for exports to US/Canada, med devices, ingestibles, safety-critical hardware. | Product category, annual turnover, export territories, units, QA/testing, warranties, batch traceability, prior recalls/claims, limit. | Medical devices, food/pharma contamination, US/Canada distribution, recalls, high hazard or failure-critical products. | D2C apparel/cosmetics/home goods and hardware cannot be rated on revenue alone. Deeptech and healthtech hardware should often be directional only unless product class, QA and jurisdictions are confirmed. Public proposal forms explicitly ask for product lines, projected turnover, expected life, complaints systems, controls, recall history and territorial sales. citeturn18view0 | E/H |
| Crime / Fidelity | Limit-based with controls matrix | Price on requested limit, but primarily via control maturity and employee-role exposure. | Floor around ₹0.35L–₹0.75L. Suppress precision above ~₹10Cr–₹15Cr unless payment/fund-handling exposure is well understood. | Cash handling, payment access, maker-checker, reconciliations, privileged finance access, outsourcing, limit, prior fraud events. | Payment-wallet float, treasury access, poor segregation, weak audits, prior employee dishonesty, unusual cash movement. | Fintech and payments can rate above SaaS, but standard B2B software businesses should not inherit fintech crime pricing simply because they are venture-funded. Public fidelity guidance emphasises background checks, audits, dual control and job rotation. citeturn19view4turn15search4 | E/H |
| EPL | Headcount-limit hybrid | Headcount should dominate; requested limit adjusts severity. Revenue should have only weak effect. | Floor around ₹0.40L–₹0.90L. Above ~500 employees or complex contractor/gig mix: broader range or referral. | Headcount, attrition, dependent geographies, contractor/gig share, HR process maturity, POSH governance, prior disputes, limit. | Known disputes, union/industrial issues, regulatory notices, mass layoffs, founder transition, pending litigation. | Seed-stage teams rarely need high EPL limits unless investor/board pressures say otherwise. Large delivery/gig/logistics workforces should move to directional only unless HR controls and loss runs are known. Reviewed public sources describe EPLI as protection product, not a universal statutory compulsory cover. citeturn3search4turn3search16 | E/H |
| Group Health | Census-based, per-member rating | No precise quote without at least employee count, average age band, location mix, sum insured, and family structure. | Show only per-head ranges if no census. Typical employee-only startup bands can be shown directionally; dependent/maternity/PED materially widen them. | Lives, age, city/location, family structure, sum insured, claims history, maternity/PED cover, insurer continuity. | Large dependents, late-age cohorts, adverse claims experience, small pools with rich maternity/PED, broad geographies without census. | Public proposal forms require age, gender, sum insured, diseases, claims history and optional benefits. So SPARC should never return a precise annual GMP/GMC premium from headcount alone. For a startup benchmark, per-head-year ranges are acceptable only as directional heuristics. citeturn19view5turn6search2turn6search3turn6search15 | E/H |
| Property / IAR / Fire | Declared reinstatement value by location and occupancy | Rate on declared asset values, construction/occupancy/protection/cat zone. Stage should not price directly. | Use Bharat Sookshma for ≤₹5Cr one location, Bharat Laghu for >₹5Cr to ≤₹50Cr one location. Above ₹50Cr or complex multi-location: suppress startup benchmark. | Reinstatement value, location, occupancy, construction, fire protection, flood/cyclone/quake zone, stock type, BI dependency. | Cat zones, high-hazard occupancy, chemical/battery/plant risks, poor hydrants/fire systems, one-location TIV >₹50Cr, multi-location complexity. | Since IRDAI de-notified tariffs effective 1 April 2024, pricing is market-driven. SPARC should therefore rate by hazard class and location, not by stage/team. The standardized Bharat products create natural segmentation thresholds. citeturn5search2turn4search2turn4search5 | E |
| Engineering / MB / EEI | Split products, not one combined engineering rate | EEI on equipment SI; MB on machinery SI and maintenance; CAR/EAR on project value and duration; CPM on individual machine schedules. | Do not return one generic “engineering” number when the user has not specified the sub-line. Suppress precision if project schedule/details are absent. | For EEI: equipment class, portability, maintenance, environment. For MB: age, maintenance, prior breakdowns. For CAR/EAR: project value, period, site hazards, contractor experience. | Testing/commissioning, tunnelling, flood/quake/wet risk, old machinery, chronic breakdowns, imported critical spares, incomplete site data. | Public forms show these are distinct underwriting classes. SPARC should stop collapsing them into one cover unless it is clearly flagged as a placeholder. citeturn19view1turn19view2turn13search3 | E/H |
| Marine / Transit | Annual transit turnover and limit-per-sending | Rate in basis points on annual transit turnover; separate max-send / limit-per-sending sanity checks. | Small domestic non-hazardous programs can be narrow. High-value fragile/perishable/theft-prone routes need wider ranges or referral. | Annual transit turnover, commodity, packing, route, mode, claims history, max send, storage extensions. | Perishable/temperature-sensitive goods, theft-prone goods, export/import complexities, special clauses, poor packing, high single send. | Indian annual/open policies are turnover-led. Do not convert revenue proxies mechanically into a huge “cargo turnover” and then price as if it were a liability SI. Public marine sources say annual/open covers are tied to estimated annual turnover and limit-per-sending. citeturn12search6turn12search11turn12search1turn12search14 | E/H |
| Trade Credit | Insurable B2B turnover or receivables-led | Price in basis points of insured turnover/receivables, with strong buyer-spread and payment-term effects. | Show only broad ranges without debtor book data. | B2B turnover, receivables, top-buyer concentration, terms, countries, sector, historical bad debts. | Long terms, concentrated debtors, export debtors, policy exclusions, weak collections, stressed sectors. | Public trade-credit sources say premiums depend on B2B turnover, countries, customer type, payment terms and coverage percentage, often below 0.5% of turnover. Without buyer/tenor data, SPARC should stay directional only. citeturn11search0turn11search15 | E/H |
| Surety | Contract-value / performance-led | Do not quote precisely from startup profile only. Show referral or very broad directional guidance. | Underwriter required for most startup cases. | Contract value, employer, nature of bond, balance sheet strength, working capital, track record, indemnity structure. | EPC/infrastructure/public works, thin net worth, long-duration obligations. | IRDAI regulates surety contracts, but public startup quote calibration is weak. Treat as referral-first. citeturn0search3turn0search11 | E/H |
| Employees’ Compensation | Payroll / employee category / hazard class | Payroll-led with occupational hazard classes; not revenue-led. | Floor by minimum premium and employee mix. | Payroll, employee classes, site hazard, contract labour mix, prior accidents. | Hazardous occupations, severe injury history, incomplete employee classification. | This is a better fit for statutory/employer-liability support than generic “group health mandatory” language. The statutory basis is the Employees’ Compensation Act, while ESI applies by establishment and wage criteria, not as a generic group mediclaim requirement. citeturn16search1turn16search11turn3search0turn3search3 | E |

### Startup-scale versus enterprise-scale display rules

A startup benchmark should be suppressed earlier than the current repo threshold. Recommended display rules are:

| Line | Keep startup benchmark | Broad directional only | Suppress benchmark and show underwriter validation |
|---|---|---|---|
| Cyber | up to ₹10Cr limit and non-specialty data profile | ₹10–₹25Cr or unusually sensitive data stack | above ₹25Cr; above ₹50Cr precise quote off |
| D&O | up to ₹10Cr for unlisted Indian startup | ₹10–₹25Cr | above ₹25Cr, or IPO/M&A/restatement/foreign securities |
| PI / Tech E&O | up to ₹10Cr for ordinary SaaS/services | ₹10–₹25Cr | above ₹25Cr or regulated/high-criticality services |
| PL / CGL | up to ₹5Cr–₹10Cr low-to-medium hazard | ₹10Cr with clear site data | hazardous processes, pollution, transport hazard, bigger towers |
| Product Liability | up to ₹5Cr–₹10Cr for low-hazard domestic products | ₹10Cr or modest export footprint | med devices, food/pharma, US/Canada exports, recall history |
| Group Health | lives and census confirmed, standard plan | lives known but incomplete census | no census, complex family mix, >300 lives with rich benefits |
| Property | one-location TIV within Bharat Sookshma/Laghu box | simple multi-location within moderate TIV | >₹50Cr per location or industrial/IAR complexity |
| Engineering | simple EEI/MB with asset schedule | moderate plant / defined project | incomplete project data, wet/cat/tunnelling, large project values |
| Marine | modest domestic turnover and max-send known | moderate turnover, some route complexity | high-value / special handling / export-heavy or no max-send |
| Trade Credit | debtor spread and payment tenors known | partial debtor data | concentrated books or missing debtor analytics |
| Surety | not recommended for precise quoting | very broad directional only | default mode |

These thresholds are **heuristic operating-box rules** for a pre-underwriting product, not insurer mandates. [H]

## Code change plan

This section is **Part D**.

### `pricing_engine.py`

Refactor the pricing engine from a mostly uniform multiplier model into a **basis-by-basis calculator registry**. Concretely:

1. Add a `PricingRule` structure per line with fields such as:
   - `pricing_basis`
   - `benchmark_key`
   - `required_confirmed_inputs`
   - `line_min_premium_lakh`
   - `max_precise_limit_cr`
   - `max_benchmark_limit_cr`
   - `hazard_band_map`
   - `controls_band_map`
   - `claims_band_map`
   - `referral_triggers`
   - `suppression_triggers`

2. Split `_price_cover()` into explicit calculators:
   - `_price_limit_liability_tranche()`
   - `_price_group_health_census()`
   - `_price_property_asset_rate()`
   - `_price_engineering_subline()`
   - `_price_marine_turnover()`
   - `_price_trade_credit_turnover()`
   - `_price_fidelity_controls_matrix()`

3. Replace several multiplicative loadings with a **bounded composite modifier**. Stage, revenue and headcount should usually choose a segment or suggest a limit; they should rarely remain live premium multipliers once the exposure basis is already confirmed.

4. Introduce:
   - `quote_confidence`
   - `calibration_basis`
   - `precision_mode`
   - `benchmark_comparison`
   - `explanation_items`

5. Lower and line-specify the benchmark suppression thresholds. The current enterprise threshold in `_pricing_scale()` is too late for startup benchmarking. Use line-specific suppression instead of a single portfolio-wide threshold. [R]

6. Change the default behavior for referral:
   - if line is outside calibrated box, return a **range** or **suppressed precise quote**
   - do **not** continue to inflate a point estimate indefinitely

7. Add line-specific sanity rules:
   - `marine_turnover_cr` cannot be inferred above a defensible multiple of declared revenue without explicit confirmation
   - `product_liability_limit_cr` for low-hazard domestic products should not jump simply because of startup stage
   - `public_liability_limit_cr` should tie to site/public exposure, not just property SI
   - `claims_last_3_years` must never default to clean unless explicitly confirmed

### `premium_estimator.py`

Replace the current monolithic `PREMIUM_RANGES` table with a **benchmark assumptions catalog**. Each benchmark record should contain:

- product key
- startup segment
- sector cluster
- standard assumptions
- base exposure/limit/plan
- low/high directional range
- source type (`public_source`, `market_observation`, `heuristic`)
- last calibration date

The current table is useful as an MVP but too coarse: it buckets only by stage/team and keeps many unrelated lines in the same style. Its footnote also makes dated public-source claims without machine-readable provenance or per-line traceability (`premium_estimator.py`, lines 190–199). Keep the benchmark layer, but make it auditable and explicitly assumption-based. [R]

### `quote_prefill.py`

This file needs the biggest philosophical change: **suggestions must remain suggestions**. Make three concrete changes:

1. Separate:
   - `suggested_input`
   - `pricing_submitted_input`
   - `confidence_of_suggestion`

2. Replace aggressive formulaic recommended limits with **grid-based, stage-aware suggestion ladders**. For example:
   - cyber default suggestion ladder: 1 / 2 / 5 / 10 / 25
   - D&O: 1 / 2 / 5 / 10 / 20 / 25
   - PI: 1 / 2 / 5 / 10 / 15 / 25  
   Then use sector/contract cues only to move up one band, not to create unconstrained limit inflation. [H]

3. Remove any default that silently improves the risk to the customer’s benefit or detriment. Most importantly:
   - `claims_last_3_years` should default to `unknown`, not `False`
   - group health rating should not proceed precisely without age/census structure
   - cargo turnover should not be inferred as a large share of revenue unless the profile explicitly indicates trading/transit-heavy operations

4. Introduce specialty flags such as:
   - `specialty_deeptech_hardware`
   - `specialty_spacetech`
   - `specialty_healthcare_delivery`
   - `specialty_med_device`
   - `specialty_large_logistics_fleet`
   - `specialty_export_product`

These should degrade confidence and alter display/referral behavior much earlier.

### `startup_shield_web/app.js`

The UI should stop presenting all quotes with the same visual certainty.

1. Add a **confidence badge** at cover level and total level:
   - Directional only
   - Technically priced
   - Underwriter validation required

2. If `precision_mode == "range"`, show ranges only.
   - Example: `₹4.5L–₹6.0L + GST`
   - not `₹5,43,217`

3. If benchmark is not comparable, visually suppress it and show:
   - “Startup benchmark not comparable to selected structure”
   - “Why: selected limit / specialty operations / scale / missing census”

4. Ensure quote-vs-benchmark explanation is always shown if:
   - quote exceeds benchmark max by more than a configured ratio, or
   - benchmark is suppressed

5. Remove or soften any unsupported “mandatory” wording unless backed by a statute or explicit contractual market norm. The safer UI labels are:
   - “Commonly purchased”
   - “Frequently required by enterprise customers / investors”
   - “Statutory employer-liability support”
   - “Investor / contract driven”
   - “Often underwriter-led”

### `tests/test_pricing_engine.py`

Keep the existing enterprise-regressive-ROL tests, because they point in the right direction. Add new tests for the real redesign goals:

- **Benchmark suppression**
  - startup benchmark hidden for cyber >₹25Cr even if revenue is below enterprise threshold
  - property benchmark hidden when one-location TIV >₹50Cr
  - group health precise quote suppressed without census

- **No overcompounding**
  - increasing revenue or records within a band should not multiply SME cyber quote beyond a configured max jump unless referral is triggered
  - adding a second mild risk concern should move one modifier band, not cascade across all multipliers

- **Claims handling**
  - unknown claims history lowers confidence and precision, but does not auto-assume no claims

- **Marine sanity**
  - inferred cargo turnover cannot exceed configured defensibility cap without explicit user confirmation
  - max-send missing => directional only

- **Bundle consistency**
  - bundle discounts apply only to quote estimate subtotal
  - GST is computed on net premium after discount
  - total equals sum of cover premiums minus discount plus GST
  - internally consistent after any quote suppression/range output

- **Niche sector behavior**
  - deeptech/spacetech/healthtech hardware/logistics do not auto-produce false precision on liability and engineering lines without specialty confirmation

## Evidence, claims discipline, and open questions

SPARC should explicitly state what it **can** and **cannot** claim.

It **can** say:
- this is a deterministic, auditable, pre-underwriting estimate
- benchmark ranges are directional market comparisons under stated assumptions
- quote estimates are non-bindable and subject to insurer underwriting
- certain lines are technically priced only within a defined operating box
- outside the box, SPARC routes to underwriter validation rather than pretending to know the market [R][E]

It **should not** say:
- bindable quote
- insurer-approved premium
- market average premium unless a dated source and assumption set is attached
- compulsory cover unless there is a clear statutory or contractual basis
- exact premium for specialty/enterprise risks with missing core inputs [R][E]

Public support is strong for **underwriting inputs and structural segmentation**, but weak for **exact Indian liability-line rate curves**. Publicly available insurer documents and proposal forms reveal what underwriters ask for, and public market sources can support broad product structures and some premium-order-of-magnitude context; they do not supply enough transparent Indian tariff data to justify over-precise cyber/D&O/PI/CGL/Product Liability rate curves. That means the quote-engine redesign should be marketed as **evidence-informed plus heuristic-calibrated**, and internally backed by real quote/placement datasets as soon as possible. citeturn20view0turn19view0turn19view5turn18view0turn22view0turn11search0turn12search11

The data program required for proper calibration is straightforward:

- anonymised brokered quote logs by line, sector, stage and selected limit
- sold-policy premiums and key underwriting fields
- decline/referral reasons
- claims emergence or at least underwriter loss-ratio reviews at a coarse segment level
- insurer appetite matrices by sector/line
- group health renewal and claims-ratio cohorts
- property/location hazard datasets
- marine commodity / route / max-send cohorts
- debtor-book metrics for trade credit

Public sources can support proposal-form structure, product segmentation, regulatory thresholds and broad commercial framing. The actual **rate curves, elasticity, hazard relativities and enterprise referral thresholds** must be treated as proprietary calibration tasks, not as public-fact claims. [E][H]

### Open questions and limitations

The largest unresolved item is the exact rate-band calibration for Indian startup liability lines above ordinary SME scale. Public sources do not disclose insurer pricing tables with enough granularity to make those bands “evidence-backed” in the actuarial sense. The heuristic bands in this report are therefore appropriate for a defensible pre-underwriting engine, but they still need retrospective calibration against real quote data before you describe them as market-calibrated. citeturn11search0turn20view0turn19view0turn18view0turn22view0

The second limitation is that the repo files provided do not include the full server-side benchmark assembly path or a historical quote dataset, so this review focuses on architecture, formulas, thresholds, UI behavior and testability rather than on empirical fit diagnostics from real placements. [R]

The practical conclusion is clear: **keep SPARC deterministic, but make it humbler**. Use explicit basis-by-line pricing, tranche ROL for liability limits, clipped modifier bands, earlier benchmark suppression, and a first-class confidence model. That will make the product more commercially realistic, more internally consistent, and much easier to defend as a pre-underwriting decision-support engine.