# Claude Chat Session Summary — 2026-05-18

## What We Did

### 1. GenAI Usage Audit
Mapped all GenAI usage across the SPARC codebase. Found 4 active Gemini calls (all via `call_gemini_json()` using `gemini-2.5-flash`):
- `why_it_matters` — per-product plain-English rationale
- `why_it_matters` on bundle level — bundle-level insight
- `bundle_insights` — Gemini summary of recommended bundle
- Outreach email drafts — contextual email generation

And 1 removed feature (GenAI reranking via `genai_recommender.py`).

---

### 2. GenAI Reranking Removed
Deleted `genai_recommender.py` (396 lines) and its test file `tests/test_genai_recommender.py`.

Removed from `server.py`:
- Import of `normalize_mode`, `rerank_payload`
- Functions: `_genai_mode()`, `_log_genai_shadow_diff()`, `_refresh_primary_genai_dependents()`, `_apply_genai_recommendation_mode()`
- Simplified `score()` to return deterministic results directly

**Why:** The deterministic engine already scores products correctly. LLM reranking was adding noise, not signal.

Kept: `_shadow_log_path()` and `_log_diff()` — these serve legacy/v2 engine comparison, not GenAI.

---

### 3. UW + RM View Split — Analysis & Plan

**Proposal:** Split the app into two views:
- **Underwriter Workbench** — queue-based case review, risk panel, decision with premium override, audit trail
- **RM Workspace** — 3-step intake flow, results dashboard with bundle recommendations

**Finding:** A complete high-fidelity prototype already exists in `design_handoff_sparc/`:
- `uw-app.jsx` — queue + top bar (181 lines)
- `uw-case.jsx` — 7 panels: Risk, Assumptions, Pre-flight, Triggers, Pricing, Inputs, Context (499 lines)
- `uw-data.js` — seed data (UW_QUEUE with 7 cases: Razorpay, Niramai, Ather, etc.)
- `rm-app.jsx`, `rm-intake.jsx`, `rm-results.jsx` — full RM workspace

**Buildability:** Panels A-F map directly to existing `/api/analyze` response fields. Queue/SLA/capacity require new infrastructure.

**Estimated build time:** ~3-4 hours for Phase 1 (UW workbench wired to live API).

---

### 4. Vercel Deployment — Confirmed No Supabase Needed

- New static files + 5-6 lines in `vercel.json` is sufficient
- UW edits (SI overrides, loadings, audit notes) → `localStorage`
- Queue data → seeded JS constant from `uw-data.js`
- SQLite already ephemeral on Vercel (`tempfile.gettempdir()`)
- Supabase only needed for real multi-UW production workflow with persistent case history

---

## Next Steps (Not Yet Started)

**Phase 1 — UW Workbench (est. 3-4 hrs):**
1. Copy `design_handoff_sparc/styles.css` → `startup_shield_web/uw-styles.css`
2. Port `uw-app.jsx` + `uw-case.jsx` into `startup_shield_web/`, replace `window.uwGetCase()` with `fetch('/api/analyze')`
3. Create `startup_shield_web/uw.html` entry point
4. Add UW routes to `vercel.json`
5. Keep `UW_QUEUE`, `UW_LOADINGS`, `UW_DISCOUNTS`, `UW_CHECKS` from `uw-data.js` as seeded constants

**Phase 2 — RM Workspace (est. 2-3 hrs):**
- Port `rm-app.jsx`, `rm-intake.jsx`, `rm-results.jsx` similarly

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `startup_shield_web/server.py` | Flask backend (GenAI reranking removed) |
| `api/analyze.py` | Vercel serverless — main scoring endpoint |
| `vercel.json` | Deployment config |
| `design_handoff_sparc/uw-app.jsx` | UW root + queue prototype |
| `design_handoff_sparc/uw-case.jsx` | UW case workspace prototype (7 panels) |
| `design_handoff_sparc/uw-data.js` | Seed data for UW workbench |
| `design_handoff_sparc/rm-app.jsx` | RM workspace prototype |
| `design_handoff_sparc/README.md` | Full design handoff with API contract |
