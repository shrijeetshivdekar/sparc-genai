# Implementation Plan — SPARC Commerce Layer (v1)

**Principle (from CLAUDE.md):** simplicity first, surgical changes, goal-driven with verifiable checks. Compose over rewrite. Every changed line traces to a requirement.

**Sequencing logic:** build the SVP demo arc first (F5 → F1 → F3), then the management layer (F2 → F4). The pricing/risk engines are read-only dependencies and are touched in **no** milestone.

---

## Milestone 0 — Foundation (persistence + GWP helper)
*Enables everything; ships nothing user-facing.*

| Task | File(s) | Verify |
|---|---|---|
| Add SQLite layer + migrations | `db.py` | `db.migrate()` idempotent; tables exist |
| Seed RMs from contacts | `db.py`, `contacts.json` | one row in `rms` |
| GWP estimator wrapping pricing/premium | `gwp_estimator.py` | returns range + disclaimer; never point |
| Unit tests | `tests/test_gwp_estimator.py` | green |

**Exit criteria:** `py -m py_compile db.py gwp_estimator.py` passes; GWP test green; no existing test broken.

---

## Milestone 1 — F5 Funding Feed (pipeline source)
*First demo beat: "where leads come from."*

| Task | File(s) | Verify |
|---|---|---|
| CSV ingest + FundingSource abstraction | `funding_ingest.py` | sample CSV → N leads |
| Auto-analyse each lead (non-LLM bulk path) | `funding_ingest.py` → existing analyze | each lead has bundle + GWP |
| `/api/commerce/funding` GET/POST | `api/commerce_funding.py`, `server.py`, `vercel.json` | list + claim work |
| Claim → creates account, moves to Prospect | `pipeline_service.py` | `accounts` row + `pipeline_event` |
| Feed UI (cards, filters, import modal) | `app.js`, `styles.css` | renders per UI spec |
| Tests | `tests/test_funding_ingest.py` | green |

**Exit:** import seed CSV in UI → claim a lead → it appears in Pipeline as Prospect.

---

## Milestone 2 — F1 GWP Dashboard (market size)
*Second demo beat: "how big is this."*

| Task | File(s) | Verify |
|---|---|---|
| Funnel + territory GWP + top-leads queries | `metrics_service.py`, `pipeline_service.py` | query returns ranges |
| `/api/commerce/dashboard` GET | `api/commerce_dashboard.py`, `server.py`, `vercel.json` | contract matches TRD |
| Opportunity UI (hero, funnel strip, leads) | `app.js`, `styles.css` | matches UI spec; Signal Red ≤10% |
| Money formatter (L/Cr, ranges) | `app.js` util | `₹87–142 Cr` renders |

**Exit:** Opportunity screen shows territory GWP range, valued funnel, sortable top leads, disclaimer present.

---

## Milestone 3 — F3 Proposal PDF (the closer)
*Third demo beat: "RM walks out with this."*

| Task | File(s) | Verify |
|---|---|---|
| Proposal payload builder | `proposal_builder.py` | payload has all covers + disclaimer |
| HTML template (DESIGN tokens) + PDF render | `templates/proposal.html`, `proposal_builder.py` | PDF < 10s |
| Inline QR (data-URI/SVG) | `proposal_builder.py` | QR resolves to analysis URL |
| `/api/commerce/proposal` POST | `api/commerce_proposal.py`, `server.py`, `vercel.json` | returns `pdf_url` |
| Generate action + preview modal + attach-to-email | `app.js`, reuse `/api/outreach` | downloads + attaches |
| Tests | `tests/test_proposal_builder.py` | disclaimer + covers present |

**Exit:** from a Pipeline/Top-lead card → Generate proposal → branded PDF with locked disclaimer; attach to outreach email.

**→ Phase 1 (demo-critical) complete. SVP demo runnable end-to-end.**

---

## Milestone 4 — F2 RM Performance
| Task | File(s) | Verify |
|---|---|---|
| Event logging on analyse/quote/proposal/claim/convert | `pipeline_service.py`, relevant api routes | `events` populated |
| Leaderboard + conversion + speed queries | `metrics_service.py` | per TRD/schema views |
| Weekly digest (structured → outreach) | `metrics_service.py`, `/api/outreach` | digest object renders |
| `/api/commerce/metrics` GET | `api/commerce_metrics.py`, `server.py`, `vercel.json` | contract matches |
| Performance UI (leaderboard, sector map, tiles, digest card) | `app.js`, `styles.css` | flat reference data, paired labels |
| Tests | `tests/test_metrics_service.py` | green |

**Exit:** Performance screen shows live leaderboard + conversion; `Send digest` dispatches via outreach.

---

## Milestone 5 — F4 Renewal & Upsell Engine
| Task | File(s) | Verify |
|---|---|---|
| Alert evaluation (renewal/upsell/at-risk/gap) | `alert_engine.py` | each type fires on threshold |
| Delta-GWP via `estimate_delta_gwp` | `gwp_estimator.py` | range delta |
| `/api/commerce/alerts` GET/POST | `api/commerce_alerts.py`, `server.py`, `vercel.json` | list + dismiss |
| Renewals UI (sorted queue, summary tile) | `app.js`, `styles.css` | sorted by delta GWP |
| Sweep trigger (on profile update + manual "re-evaluate") | `alert_engine.py` | alerts regenerate |
| Tests | `tests/test_alert_engine.py`, `tests/test_pipeline_service.py` | green |

**Exit:** changing a tracked account's stage/headcount raises a correctly-typed alert with delta GWP; at-risk logic fires on the 60/90-day rule.

---

## Cross-cutting tasks (every milestone)
- Register each new route in **both** `server.py` (local) and `vercel.json` (prod).
- Keep existing tabs/routes byte-identical in contract.
- Add the pilot-token gate on commerce routes when `VERCEL` is set.
- Run after each milestone:
  ```
  py -m py_compile <new modules> api/commerce_*.py server.py
  node --check startup_shield_web/app.js
  py -m pytest tests/ -q
  ```

## Risk register
| Risk | Mitigation |
|---|---|
| PDF library unavailable in serverless | Use stdlib-light HTML→PDF; fall back to server-rendered HTML + print-to-PDF if needed |
| Gemini quota on bulk auto-analyse (F5) | Use non-LLM analyse path for bulk; LLM only on single RM-initiated analyses |
| SQLite ephemerality on Vercel | `/tmp` for pilot; `SPARC_DB_URL` (external) for production persistence |
| `app.js` size / merge risk | Scoped, additive functions; new Commerce mode isolated from `renderResults` |
| Point-estimate leakage | Schema + estimator enforce `_low`/`_high`; UI formatter rejects single values |

## Definition of done (v1)
- All five features behind the Commerce mode, demoable end-to-end on the pilot dataset.
- Zero change to risk/pricing engine behaviour or existing tab contracts.
- All new tests green; static checks pass.
- Every premium surface shows a range + IRDAI disclaimer.
- UI passes DESIGN.md review (Signal Red ≤10%, no SaaS clichés, paired status colors).
