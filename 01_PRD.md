# PRD — SPARC Commerce Layer (v1)

**Document:** Product Requirements Document
**Product:** SPARC | Startup Shield — Commerce Layer
**Owner:** Product (SPARC)
**Status:** Draft for build
**Audience for the feature set:** SVP, Commercial Lines (Sales & Commerce)

---

## 1. Why this exists

SPARC v1 was rejected by the Sales & Commerce SVP. The reason was not quality — the risk engine, bundle logic, and pricing are sound. The reason was **language**. SPARC spoke underwriting (risk scores, regulatory citations, methodology). The SVP buys in one currency: **GWP, pipeline, conversion, RM productivity, retention.**

The Commerce Layer reframes SPARC from a *per-startup analysis tool* into a *revenue system*. It does not replace the existing engine. It sits on top of it and aggregates, surfaces, and monetises what the engine already produces.

### The reframe
| SPARC v1 (rejected) | SPARC Commerce Layer (this PRD) |
|---|---|
| "Risk analysis engine" | "GWP generation machine for the startup segment" |
| "Accurate bundle recommendations" | "RMs close faster with a proposal in hand" |
| "Regulatory citation layer" | "Surfaces ₹X Cr of addressable premium not being captured" |
| "Explainable scoring" | "Weekly pipeline dashboard — see what converts" |
| "Signal Radar" | "Alerts you when a startup raises money in your territory" |

---

## 2. Goals & non-goals

### Goals
1. Give the SVP a single screen quantifying the **GWP opportunity** SPARC unlocks.
2. Give sales management **visibility into RM activity and conversion**.
3. Let an RM leave a meeting with a **branded, sendable proposal** in under 10 seconds.
4. Make SPARC drive **renewal and upsell GWP**, not just new business.
5. Convert public **funding events into claimable, GWP-valued leads**.

### Non-goals
- Not a bindable quoting / policy-issuance system. All premium remains indicative under IRDAI File-and-Use.
- Not a CRM replacement. It is a pipeline intelligence layer; it can later sync to a CRM but does not become one in v1.
- Not a rewrite of the risk or pricing engine. Those are upstream dependencies, treated as read-only.
- Not a change to the existing tabs (`Bundle`, `Outreach`, `Estimated Quote`, `Risk scores`, `Actions`).

---

## 3. Target users

| Persona | Need | Primary feature |
|---|---|---|
| **SVP / Sales leadership** | Quantify opportunity, justify spend, see what converts | F1 GWP Dashboard, F2 RM Performance |
| **Relationship Manager (RM)** | More leads, faster close, retain accounts | F3 Proposal PDF, F4 Renewal Engine, F5 Funding Feed |
| **Founder (recipient)** | A clear document to take to their board | F3 Proposal PDF |

---

## 4. Feature set

### F1 — GWP Opportunity Dashboard
**Problem:** No aggregate, money-denominated view exists. The SVP cannot see scale.

**Solution:** An executive screen showing addressable GWP across territory and sector, a pipeline funnel valued in INR, and the top-value leads.

**User stories**
- As an SVP, I see total addressable GWP for my territory so I can size the opportunity.
- As an SVP, I see a funnel (Prospects → Analysed → Quoted → Converted) with INR at each stage so I know where deals leak.
- As an SVP, I see the top 10 leads ranked by estimated bundle premium so I know where to push.

**Acceptance criteria**
- Dashboard renders territory addressable GWP as a range (never a point estimate), consistent with the indicative-pricing rule.
- Funnel shows count + INR value per stage; values derive from the existing `premium_estimator` / pricing engine, not new numbers.
- Top-leads list is sortable by estimated GWP, sector, stage, city.
- Every aggregate carries the disclaimer: *"Indicative. Estimated GWP based on indicative premium bands; not bound business."*

### F2 — RM Performance & Conversion Intelligence
**Problem:** Zero management visibility. SPARC is invisible to the SVP after the demo.

**Solution:** RM activity leaderboard, bundle win rates, sector conversion map, speed metrics, and an auto-generated weekly SVP digest.

**User stories**
- As an SVP, I see per-RM analysed/quoted/pipeline-GWP so I can manage performance.
- As an SVP, I see which bundles convert and where deals stall by premium band.
- As an SVP, I receive a weekly digest email summarising activity and pipeline GWP.

**Acceptance criteria**
- Leaderboard filterable by week/month, city, sector.
- Conversion shown as a rate (quoted → converted) per RM and per sector.
- Weekly digest generates a structured summary object (rendered to email via existing outreach pipeline).
- No PII beyond RM identity already in `contacts.json`.

### F3 — One-Click Branded Proposal PDF
**Problem:** SPARC ends at a screen. Deals die where the RM has to hand-build a proposal.

**Solution:** A "Generate Proposal" action producing an ICICI Lombard-branded PDF: company, recommended bundle, cover-level summary, indicative premium range, the regulatory triggers that justified each cover, RM contact block, validity + IRDAI disclaimer, and a QR back to the SPARC analysis.

**User stories**
- As an RM, I click one button and get a branded PDF I can email to the founder.
- As a founder, I receive a document I can take to my board.

**Acceptance criteria**
- PDF generated server-side in < 10s for a standard profile.
- Contains mandatory disclaimer verbatim: *"Indicative only under IRDAI File-and-Use detariffed regime. Not a bindable quote. Valid 30 days, subject to underwriting confirmation."*
- Premium shown as a range with factor basis, mirroring the pricing engine output.
- PDF is downloadable and attachable to the existing Outreach email flow.
- Branding follows DESIGN.md (Signal Red, Space Grotesk, Assessment Paper); no generic template.

### F4 — Renewal & Upsell Trigger Engine
**Problem:** SPARC is acquisition-only. Retention and upsell GWP is unaddressed.

**Solution:** Watches pipeline accounts for stage/headcount/regulatory changes and raises renewal, upsell, at-risk, and coverage-gap alerts — each valued in INR delta GWP.

**User stories**
- As an RM, I'm alerted when an account crosses a threshold that changes its recommended bundle.
- As an RM, I see the delta GWP of an upsell so I know it's worth the call.
- As an SVP, I see total GWP at risk from upcoming renewals.

**Acceptance criteria**
- Alert fires when a tracked account's profile change crosses a configurable threshold (stage change, team-size band change, new regulatory trigger).
- Each alert carries a typed reason and an estimated delta-GWP range.
- At-risk logic: renewal due ≤ 60 days AND no RM engagement ≤ 90 days → flag with GWP-at-risk.
- Alerts dismissible and auditable (who/when).

### F5 — Funding Intelligence Feed (Pipeline Generator)
**Problem:** The SVP thinks "funded startup = prospect." SPARC doesn't convert funding events into valued leads automatically.

**Solution:** A feed of new funding events mapped to an instant SPARC analysis and an estimated GWP, filtered by territory, claimable by RMs.

**User stories**
- As an RM, I see newly funded startups in my city with an estimated bundle and GWP, and I claim the lead.
- As an SVP, I see total new fundable GWP surfaced this week by city and sector.

**Acceptance criteria**
- Each feed item auto-runs the existing analyze flow to produce score + recommended bundle + estimated GWP (no manual entry).
- Items filterable by city/sector/stage; claimable (assigns to RM, moves into pipeline as a Prospect).
- Source attribution shown per item (funding source/date).
- Ingestion is pluggable: manual CSV import for v1, API connector later. v1 must work with a seeded/imported dataset so it demos without a paid data licence.

---

## 5. Success metrics

| Metric | Baseline | Target (60-day pilot) |
|---|---|---|
| Addressable GWP made visible | ₹0 (no view) | Full territory sized |
| RM proposal turnaround | manual / hours | < 10s to PDF |
| Quote → proposal-sent rate | not tracked | tracked + ≥ 50% |
| Funding leads claimed / week | 0 | ≥ 70% of surfaced |
| Renewal/upsell alerts actioned | 0 | tracked |
| SVP weekly digest open | n/a | delivered weekly |

---

## 6. Constraints (inherited, non-negotiable)
- **India-specific** throughout — IRDAI / RBI / DPDP / DGCA / ONDC framing, INR, NIC 2008.
- **Indicative-only pricing** — ranges, factor trace, sources, disclaimer. Never bindable.
- **Design authority** — PRODUCT.md / DESIGN.md. No generic SaaS dashboard. Signal Red ≤ 10% per screen.
- **Scoped edits** — `app.js` is large; compose, don't rewrite. Preserve existing tabs/flows.
- **Pricing engine is infrastructure** — read from `pricing/model.py` and `premium_estimator.py`; do not rewrite.

---

## 7. Release phasing
- **Phase 1 (demo-critical):** F5 Funding Feed → F1 GWP Dashboard → F3 Proposal PDF. This is the SVP demo arc: pipeline → market size → closing moment.
- **Phase 2:** F2 RM Performance → F4 Renewal Engine.

---

## 8. Open questions
1. Funding data source for production (Tracxn / VCCircle licence) — v1 uses imported CSV.
2. Is RM auth needed for the leaderboard, or is single-tenant pilot acceptable? (Assume single-tenant pilot.)
3. Does the proposal PDF need legal/compliance sign-off on disclaimer wording before pilot? (Assume yes — wording locked from pricing subsystem.)
