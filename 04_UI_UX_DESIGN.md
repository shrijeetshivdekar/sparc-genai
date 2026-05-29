# UI/UX Design — SPARC Commerce Layer (v1)

**Design authority:** `DESIGN.md` ("The Risk War Room"). This spec inherits every rule. Where this document is silent, DESIGN.md governs.

**Non-negotiables carried in:**
- Signal Red `#AD1E23` on ≤ 10% of any screen — decisions and critical flags only.
- Assessment Paper `#FAFAF8` canvas; Pure White card fill only.
- Space Grotesk headings, `-0.03em` tracking at Title+; DM Sans body.
- Content cards float (ambient shadow); data rows are flat.
- No SaaS admin grids, no teal, no gradient text, no `border-left` accent stripes, no glassmorphism on content cards.
- `scale(0.97)` press feedback; respect `prefers-reduced-motion`; animate `transform`/`opacity` only.

---

## 1. Information architecture

The Commerce Layer is a **new top-level mode**, peer to the existing RM analysis flow — not a new results tab. Entry point: a mode switch in the fixed topbar.

```
TOPBAR  [SP]  SPARC | Startup Shield        [ Analyse ]  [ Commerce ]      RM ▾
                                               (existing)   (new mode)

COMMERCE MODE  ── left rail (sequential, DESIGN §Sidebar steps) ──
   ▸ Opportunity      (F1 GWP Dashboard)      ← default landing for SVP
   ▸ Funding Feed     (F5)
   ▸ Pipeline         (accounts by stage)
   ▸ Renewals         (F4 alerts)
   ▸ Performance      (F2 RM intelligence)
```

The left rail uses the existing sidebar-step component (transparent at rest, `#F1F1EE` hover, red-tint active). No icon-grid SaaS nav.

---

## 2. F1 — Opportunity (GWP Dashboard)

The screen the SVP sees first. Reads as a **briefing**, not a dashboard.

**Layout (single column, varied card density — never a uniform grid):**

1. **Hero band (dark, Board Navy `#151923`)** — full-width, the one command surface.
   - Eyebrow label (red pill, uppercase): `TERRITORY OPPORTUNITY`
   - Display headline (Space Grotesk 800): the GWP range, e.g. `₹87–142 Cr`
   - Sub: `addressable annual GWP · Bengaluru + Mumbai · 2,340 funded startups`
   - Right-aligned scope filters (city / sector / stage) as default chips.
   - Disclaimer line, Ink Faint, small: *"Indicative. Estimated GWP from indicative premium bands; not bound business."*

2. **Funnel strip** — four flat data tiles on Document Surface `#F1F1EE` (reference data → flat, no shadow). Each: stage label, count, GWP range. A thin connecting chevron between tiles, drawn in Ink Ghost. Leak between Quoted→Converted highlighted with Caution Amber label + icon (never color alone).

3. **Top-value leads** — list of floating content cards (`.r-card`, ambient shadow). Each card: company name (Title), sector + stage + city metadata (Label), bundle (body), and a right-pinned GWP range in Space Grotesk. Sort control above (GWP / sector / city). Primary action per card: `Open analysis →` (ghost button).

**Empty state:** "No accounts in scope yet. Import a funding feed to size the opportunity." → link to Funding Feed.

---

## 3. F5 — Funding Feed

Reads as an intelligence feed of claimable leads.

- **Header:** eyebrow `NEW THIS WEEK`, headline = surfaced GWP range, sub = count by city.
- **Filter row:** city / sector / stage chips (default/active states per DESIGN).
- **Feed cards (content cards):** each shows
  - company + round (`Acme HealthTech · Series A · ₹45 Cr raised`)
  - source + date (Reference Blue metadata, e.g. `VCCircle · 22 May 2026`)
  - auto-analysis result: estimated bundle + risk headline
  - GWP range pinned right
  - Primary action (Signal Red, the one decision on the card): `Claim lead`
- On claim: card collapses with a Clearance Green `CLAIMED` label + "moved to Pipeline as Prospect"; assigns to current RM.
- **Import control (top-right, ghost):** `Import funding CSV` → modal with drag-drop; on success shows count ingested + GWP surfaced.

---

## 4. Pipeline

Kanban-adjacent but disciplined — columns are tonal surfaces, cards float.

- Columns: `Prospect · Analysed · Quoted · Converted · Lost`.
- Column header: stage label + count + summed GWP range (flat).
- Cards: company, bundle, GWP range, RM avatar/initials, days-in-stage.
- Drag to move stage → writes a `pipeline_event`. Reduced-motion: replace drag with a stage dropdown.
- A `Lost` move asks for a one-tap reason chip (price / timing / competitor / no-need).

---

## 5. F4 — Renewals (Alerts)

A prioritised alert queue, not a notification dump.

- **Sort:** by delta-GWP descending (money first — the SVP's instinct).
- **Alert card (content card):** typed badge (renewal / upsell / at-risk / coverage-gap), company, one-line reason (e.g. *"Crossed 3,500 employees — Employment Practices now indicated"*), and the **delta GWP range** in Space Grotesk, pinned right.
  - `at_risk` badge uses Caution Amber + warning icon (paired, never color alone).
  - `upsell` / `renewal` use Reference Blue.
- Actions: `Review account →` (ghost), `Dismiss` (text button → sets alert dismissed).
- **Top summary tile:** total GWP-at-risk from renewals due ≤ 60 days (flat tile, amber-labelled).

---

## 6. F2 — Performance (RM Intelligence)

Management view. Dense where density earns trust.

1. **Leaderboard table (flat reference data):** RM · Analysed · Quoted · Proposals · Converted · Pipeline GWP. Sortable headers. Conversion rate column with a tiny inline bar (Ink Ghost track, Signal Red fill capped at 10% coverage).
2. **Sector conversion map:** horizontal labelled bars per sector (quoted vs converted). Bars flat; labels mandatory.
3. **Speed metric tiles:** median Signal→Analysis, Analysis→Quote, Quote→Proposal (flat tiles).
4. **Weekly digest preview card (content card):** the generated summary the SVP receives, with `Send digest` (ghost) reusing the outreach pipeline.

---

## 7. F3 — Proposal generation (action + artifact)

Not a screen — an action available from any analysed account (Pipeline card, Top-lead card, or the existing results view).

- **Trigger:** `Generate proposal` button (Signal Red, the decision) → inline progress (`Generating… < 10s`).
- **Result modal:** PDF preview thumbnail + `Download PDF` + `Attach to email` (hands off to existing Outreach flow).
- **The PDF itself** (themed to DESIGN.md, printed-document feel):
  - Masthead: ICICI Lombard mark + SPARC wordmark; Signal Red rule line.
  - Company block: name, sector, stage, city, date.
  - Recommended bundle + fit %; cover-level table (cover · why it fires · indicative range).
  - Total indicative GWP **range** in Space Grotesk.
  - Regulatory triggers section (IRDAI/RBI/DPDP/DGCA citations) — the credibility layer, retained.
  - RM contact block (from `contacts.json`).
  - QR code (links back to the SPARC analysis).
  - Footer disclaimer, verbatim: *"Indicative only under IRDAI File-and-Use detariffed regime. Not a bindable quote. Valid 30 days, subject to underwriting confirmation."*

---

## 8. Components added (reuse-first)
| Component | Base | New behaviour |
|---|---|---|
| Mode switch (topbar) | segmented control (DESIGN §Section nav) | toggles Analyse / Commerce |
| GWP range pill | Title type + Space Grotesk | renders `₹low–high` with auto L/Cr formatting |
| Funnel tile | flat data tile | count + GWP range + leak flag |
| Lead card | `.r-card` | source meta + claim action |
| Alert card | `.r-card` | typed badge + delta GWP |
| Proposal modal | existing modal | PDF preview + attach-to-email |

No new color tokens. No new font. No new radius. All within DESIGN.md.

---

## 9. Money formatting rule
- < ₹1 Cr → show in ₹ Lakh (`₹28L`).
- ≥ ₹1 Cr → show in ₹ Cr to one decimal (`₹1.4 Cr`).
- Ranges always `low–high` with a single unit (`₹28–45 L`, `₹87–142 Cr`).
- Never a single point estimate anywhere in the UI.

## 10. Accessibility & motion
- Status never by color alone — every green/amber/blue paired with label/icon.
- All animation `transform`/`opacity`; `prefers-reduced-motion` fallback (drag→dropdown, pulse→static).
- Tables keyboard-navigable; sort headers are buttons.
