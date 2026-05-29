# TRD — SPARC Commerce Layer (v1)

**Document:** Technical Requirements Document
**Depends on:** 01_PRD.md
**Stack of record:** vanilla JS frontend (`app.js`, `index.html`, `styles.css`), local `server.py`, Vercel serverless functions under `api/`, Python domain logic at repo root, pricing subsystem under `pricing/`.

---

## 1. Architectural principle

The Commerce Layer is **additive and read-mostly over the existing engine**. It introduces:
- a thin **persistence layer** (accounts, pipeline, events, alerts) — currently SPARC is stateless per analysis,
- five **new API routes**,
- five **new frontend surfaces** (one new top-level mode + screens), and
- a **GWP estimation helper** that wraps the existing pricing/premium modules.

It must not modify: `risk_engine.py`, `bundle_recommender_v2.py`, `pricing/model.py`, `premium_estimator.py` (read-only consumers only).

```
                  ┌─────────────────────────────────────────────┐
                  │            EXISTING ENGINE (read-only)        │
                  │  risk_engine · bundle_recommender_v2 ·        │
                  │  pricing/model · premium_estimator            │
                  └───────────────┬─────────────────────────────┘
                                  │  (function calls only)
                  ┌───────────────▼─────────────────────────────┐
                  │          COMMERCE SERVICE LAYER (new)         │
                  │  gwp_estimator · pipeline_service ·           │
                  │  alert_engine · proposal_builder ·            │
                  │  funding_ingest · metrics_service             │
                  └───────────────┬─────────────────────────────┘
                                  │
        ┌─────────────────────────┼──────────────────────────────┐
        │                         │                              │
 ┌──────▼──────┐         ┌────────▼────────┐            ┌────────▼────────┐
 │  SQLite DB  │         │  new api/ routes │            │   PDF renderer  │
 │ (SPARC_DB)  │         │  (5 endpoints)   │            │  (proposal)     │
 └─────────────┘         └─────────────────┘            └─────────────────┘
                                  │
                          ┌───────▼────────┐
                          │  app.js surfaces│
                          │  (Commerce mode)│
                          └────────────────┘
```

---

## 2. New backend modules (repo root)

| Module | Responsibility | Key functions |
|---|---|---|
| `gwp_estimator.py` | Wrap pricing/premium engines to return an INR GWP **range** for a profile or bundle | `estimate_gwp(profile) -> GwpRange`, `estimate_delta_gwp(old, new) -> GwpRange` |
| `pipeline_service.py` | CRUD for accounts & pipeline stage transitions | `upsert_account`, `move_stage`, `claim_lead`, `list_pipeline` |
| `alert_engine.py` | Evaluate tracked accounts for renewal/upsell/at-risk/gap | `evaluate_account`, `evaluate_all`, `list_alerts`, `dismiss_alert` |
| `proposal_builder.py` | Build proposal payload from an analysis result | `build_proposal_payload(result) -> dict` |
| `funding_ingest.py` | Ingest funding events (CSV v1), auto-analyse, value as leads | `ingest_csv(path)`, `to_leads()` |
| `metrics_service.py` | Aggregate RM activity, funnel, conversion, digest | `funnel()`, `rm_leaderboard()`, `weekly_digest()` |
| `db.py` | SQLite connection + migrations (uses `SPARC_DB_PATH`) | `get_conn`, `migrate` |

### GWP estimation rule
`gwp_estimator.estimate_gwp` MUST:
- call the existing pricing path (`pricing/model.quote` where inputs allow, else `premium_estimator` bands),
- return `{low, high, basis, data_quality, disclaimer}` — never a single point,
- propagate the existing disclaimer string,
- aggregate at territory level by summing midpoints but **displaying ranges** (sum of lows … sum of highs).

---

## 3. New API routes

All routes return JSON, mirror existing `api/` function style, and are registered in `vercel.json` and the local `server.py` router. Auth: pilot is single-tenant; gate behind a shared `SPARC_PILOT_TOKEN` header if `VERCEL` env is set.

| Route | Method | Purpose | Returns |
|---|---|---|---|
| `/api/commerce/dashboard` | GET | F1 territory GWP, funnel, top leads | `{territory_gwp, funnel, top_leads[]}` |
| `/api/commerce/metrics` | GET | F2 leaderboard, conversion, digest | `{leaderboard[], conversion{}, digest{}}` |
| `/api/commerce/proposal` | POST | F3 build + render proposal PDF | `{pdf_url, proposal_id}` |
| `/api/commerce/alerts` | GET / POST | F4 list / dismiss alerts | `{alerts[]}` / `{ok}` |
| `/api/commerce/funding` | GET / POST | F5 feed list / claim lead | `{leads[]}` / `{ok, account_id}` |

### Route contracts (selected)

**GET `/api/commerce/dashboard?city=&sector=&stage=`**
```json
{
  "territory_gwp": { "low_inr": 870000000, "high_inr": 1420000000, "currency": "INR",
                     "basis": "indicative bands x addressable count", "disclaimer": "..." },
  "funnel": [
    { "stage": "prospect",  "count": 2340, "gwp_low": 5.2e8, "gwp_high": 8.9e8 },
    { "stage": "analysed",  "count": 410,  "gwp_low": 9.0e7, "gwp_high": 1.6e8 },
    { "stage": "quoted",    "count": 120,  "gwp_low": 3.0e7, "gwp_high": 5.5e7 },
    { "stage": "converted", "count": 28,   "gwp_low": 8.0e6, "gwp_high": 1.4e7 }
  ],
  "top_leads": [
    { "account_id": "acc_...", "name": "Acme HealthTech", "sector": "HealthTech",
      "stage": "Series A", "bundle": "Enterprise Secure",
      "gwp_low_inr": 2800000, "gwp_high_inr": 4500000, "city": "Bengaluru" }
  ]
}
```

**POST `/api/commerce/proposal`**
```json
// request
{ "account_id": "acc_...", "analysis": { /* window.__result payload or stored result */ } }
// response
{ "proposal_id": "prop_...", "pdf_url": "/files/proposals/prop_....pdf",
  "generated_at": "2026-05-28T10:00:00Z" }
```

**POST `/api/commerce/funding` (claim)**
```json
// request
{ "action": "claim", "lead_id": "lead_...", "rm_email": "ilom43171@icicilombard.com" }
// response
{ "ok": true, "account_id": "acc_...", "stage": "prospect" }
```

---

## 4. GWP estimation: data flow

```
profile ──► gwp_estimator.estimate_gwp
                │
                ├─ if exposure inputs present ──► pricing.model.quote() ──► range
                └─ else ──► premium_estimator bands (micro/small/growth) ──► range
                                                            │
                                                            ▼
                                  { low, high, basis, data_quality, disclaimer }
```

- Bucket mapping reuses `premium_estimator.STARTUP_SIZE_BUCKETS` (stage + team_max).
- Bundle-level GWP = sum of cover-level ranges already produced by the engine; do not invent rates.
- Territory GWP = Σ low … Σ high over accounts in scope.

---

## 5. Persistence

Currently SPARC uses `SPARC_DB_PATH` (referenced in CLAUDE context). v1 introduces SQLite tables (schema in `03_BACKEND_SCHEMA.md`). Migrations run on server boot (`db.migrate()`), idempotent. On Vercel, use a file path under `/tmp` for ephemeral pilot or an external SQLite/Postgres if persistence across cold starts is required (flag: `SPARC_DB_URL`).

---

## 6. PDF rendering

- Library: server-side HTML→PDF. Prefer a dependency already viable in the Python serverless context. v1: render a styled HTML template (DESIGN.md tokens) and convert with a single library; keep it stdlib-light per repo convention (repo is mostly stdlib + PyYAML).
- Template lives at `templates/proposal.html`, themed with Signal Red / Space Grotesk / Assessment Paper.
- QR code: encode the SPARC analysis URL (`/?account=<id>`); generate as inline SVG/data-URI to avoid binary asset handling.
- Output stored under a served path (`/files/proposals/`), returned as `pdf_url`.

---

## 7. Funding ingestion (F5)

- v1 source: **CSV import** (`funding_ingest.ingest_csv`) — no paid licence needed for demo.
- Required columns: `company, city, sector, stage, amount_inr, round, source, announced_on`.
- Pipeline: each row → synthesise a minimal profile → call existing `analyze` path → store as `lead` with estimated GWP.
- Connector abstraction (`FundingSource`) so a Tracxn/VCCircle API can be dropped in later without touching callers.

---

## 8. Metrics & digest (F2)

- Activity events are written on every analyse / quote / proposal / claim (see `events` table).
- `metrics_service.funnel()` counts and values events by stage.
- `weekly_digest()` returns a structured summary; rendering to email reuses the existing `/api/outreach` pipeline (compose digest → outreach send), not a new mailer.

---

## 9. Performance & limits
- Dashboard query target < 500ms on pilot dataset (≤ 5k accounts) — index on `(city, sector, stage)`.
- Proposal generation < 10s (PRD acceptance).
- Funding ingest batch: process ≤ 1k rows per import; analyse calls rate-limited to avoid Gemini quota (reuse `GEMINI_*` env timeouts; prefer non-LLM analyse path for bulk).

---

## 10. Security / compliance
- All premium outputs carry the IRDAI indicative disclaimer; proposal PDF disclaimer wording is locked.
- No new PII beyond `contacts.json`; founder contact captured only if RM enters it.
- Pilot token gate on commerce routes when deployed.

---

## 11. Testing surface (add to `tests/`)
- `test_gwp_estimator.py` — range output, never point; bucket mapping; disclaimer present.
- `test_pipeline_service.py` — stage transitions, claim idempotency.
- `test_alert_engine.py` — each alert type fires on the right threshold; delta GWP computed.
- `test_proposal_builder.py` — payload contains mandatory disclaimer + all covers.
- `test_funding_ingest.py` — CSV → leads, GWP populated.
- `test_metrics_service.py` — funnel counts/values, digest shape.
- Static: `py -m py_compile` new modules + `api/commerce_*.py`; `node --check startup_shield_web/app.js`.

---

## 12. Non-regression guardrails
- Existing routes (`/api/analyze`, `/api/pricing`, `/api/signals`, `/api/outreach`, `/api/pipeline`) unchanged in contract.
- Existing tabs render identically; Commerce is a **new top-level mode**, not a change to results tabs.
- `window.__result` / `state.profile` access patterns reused, not replaced.
