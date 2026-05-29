# App Flow — SPARC Commerce Layer (v1)

End-to-end flows showing how a user moves through the Commerce Layer and how data moves through the system. Existing flows (manual analyse, autofill, signal radar, premium triage) are unchanged.

---

## 0. Mode entry

```
User opens SPARC
   │
   ▼
Topbar mode switch:  [ Analyse ]  [ Commerce ]
   │                                   │
   ▼ (existing)                        ▼ (new)
Manual / autofill analysis     Commerce mode → default screen: Opportunity (F1)
                                Left rail: Opportunity · Funding Feed · Pipeline · Renewals · Performance
```

---

## 1. F5 — Funding Feed → claim → pipeline (lead acquisition)

```
RM opens Funding Feed
   │
   ├─ (one-time) Import funding CSV ──► POST /api/commerce/funding {import}
   │        │
   │        ▼
   │   funding_ingest.ingest_csv()
   │        │  for each row:
   │        │     synthesise minimal profile
   │        │     ──► existing analyze (non-LLM bulk path)
   │        │     ──► gwp_estimator.estimate_gwp() → range
   │        │     ──► INSERT funding_leads (est_bundle, est_gwp_low/high)
   │        ▼
   │   leads stored (status=open)
   │
   ▼
GET /api/commerce/funding?city=&sector=&stage=
   │
   ▼
Feed renders lead cards (company · round · source · est bundle · GWP range)
   │
   ▼
RM clicks "Claim lead"
   │
   ▼
POST /api/commerce/funding {action:"claim", lead_id, rm_email}
   │
   ▼
pipeline_service.claim_lead()
   │   ├─ INSERT accounts (stage=prospect, source=funding_feed, rm_email)
   │   ├─ UPDATE funding_leads (status=claimed, account_id)
   │   ├─ INSERT pipeline_event (→prospect)
   │   └─ INSERT events (kind=lead_claimed, gwp range)
   ▼
Card shows CLAIMED (green) → "moved to Pipeline as Prospect"
```

---

## 2. F1 — Opportunity dashboard (executive view)

```
SVP opens Opportunity (default Commerce screen)
   │
   ▼
GET /api/commerce/dashboard?city=&sector=&stage=
   │
   ▼
metrics_service builds:
   ├─ territory_gwp  = Σ gwp_low … Σ gwp_high over accounts in scope
   ├─ funnel         = per-stage count + GWP range (schema funnel view)
   └─ top_leads      = accounts ordered by gwp_high desc (limit 10)
   │
   ▼
Render:
   ├─ Hero band: ₹low–high Cr addressable GWP + scope chips + disclaimer
   ├─ Funnel strip: Prospect → Analysed → Quoted → Converted (count + GWP)
   │     └─ leak flagged (amber + label) where Quoted→Converted drop is large
   └─ Top-value leads: floating cards, sortable
   │
   ▼
SVP clicks a lead "Open analysis →"  ──► loads stored analysis (window.__result shape)
```

---

## 3. RM analysis → stored account (bridge from existing engine)

```
RM runs analysis (existing Analyse mode)  OR  opens a claimed lead
   │
   ▼
Engine returns result (risk scores, bundle, triggers, covers)  → window.__result
   │
   ▼
On "Save to pipeline" (or auto on claimed-lead analyse):
   ├─ INSERT/UPDATE accounts (profile_json, stage=analysed)
   ├─ INSERT analyses (result_json, bundle, fit, triggers)
   ├─ gwp_estimator.estimate_gwp() ──► INSERT gwp_estimates (range)
   ├─ INSERT pipeline_event (→analysed)
   └─ INSERT events (kind=analysed, gwp range)
```

---

## 4. F3 — Proposal generation (the closer)

```
RM (from results / Pipeline card / Top-lead card) clicks "Generate proposal"
   │
   ▼
POST /api/commerce/proposal { account_id, analysis }
   │
   ▼
proposal_builder.build_proposal_payload()
   ├─ pull bundle + cover-level GWP ranges (from gwp_estimates / engine)
   ├─ pull regulatory triggers (analysis.triggers_json)
   ├─ pull RM block (contacts.json)
   ├─ build QR (data-URI → analysis URL)
   ├─ render templates/proposal.html (DESIGN tokens)
   ├─ HTML → PDF  (< 10s)
   ├─ lock disclaimer string (IRDAI File-and-Use, valid 30d)
   ├─ INSERT proposals (pdf_path, valid_until)
   └─ INSERT events (kind=proposal_generated)
   │
   ▼
Response { proposal_id, pdf_url }
   │
   ▼
Modal: PDF preview
   ├─ Download PDF
   └─ Attach to email ──► existing /api/outreach flow (founder email)
```

---

## 5. F4 — Renewal & upsell alerts

```
Trigger: profile update on a tracked account  OR  manual "Re-evaluate"  OR  nightly sweep
   │
   ▼
alert_engine.evaluate_account(account)
   │
   ├─ stage change (e.g. Series A → B) ───────► type=upsell
   ├─ team-size band crossed (e.g. >3500) ────► type=upsell / coverage_gap
   ├─ new regulatory trigger fired ───────────► type=coverage_gap
   ├─ renewal_due ≤60d AND last_engaged >90d ─► type=at_risk
   └─ renewal_due ≤60d ───────────────────────► type=renewal
   │      each: estimate_delta_gwp(old_bundle, new_bundle) → range
   ▼
INSERT alerts (type, reason, trigger_detail, delta_gwp_low/high, status=open)
   │
   ▼
RM opens Renewals
   │
   ▼
GET /api/commerce/alerts?status=open  (sorted by delta_gwp desc)
   │
   ▼
Render alert queue + "GWP at risk ≤60d" summary tile
   │
   ├─ "Review account →"  → opens account analysis
   └─ "Dismiss"           → POST /api/commerce/alerts {dismiss} → status=dismissed
```

---

## 6. F2 — Performance & weekly digest

```
Throughout usage: events appended (analysed | quoted | proposal_generated | lead_claimed | converted)
   │
   ▼
SVP opens Performance
   │
   ▼
GET /api/commerce/metrics?since=
   │
   ▼
metrics_service:
   ├─ rm_leaderboard()  (events grouped by rm)
   ├─ conversion by sector (quoted vs converted)
   ├─ speed metrics (median stage gaps from pipeline_events)
   └─ weekly_digest()  (structured summary)
   │
   ▼
Render leaderboard + sector map + speed tiles + digest preview card
   │
   ▼
"Send digest" ──► compose digest ──► existing /api/outreach ──► SVP email
```

---

## 7. State & contracts (quick reference)

| Surface | Reads | Writes |
|---|---|---|
| Funding Feed | `funding_leads` | `accounts`, `pipeline_events`, `events` (on claim) |
| Opportunity | `accounts`, `gwp_estimates`, funnel view | — |
| Pipeline | `accounts`, `gwp_estimates` | `pipeline_events` (on move) |
| Proposal | `analyses`, `gwp_estimates`, `contacts.json` | `proposals`, `events` |
| Renewals | `accounts`, `alerts` | `alerts` (on dismiss) |
| Performance | `events`, `pipeline_events` | — (digest → outreach) |

**Invariants across all flows:**
- Every premium is a **range** (`_low`/`_high`), never a point.
- Every premium surface carries the IRDAI indicative disclaimer.
- Existing engine modules are **read-only**; Commerce only calls their public functions.
- Commerce is a separate mode; existing tabs and routes are untouched.
