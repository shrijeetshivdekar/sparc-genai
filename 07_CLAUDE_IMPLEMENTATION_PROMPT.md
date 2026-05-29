# Claude Implementation Prompt — SPARC Commerce Layer

> Paste this as the opening instruction when handing the repo to Claude (or Claude Code). It encodes the build, the order, and the guardrails. The six spec files (`01_PRD.md` … `06_APP_FLOW.md`) are the source of truth; this prompt is the operating instruction.

---

## ROLE & CONTEXT

You are working on **SPARC | Startup Shield**, an ICICI Lombard startup-insurance decision-support system. Read `CLAUDE.md` and `PRODUCT.md`/`DESIGN.md` first, then the six Commerce Layer specs: `01_PRD.md`, `02_TRD.md`, `03_BACKEND_SCHEMA.md`, `04_UI_UX_DESIGN.md`, `05_IMPLEMENTATION_PLAN.md`, `06_APP_FLOW.md`.

SPARC v1 was rejected by a Sales & Commerce SVP because it spoke underwriting, not revenue. You are building the **Commerce Layer**: an additive, revenue-facing layer over the existing engine that surfaces GWP, pipeline, conversion, RM productivity, proposals, renewals, and funding leads. Five features: F1 GWP Dashboard, F2 RM Performance, F3 Proposal PDF, F4 Renewal/Upsell Engine, F5 Funding Feed.

## HARD CONSTRAINTS (do not violate)

1. **Do not modify the risk or pricing engines.** `risk_engine.py`, `bundle_recommender_v2.py`, `pricing/model.py`, `pricing/parameters.yaml`, `premium_estimator.py` are READ-ONLY. Call their public functions only. If you think one must change, STOP and ask.
2. **Indicative pricing only.** Every premium/GWP value is a **range** (`_low`/`_high`), never a single point. Every premium surface carries verbatim: *"Indicative only under IRDAI File-and-Use detariffed regime. Not a bindable quote."* (Proposal adds: *"Valid 30 days, subject to underwriting confirmation."*)
3. **India-specific.** IRDAI / RBI / DPDP / DGCA / ONDC framing, INR, NIC 2008. No US benchmarks, no US-first language.
4. **Design authority is DESIGN.md.** Signal Red `#AD1E23` on ≤10% of any screen; Assessment Paper `#FAFAF8` canvas; Space Grotesk headings at `-0.03em`; content cards float, data rows flat. No SaaS admin grids, no teal, no gradient text, no `border-left` accent stripes, no glassmorphism on content cards, no `transition: all`. Respect `prefers-reduced-motion`.
5. **Compose, don't rewrite.** `app.js` is large. Add Commerce as a **new top-level mode**, isolated from `renderResults`. Do not touch existing tabs (`Bundle`, `Outreach`, `Estimated Quote`, `Risk scores`, `Actions`) or existing routes (`/api/analyze`, `/api/pricing`, `/api/signals`, `/api/outreach`, `/api/pipeline`).
6. **Register every new route in BOTH** `server.py` (local) and `vercel.json` (prod).
7. **Surgical diffs.** Every changed line traces to a spec requirement. Don't refactor adjacent code. Don't delete pre-existing dead code.

## WORKING METHOD (from CLAUDE.md)

- State assumptions explicitly before coding. If a spec is ambiguous, present options — don't pick silently.
- Simplest code that satisfies the spec. No speculative abstractions.
- For each milestone: state a short plan with verifiable checks, implement, then run the checks.
- After every milestone, run:
  ```
  py -m py_compile <new modules> api/commerce_*.py server.py
  node --check startup_shield_web/app.js
  py -m pytest tests/ -q
  ```
  All existing tests must stay green.

## BUILD ORDER (follow 05_IMPLEMENTATION_PLAN.md exactly)

**M0 — Foundation:** `db.py` (SQLite + idempotent migrations per `03_BACKEND_SCHEMA.md`, seed `rms` from `contacts.json`), `gwp_estimator.py` (wrap pricing/premium → range + disclaimer; never point). Tests: `test_gwp_estimator.py`.

**M1 — F5 Funding Feed:** `funding_ingest.py` (CSV → auto-analyse via existing NON-LLM path → valued leads), `pipeline_service.py` (claim → account + pipeline_event), `api/commerce_funding.py`, Feed UI in `app.js`/`styles.css`. Tests: `test_funding_ingest.py`.

**M2 — F1 GWP Dashboard:** `metrics_service.py` (funnel, territory GWP, top leads), `api/commerce_dashboard.py`, Opportunity UI + money formatter (L/Cr, ranges). 

**M3 — F3 Proposal PDF:** `proposal_builder.py` (+ `templates/proposal.html`, inline QR), `api/commerce_proposal.py`, Generate action + preview modal + attach-to-email via existing `/api/outreach`. Tests: `test_proposal_builder.py`. **← Phase 1 demo complete; verify the full SVP arc runs end-to-end.**

**M4 — F2 RM Performance:** event logging on analyse/quote/proposal/claim/convert, `metrics_service` leaderboard/conversion/speed/digest, `api/commerce_metrics.py`, Performance UI, digest via `/api/outreach`. Tests: `test_metrics_service.py`.

**M5 — F4 Renewal Engine:** `alert_engine.py` (renewal/upsell/at_risk/coverage_gap + delta GWP), `api/commerce_alerts.py`, Renewals UI. Tests: `test_alert_engine.py`, `test_pipeline_service.py`.

## ACCEPTANCE (per feature) — verify against PRD §4

- **F1:** territory GWP renders as a range; funnel shows count+GWP per stage; top leads sortable; disclaimer present.
- **F2:** leaderboard filterable; conversion rate per RM/sector; weekly digest object renders and sends via outreach.
- **F3:** PDF < 10s; mandatory disclaimer verbatim; premium as range; attachable to outreach; DESIGN-themed (not generic).
- **F4:** alert fires on correct threshold; typed reason + delta-GWP range; at-risk = renewal ≤60d AND no engagement ≤90d.
- **F5:** each lead auto-valued with bundle + GWP; filterable; claimable → moves to Prospect; source attributed.

## DELIVERY PROTOCOL

For each milestone, in one turn:
1. One-paragraph plan + explicit assumptions.
2. The diffs (new files + scoped edits).
3. The verification commands you ran and their results.
4. A one-line "ready for next milestone" or a blocked-question if a constraint is at risk.

Do not proceed past a milestone whose checks fail. Do not batch all five features into one giant diff — ship milestone by milestone so each is reviewable.

## FIRST ACTION

Confirm you have read all six specs + `CLAUDE.md` + `DESIGN.md`. Then state your M0 plan and assumptions (especially: SQLite path strategy for local vs Vercel, and which existing analyze function is the non-LLM bulk path for F5). Wait for go, then implement M0.
