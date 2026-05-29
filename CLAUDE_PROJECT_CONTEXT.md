# SPARC Project Context for Claude

This document is a full working-context handoff for this repository so another coding model can make changes without starting cold.

---

## 1. Project Identity

**Project name:** SPARC | Startup Shield  
**Primary user:** ICICI Lombard Relationship Managers (RMs) selling insurance to startups  
**Secondary user:** startup founders reviewing the risk report and quote support material  
**Core job:** turn a startup profile into a defensible insurance risk brief, recommended ICICI Lombard bundle, indicative premium view, outreach material, and next-action guidance

SPARC is not a generic dashboard. It is a meeting-room sales and underwriting support system. The RM should be able to open it in front of a founder and look informed within 1-2 minutes.

---

## 2. Product Goal

SPARC analyzes a startup across Indian regulatory, cyber, liability, governance, property, employee, and transit dimensions, then:

1. builds or autofills a startup profile,
2. computes risk scores,
3. recommends bundle(s) and individual products,
4. explains the recommendation in Indian insurance language,
5. produces outreach content,
6. provides indicative pricing support,
7. surfaces public trigger signals for pipeline generation.

The tool is intentionally India-specific:

- IRDAI / RBI / DPDP / ONDC / DGCA / gig-worker regulation context
- INR throughout
- NIC 2008 codes in pricing
- Indian product naming and bundle logic
- no US benchmarks unless explicitly labeled as external context

---

## 3. Architecture

### Frontend

- `startup_shield_web/index.html`
- `startup_shield_web/app.js`
- `startup_shield_web/styles.css`

This is a **vanilla JS** app, not React, not a framework SPA.  
`app.js` is the main UI and orchestration layer and is large.

### Local backend

- `startup_shield_web/server.py`

This is the local development server. It serves the frontend and implements API routes for local use.

Default local port:

- `5174` if no argument is supplied
- custom port supported, e.g. `py startup_shield_web/server.py 5181`

### Production backend

Serverless Python functions under:

- `api/analyze.py`
- `api/autofill.py`
- `api/company-profiles.py`
- `api/health.py`
- `api/meta.py`
- `api/outreach.py`
- `api/pipeline.py`
- `api/pricing.py`
- `api/signals.py`

Deployment config:

- `vercel.json`

### Core decisioning / domain logic

- `risk_engine.py`
- `premium_estimator.py`
- `pricing_engine.py`
- `bundle_catalog.py`
- `bundle_recommender_v2.py`
- `bundle_scoring_utils.py`
- `risk_appetite.py`
- `policy_wording.py`
- `company_profiles.py`
- `custom_product_triggers.py`
- `b2b2b_map.py`

### Pricing subsystem

- `pricing/model.py`
- `pricing/parameters.yaml`
- `pricing/parameters.json`
- `pricing/rules.py`
- `pricing/sources.md`
- `pricing/README.md`

This pricing module is a distinct subsystem and should be treated as the authoritative pricing core.

---

## 4. Main User Flows

### A. Manual RM flow

1. RM opens the tool
2. Enters or edits startup profile details
3. Runs analysis
4. Receives:
   - risk report
   - bundle recommendation
   - quote views
   - risk-score breakdown
   - actions / trigger outputs
   - outreach support

### B. Auto-profile flow

1. RM types a company name
2. Frontend calls `/api/autofill`
3. Gemini or profile lookup creates the profile draft
4. Frontend then calls `/api/analyze`
5. Results are rendered

Important nuance:

- In local dev, `/api/autofill` may return a more complete result
- On Vercel, `/api/autofill` can return profile-oriented data that is then passed to `/api/analyze`

### C. Signal Radar flow

1. User opens Signal Radar dashboard
2. Frontend calls `/api/signals`
3. Public triggers are shown as lead-generation tasks
4. RM can run SPARC from a signal card to generate a profile/report

### D. Premium Triage flow

1. On the results page, the RM opens the Premium Triage control
2. Selects line of business (`DO`, `Cyber`, `PI`, `CGL`, `Property`, `GH`)
3. Frontend calls `/api/pricing`
4. Quote is rendered as a formula-chain calculator
5. Rating factors and adjustments can be edited client-side for live recalculation

---

## 5. Current Major Features

### 5.1 Startup profile creation / enrichment

- manual profile entry
- company lookup / company profile search
- auto-profile via Gemini
- verified company dataset support
- startup profile import panel

### 5.2 Risk scoring

SPARC scores a startup across grouped domains such as:

- Digital & Data
- Legal & Governance
- Operational
- Macro & Emerging

Backend definitions live in:

- `risk_engine.py`
- `startup_shield_web/server.py` (`RISK_DISPLAY_GROUPS`)

### 5.3 Bundle recommendation

There are bundle-recommendation flows including:

- legacy / baseline logic
- V2 ranking logic
- bundle alternatives
- bundle fit explanations
- product-level recommendation cards

Relevant files:

- `bundle_catalog.py`
- `bundle_recommender_v2.py`
- `bundle_scoring_utils.py`

### 5.4 Pricing views

There are two pricing concepts in the app:

1. **Existing estimated quote / bundle quote surfaces**
   - based on internal pricing and bundle pricing utilities
   - rendered in the main results experience

2. **Premium Triage**
   - separate formula-chain calculator
   - calls `/api/pricing`
   - uses the `pricing/` model

### 5.5 Outreach generation

Outreach is a first-class feature.

Includes:

- company outreach
- signal outreach
- founder pitch support
- objection / pitch library usage
- email templates

Relevant files:

- `api/outreach.py`
- `startup_shield_web/email-template-signal-outreach.html`
- `email-template-rm-outreach.html`
- `startup_shield_web/server.py` (pitch library preload)

### 5.6 Signal Radar

Signal Radar is a lead engine / trigger-monitoring surface.

Inputs:

- public news / business / regulatory triggers
- structured signal rules
- mapped insurance implications

Relevant files:

- `api/signals.py`
- `signals.md`
- `signals_inventory.csv`
- `startup_shield_web/signal_rules.py`

Current normalized signal inventory artifact:

- `signals_inventory.csv`

### 5.7 Pipeline dashboard

There is a pipeline screen powered by `/api/pipeline` that surfaces startup opportunities and filters.

### 5.8 Policy wording comparison

There is a policy comparison flow using:

- `policy_wording.py`
- `/api/policy/compare` behavior from the local app flow

### 5.9 Downstream opportunities

There is a downstream-opportunities module in the Actions tab.  
It uses:

- `b2b2b_map.py`

The rendering function returns nothing if no mapped opportunities exist, so the section can appear absent depending on sector/customer type match quality.

---

## 6. Results Page Structure

Main render entry:

- `renderResults(result)` in `startup_shield_web/app.js`

The results screen currently contains tabs:

- `Bundle`
- `Outreach`
- `Estimated Quote`
- `Risk scores`
- `Actions`

Important rendered sections include:

- top hero / company summary
- KPI strip
- bundle recommendation
- outreach kit
- pricing panels
- methodology modal/panel
- downstream opportunities
- founder context strip
- policy wording comparison

### Important runtime state

The current analyzed result is stored globally after render:

- `window.__result`
- `window.__refineResult`

The current profile is also stored in:

- `state.profile`

If a Claude task needs the active analyzed profile after results render, the most reliable frontend access path is:

- `window.__result?.profile`

Inside `renderResults(result)`, use:

- `result.profile`

### Premium Triage location

Current helper functions in `app.js` include:

- `renderEstimateQuoteButton(result)`
- `loadPricingPanel(...)`
- `renderPricingCalculator(...)`

The Premium Triage panel is mounted under:

- `#pricing-panel`

---

## 7. Design / UX Rules

The project has a defined design system and should not drift into generic SaaS UI.

Read:

- `PRODUCT.md`
- `DESIGN.md`

High-level constraints:

- serious, high-credibility underwriting tone
- off-white “assessment paper” background
- restrained use of red as accent
- Space Grotesk + DM Sans typography
- no teal admin dashboard energy
- no consumer-fintech gradients/blobs
- no legacy banking-portal ugliness
- layered information density
- “show the math” wherever possible

SPARC should feel like a risk briefing / command surface, not a template dashboard.

---

## 8. API Surface Summary

### `/api/meta`
Used for app metadata / runtime info.

### `/api/company-profiles`
Searches and fetches startup profiles.

### `/api/autofill`
Uses Gemini and other logic to build a startup profile from company name and public information.

### `/api/analyze`
Pure Python analysis layer for turning a profile into:

- scores
- recommendations
- bundle outputs
- pricing-support outputs
- actions
- outreach context

### `/api/signals`
Returns Signal Radar data. Has had hardening work around fallbacks and packaging.

### `/api/pipeline`
Returns pipeline/dashboard data.

### `/api/outreach`
Returns outreach prompts and generated support content.

### `/api/pricing`
Returns:

- `quote`
- `loadings_catalog`

Backed by:

- `pricing/model.py`

---

## 9. Pricing Subsystem Constraints

This is important.

The `pricing/` directory is already a structured pricing engine and should not be casually rewritten.

### Core facts

- `pricing/model.py` contains `quote()`
- `pricing/parameters.yaml` is the source of truth for parameters
- every rate/factor should be source-backed
- it is **indicative only**
- it is **not a bindable quote**
- it must remain India-specific
- it should not import US benchmark logic

### Output expectation

Pricing should produce:

- a range, not a single point estimate
- factor trace
- source citations
- data quality score
- placeholders list
- disclaimer

### Existing disclaimer language

Keep this visible in pricing surfaces:

> Indicative only under IRDAI File-and-Use detariffed regime. Not a bindable quote.

### Known pricing UI behavior

Premium Triage supports inline editing of:

- base rate
- rating multipliers
- loadings / discounts

But not:

- GST
- stamp duty
- expense multiplier
- uncertainty band
- clamp rules

---

## 10. Signal Inventory Context

The signal research is substantial and structured.

Primary research sources in repo:

- `signals.md`
- `signals_inventory.csv`

Current normalized count in `signals_inventory.csv`:

- `151` rows

Signal domains represented:

- Public business signals
- Liability
- Cyber & Financial Lines
- Property & Engineering
- Employee Benefits
- Transit / Motor / Trade

If a Claude task touches Signal Radar, it should preserve:

- domain mapping
- rationale
- telemetry-source logic
- mapped ICICI Lombard products

---

## 11. Data Model Notes

The local server defines a large `DEFAULT_PROFILE` in `startup_shield_web/server.py`.

Important profile fields include:

- `startup_name`
- `sector`
- `sub_sector`
- `funding_stage`
- `team_size`
- `operations`
- `data_handled`
- `regulatory`
- `physical_assets`
- `has_investors`
- `annual_revenue_cr`
- `total_insurable_asset_value_cr`
- `gross_profit_cr`
- `fleet_count`
- `healthcare_operations`
- `payment_or_card_program`
- `claims_last_3_years`

Two commercially important numeric fields that now exist in the profile model:

- `annual_revenue_cr`
- `total_insurable_asset_value_cr`

These are used in pricing and summary presentation contexts and should not be dropped.

---

## 12. Deployment / Runtime

### Local

Run:

```bash
py startup_shield_web/server.py 5181
```

or any other port.

### Production

Deployed through:

- `vercel.json`

Static frontend files:

- `startup_shield_web/index.html`
- `startup_shield_web/app.js`
- `startup_shield_web/styles.css`

Serverless Python functions back the APIs.

### Environment

Minimum important environment variable:

- `GEMINI_API_KEY`

Other useful ones from `requirements.txt` and server runtime:

- `GEMINI_MODEL`
- `GEMINI_MAX_TOKENS`
- `GEMINI_TIMEOUT_SECONDS`
- `SPARC_DB_PATH`
- `VERCEL`

### Dependencies

The repo is mostly standard-library Python plus:

- `PyYAML>=6.0.1`

---

## 13. Testing Surface

Test directory:

- `tests/`

Current test modules include:

- `test_bundle_catalog_v1_patch.py`
- `test_bundle_v2.py`
- `test_company_profiles.py`
- `test_legacy_bundle_global.py`
- `test_outreach_generation.py`
- `test_policy_wording.py`
- `test_pricing.py`
- `test_pricing_engine.py`
- `test_v2_engine.py`
- `test_why_it_matters_payload.py`

Basic static checks commonly used:

```bash
py -m py_compile startup_shield_web/server.py api/pricing.py api/analyze.py
node --check startup_shield_web/app.js
```

---

## 14. Known Working Conventions / Guardrails

When editing this project, Claude should follow these rules:

1. **Do not rewrite the pricing model casually.**
   - Treat `pricing/model.py` and `pricing/parameters.yaml` as structured infrastructure.

2. **Do not make the UI generic.**
   - Use `PRODUCT.md` and `DESIGN.md` as the design authority.

3. **Preserve Indian specificity.**
   - IRDAI / RBI / DPDP / ONDC / DGCA framing
   - INR
   - no US-first language

4. **Prefer compositional changes over broad rewrites.**
   - `app.js` is large and feature-dense.
   - Make scoped edits.

5. **Preserve existing tabs and flows unless explicitly asked to replace them.**
   - Especially `Bundle`, `Outreach`, `Estimated Quote`, `Risk scores`, `Actions`.

6. **Keep the system explainable.**
   - Show math, sources, rationale.

7. **Assume the repo may be dirty.**
   - Do not revert unrelated user changes.

8. **Local and Vercel behavior are not always identical.**
   - The autofill/analyze split and packaging behavior matter.

---

## 15. High-Value Files to Inspect First

If Claude needs to make feature changes, start with these files:

- `startup_shield_web/app.js`
- `startup_shield_web/styles.css`
- `startup_shield_web/server.py`
- `vercel.json`
- `risk_engine.py`
- `bundle_recommender_v2.py`
- `pricing/model.py`
- `pricing/parameters.yaml`
- `signals.md`
- `signals_inventory.csv`
- `PRODUCT.md`
- `DESIGN.md`

---

## 16. Suggested Prompt Wrapper for Claude

Use this as the opening instruction when handing the repo to Claude:

> You are working on SPARC, an ICICI Lombard startup-insurance decision support system. Read `CLAUDE_PROJECT_CONTEXT.md` first, then inspect only the files needed for the task. Preserve the existing product intent: high-credibility Indian insurance risk analysis, bundle recommendation, signal radar, outreach generation, and indicative premium support. Do not genericize the UI, do not rewrite the pricing engine unless explicitly asked, and keep all reasoning India-specific, explainable, and source-aware. Prefer scoped edits in `startup_shield_web/app.js`, `startup_shield_web/styles.css`, `startup_shield_web/server.py`, and the `api/` functions. Before changing behavior, identify the exact render/function boundaries involved.

---

## 17. If the Task Is UI-Specific

Tell Claude this as well:

> The UI is vanilla JS and CSS. The main results surface is rendered by `renderResults(result)` in `startup_shield_web/app.js`. The active analyzed profile after render is available at `window.__result?.profile`, and also in `state.profile`. Premium Triage exists and is mounted under `#pricing-panel`. Do not introduce framework assumptions.

---

## 18. If the Task Is Pricing-Specific

Tell Claude this:

> The pricing engine already exists under `pricing/`. `pricing/model.py` provides the quote engine. `pricing/parameters.yaml` is the source of truth for rates/factors/loadings. The app calls `/api/pricing`. Maintain indicative-range behavior, factor trace, source citations, data-quality score, and disclaimer. Never convert it into a bindable or unsourced quote engine.

---

## 19. If the Task Is Signal-Radar-Specific

Tell Claude this:

> Signal research is already normalized into `signals_inventory.csv` from `signals.md`. Keep the columns `signal`, `domain`, `telemetry_source`, `rationale`, and `mapped_ICICI_Lombard_products`. Signal Radar is a lead engine, not just a news feed. Preserve the mapping from public triggers to RM action and insurance implications.

