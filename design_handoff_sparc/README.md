# Handoff: SPARC — Startup Insurance Risk Engine

> Three-persona front-end for ICICI Lombard's startup-protection product. One backend, three distinct UIs (RM, Underwriter, Founder).

---

## About these files

The HTML / CSS / JSX in this bundle are **design references**, not production code. They are high-fidelity, working prototypes built with React + Babel runtime to demonstrate the intended look, behaviour, and information architecture across the three persona views.

**Your task is to recreate these designs inside the SPARC codebase's existing front-end environment.** If the codebase already has an established framework (likely React, given the prototypes), use it and its established component patterns. If no front-end exists yet, pick the best fit for the team (React + Vite + Tailwind is a sensible default). Do **not** ship the prototype HTML directly — the runtime React loader, inline JSX, and ad-hoc CSS are not production-ready.

The prototypes do already call `POST /api/analyze` indirectly: in this bundle, `data.js → window.runAnalysis(profile)` is the local deterministic stand-in that emits the same shape as your real API. In production, swap that for a fetch to `/api/analyze` and consume the response keys listed in the brief (`overall`, `bundle_match`, `scores`, `pricing_engine_quote`, `outreach_prompts`, `v2_insights`, etc.).

---

## Fidelity

**High-fidelity.** Final colors, typography, spacing, layout, and interactive states are all decisions — not placeholders. Recreate pixel-close to the prototypes using the codebase's existing component primitives. Where the codebase has stronger components than the prototype (e.g. a real Select with a portal, a Toast system, a Form library), prefer them over a mechanical port.

---

## File map

```
design_handoff_sparc/
├── README.md                       — this file
├── index.html                      — Persona selector landing
├── rm-workspace.html               — RM workspace (intake → results)
├── underwriter-workbench.html      — UW 3-pane workbench
├── founder-view.html               — Founder 5-question intake + 3-screen result
├── styles.css                      — Single shared stylesheet (all 4 views)
├── data.js                         — Risk engine + seed companies + bundles + helpers
├── uw-data.js                      — UW queue, comparables, loadings, reg-rule refs
├── rm-app.jsx                      — RM root component (state, flow, tweaks)
├── rm-intake.jsx                   — RM intake screen
├── rm-results.jsx                  — RM results screen (verdict bar + pitch + email + drawers)
├── uw-app.jsx                      — UW root (queue + top bar)
├── uw-case.jsx                     — UW case workspace (6 spec'd panels + decision pane)
├── founder-app.jsx                 — Founder 3-stage flow (intake → loading → result-1/2/3)
└── tweaks-panel.jsx                — Prototype-only tweak harness; can be dropped in production
```

---

## Design tokens

The full set sits at the top of `styles.css` as CSS custom properties. Mirror them as Tailwind theme tokens / Style Dictionary tokens / SCSS vars depending on stack.

### Colors (per ICICI Lombard brand spec)

| Token              | Hex        | Usage |
|--------------------|------------|-------|
| `--brand`          | `#8C2424`  | Deep burgundy. Brand identity: logo block, brand mark, hero emphasis text ("Three jobs to do"), section letter accents (A · B · C), eyebrow text, brand-block backgrounds (founder CTA card), bundle-recommendation highlight in verdict bar. |
| `--brand-2`        | `#6F1C1C`  | Burgundy hover/pressed. |
| `--brand-soft`     | `#F5E3E3`  | Burgundy tints (risk icon backgrounds on founder view). |
| `--accent`         | `#E26A37`  | Orange/coral. **Primary CTAs**, hover states, active chip/option states, form-field focus rings, progress bar fills, "Generate pitch" / "Send email" / "Approve & quote" / "Talk to ICICI Lombard". |
| `--accent-2`       | `#C75620`  | Accent hover/pressed. |
| `--accent-soft`    | `#FBE5D7`  | Focus-ring glow, soft-amber chip backgrounds. |
| `--secondary`      | `#19385A`  | Deep blue. Secondary buttons, info-status borders, regulatory-rule reference cards in UW. |
| `--secondary-2`    | `#102740`  | Secondary hover. |
| `--secondary-soft` | `#D9E2EE`  | Secondary tints. |
| `--bg`             | `#F9F9F9`  | Page background (warm off-white). |
| `--bg-2`           | `#F1F1EE`  | Inset / queue / topbar background. |
| `--surface`        | `#FFFFFF`  | Cards, inputs, drawers. |
| `--surface-2`      | `#F4F4F1`  | Subtle surface (table heads, hovered rows). |
| `--ink`            | `#333333`  | Body text (12.6:1 on `--bg`, WCAG AAA). |
| `--ink-2`          | `#5C5C5C`  | Secondary text. |
| `--ink-3`          | `#8A8A8A`  | Muted text, hints, meta. |
| `--border`         | `#E5E5E0`  | Default borders. |
| `--border-strong`  | `#D0D0CB`  | Hover / stronger separators. |
| `--green`          | `#2F8F5B`  | Status: pass / clean / discount. |
| `--amber`          | `#C77A1C`  | Status: warning / loading. |
| `--red`            | `#8C2424`  | Status: high-severity (same as `--brand`). |

**Contrast audit (WCAG AA target):**
- `--ink` on `--bg`: **12.6:1** ✓ AAA
- `--brand` on white: **7.9:1** ✓ AAA
- White on `--brand`: **7.9:1** ✓ AAA
- White on `--accent`: **3.4:1** — only used on large/bold button text (passes AA Large).

### Typography

```css
--font-display: 'Space Grotesk', 'Inter', system-ui, sans-serif;
--font-body:    'DM Sans', system-ui, sans-serif;
--font-mono:    'JetBrains Mono', ui-monospace, 'SF Mono', monospace;
```

- **Display (Space Grotesk 700, tracking `-0.02em`)** — all hero / section / company / number-stat headings. List of selectors that take `--font-display` is enumerated at the top of `styles.css` (search `font-family: var(--font-display)`).
- **Body (DM Sans 400 / 500 / 600)** — everything else.
- **Mono (JetBrains Mono 400 / 500)** — case IDs, prices, SLAs, raw numbers in tables, kbd hints, monospace status pills. `font-variant-numeric: tabular-nums` applied site-wide.

Type scale (px):

| Use                          | Size | Weight | Tracking  |
|------------------------------|------|--------|-----------|
| Landing hero                 | 64   | 700    | -0.035em  |
| Founder H1                   | 52   | 700    | -0.03em   |
| RM intake H1                 | 52   | 700    | -0.03em   |
| RM result company name       | 22   | 700    | -0.01em   |
| UW case company              | 38   | 700    | -0.02em   |
| Section title                | 20–22| 700    | -0.01em   |
| Body                         | 14   | 400    | 0         |
| Founder body                 | 17   | 400    | 0         |
| UW table cell                | 12.5 | 400    | 0         |
| Meta / eyebrow / label       | 10–11| 600    | 0.14–0.20em uppercase |
| Mono numbers                 | 11–14| 500    | 0.02em    |

### Spacing & radii

- 8-pt grid. Page padding 56px (RM/landing), 32px (UW for density), 64px (founder for breathing room).
- Border radius scale: `--r-sm: 4px`, `--r: 6px`, `--r-lg: 8px` (per brief).
- Shadows: minimal — one soft elevation `--shadow: 0 1px 0 rgba(15,23,42,0.04), 0 8px 24px -10px rgba(15,23,42,0.10)` for hover lifts only. No drop shadows on chrome.

### Density tokens (per persona)

```css
[data-persona="rm"]      { ... }   /* density ≈ 4/10, comfortable, generous whitespace */
[data-persona="uw"]      { --page-pad: 32px; }   /* ≈ 8/10, tabular, mono numbers */
[data-persona="founder"] { --page-pad: 64px; }   /* ≈ 2/10, large type */
```

Set `data-persona` on `<html>` so the right token block applies globally.

---

## Views

### 1. Landing — `index.html`

**Purpose**: persona selector. First screen any internal user sees.

**Layout**:
- Top header bar (24px vertical padding, 1px bottom border): brand block (32×32 burgundy square with white "SP", wordmark "SPARC" + uppercase subtitle "STARTUP PROTECTION & RISK CLASSIFICATION"). Right side: version / build meta separated by `|` dividers.
- Hero (max-width 760px): burgundy eyebrow "ICICI LOMBARD · INTERNAL TOOL" → 64px headline "One engine. / *Three jobs to do.*" (italic word in burgundy) → 18px slate lede.
- Persona triptych (3-column grid, 20px gap): each card is white surface, 1px border, 8px radius, 32px padding. Mono eyebrow ("01 · Sales"), 26px role name, burgundy uppercase tag, description, then a 3-row stats list (label/value), then a CTA row with arrow.
- Hover: card lifts (`translateY(-3px)`), border becomes `--accent`, soft accent halo appears top-right, arrow shifts right and turns orange.
- Footer: 1px top border, tiny meta strip.

**Components**: persona card × 3 (RM / Underwriter / Founder), each linking to its workspace.

### 2. RM Workspace — `rm-workspace.html`

**Purpose**: walk into a founder call with the bundle, the talking points, and the email already drafted.

**Two phases**: `intake` → (1.3s loading) → `results`.

#### Intake (`rm-intake.jsx`)
- Sticky top bar with brand block + "RM workspace · New analysis" context + ghost links (Last 30 days / My pipeline / Templates).
- Single column, max-width 720px, generous whitespace.
- "Recent & suggested" chip row — 5 seeded companies, click to prefill the entire profile.
- "Or search a company" — typeahead input with `⌘K` hint; matches show in a dropdown row (name + sector·stage·team meta).
- After a company is selected, 4-up form grid appears (Sector / Stage segmented / Team / Revenue) plus a "Add if known:" chip strip for regulatory flags (RBI / SEBI / IRDAI regulated, Processes payments, Stores health data, Cross-border, DPDP fiduciary, AI in product).
- Primary CTA: orange "Generate pitch →" pill button (disabled until name + sector + stage + team are present). Hint text to the right.

#### Results (`rm-results.jsx`)
- **Verdict bar** (sticky, 18px padding, 1px bottom border): 3-column grid (left: back-arrow + company name 22px + meta; centre: pill-shape with 3 stats — Recommendation (burgundy bundle name), Annual band (mono numbers), Risk (number + tier label color-coded); right: "Hand to UW desk ↗" / Edit intake / Save to pipeline ghost links).
- **Block A — The pitch**: 3 talking-point lines, each in a white card with a 3px burgundy left border, mono "01 / 02 / 03" marker, then body copy at 16px. Header row has "Copy bullets" pill that copies all three to clipboard.
- **If they push back**: dashed-border card with 3-column grid of objection/response pairs. Italic question, dashed divider, response.
- **Block B — The message**: pre-drafted email in a white card. To / Subject metadata rows, dashed divider, then pre block of the body (or textarea when editing). "Edit" / "Copy" pill links in the header. Below: Send email (orange CTA) + Send via WhatsApp + Schedule for tomorrow 9 AM ghost links.
- **Block C — The proof**: 4 collapsible drawers (closed by default, only one open at a time):
  1. Why this bundle, not another — alternatives grid (chosen card highlighted with burgundy border, rejected cards with rejection reason).
  2. Full risk profile — heatmap (responsive grid of cells, opacity-graded burgundy background per score tier, score + label + short mono code).
  3. Cover-by-cover pricing — table (cover / SI / premium with mandatory/optional dot markers, subtotal / discount / GST / final rows).
  4. Hand off to underwriter — 2-col grid of UW status rows (clean / warn / info color-coded left borders), "Send to UW desk" action.

#### Loading screen
- Vertically centred mark (spinner SVG, burgundy), 36px Space Grotesk title "Analysing [Company]", uppercase mono sub "SPARC underwriting protocol · v2026.05", 4-row step list animating from `dot` → `done`.

### 3. Underwriter Workbench — `underwriter-workbench.html`

**Purpose**: triage queue, validate every assumption, price each cover, sign off with a documented decision trail.

**Layout**: 3-pane app shell. Top bar + queue (left, 280px) + case workspace (centre, flex) + decision pane (right, 340px sticky).

#### Top bar (56px height)
- Brand block (smaller variant) + wordmark "SPARC / UNDERWRITING WORKBENCH" + divider + 3 mono stats ("5 pending", "2 high priority", "62% capacity").
- Right: search input (`/` kbd hint) + "RM view ↗" ghost link + user chip (burgundy avatar circle + name + "UW-07" id in mono).

#### Queue (`uw-app.jsx`)
- "Queue" 22px display heading + count badge.
- Filter pills: All / High / Mine (active = dark ink).
- Vertically stacked case rows. Each row:
  - Top row: mono case ID (`SPARC-2401`) + SLA pill (semantic colors — green/amber/red, pulses when critical).
  - Company name (14px medium), bundle (11.5px muted), meta strip (mono amount, RM initials chip, submitted-ago time).
  - Active row has 2px orange left border + lifted background.
- Footer: 2 KPI rows ("Today's resolved", "SLA at risk").

#### Case workspace (`uw-case.jsx`)
Six spec'd panels + one supplemental, each scroll-anchored. A horizontal panel-jump nav sits above the body (`A · Risk · B · Assumptions · C · Pre-flight · …`).

1. **A. Risk score** — 13-cell grid (3+ columns responsive). Each cell shows risk name + tier-colored mono score, then 1–3 "signal" rows (mono uppercase label / sentence detail) that drove the score. Hover adds a left burgundy bar.
2. **B. Pricing assumptions** — table: Input / Value used (mono) / Source (color-dotted pill — `User-supplied` green / `Estimated` amber / `Inferred` amber / `Default` grey).
3. **C. Underwriter checks** — flat list of pre-flight items (Sanctions, KYC, Sector aggregate, Retro date, Prior claims, Senior referral). Each has a semantic pin dot + label + note + status pill + optional "Resolve" action button.
4. **D. Regulatory triggers** — 3-column row per trigger: severity pill (high = burgundy, med = amber, low = blue) / title + finding + action with dashed-divider "Action" sub-row / rule reference card (blue-left-border box: rule name + mono section reference + brief).
5. **E. Cover-level pricing** — editable table: dot + cover name (+ optional tag) / number-input SI / mono ROL (base rate) / number-input UW loading % / computed mono premium / row exclude × button. Below: two columns of toggle chips for Loadings (amber-tinted when on) and Discounts (green-tinted when on).
6. **F. Inputs required for firm quote** — list, each row: Critical / Optional tag pill + label + reason + "Request" action button.
7. **G. Context (supplemental)** — sector aggregate bar (showing before/after this case vs cap, color-segmented) + comparable cases table.

#### Decision pane (sticky right, 340px)
- Live premium block: "Live premium" eyebrow → ₹ currency + 44px Space Grotesk number + "L / year" unit → mono "vs RM indicative" row with ▲/▼ delta percentage (amber up, green down).
- Breakdown table: subtotal / net adjustment (colored by sign) / GST / final payable.
- 2×2 meta grid: Validity / Commission / Authority / SI total.
- Audit note: required textarea (12-char minimum), live char counter (red until met, green when met).
- 4 stacked decision buttons: Approve & quote (orange CTA, `⌘ ↵` kbd), Modify & approve / Refer to senior / Decline (white, decline turns red on hover).
- Foot: notification preview + warnings ("Clear all pre-flight checks before approving").

### 4. Founder View — `founder-view.html`

**Purpose**: a founder, alone with a laptop, understands their risk and what to do about it in plain English.

**3 stages**: `intake` → 1.1s loading → 3 sequential result screens.

#### Top bar
- Minimal: `← All views` link / centered SP+SPARC brand / "Quick check" or "n of 3" step marker.

#### Intake (`founder-app.jsx → Intake`)
- 17px base font, 64px page padding, max-width 720px.
- Burgundy eyebrow → 52px headline "Let's see what protection you actually need." → 19px lede ("No jargon. No upsell. Just an honest read on your top three risks and a rough sense of cost.").
- 5 fields, each in a `FdField` row with mono burgundy number ("01") + 22px label + control + optional hint:
  1. Free-text "What does your company do?" with full-width 16px input
  2. Number "How many people on the team?" — mono number input
  3. "What stage are you at?" — pill segmented (Pre-seed / Seed / Series A / Series B+), active = orange-filled
  4. "Do you handle customer payments or personal data?" — Yes / Not really pill pair
  5. "Are you regulated?" — Yes / No pill pair
- Submit: orange CTA "See my risk profile →" (disabled until all 5 are answered). Trust note below.

#### Result 1 — Your risks
- "Step 1 of 3 · Your risks" eyebrow → 52px headline "Here's what we noticed." → personalised lede mentioning their sector + stage + team.
- 3 risk cards, each a 3-column row: mono number (hidden on mobile) / round burgundy-soft icon disc with line-art glyph / body with 24px headline (plain English: "Your data is a target") + 16px sentence.
- Bottom nav: progress dots (active dot stretches to a 20px pill) + orange "What can I do about it? →" CTA.

#### Result 2 — What you need
- Eyebrow → 52px concept headline (e.g. "Liability protection for digital-first teams") → lede describing the bundle as a *protection concept*, not a product name.
- 3 benefit rows, each with an orange round check disc + 19px name ("If your data is breached") + 15px description.
- Nav: ← Back / progress dots / orange "What does it cost? →".

#### Result 3 — Cost + next step
- Eyebrow → 52px "A rough estimate, not a quote." → lede.
- Cost card (white surface, centred): "Indicative annual premium" eyebrow → ₹ low – ₹ high (48px Space Grotesk numbers) → "Lakhs per year, all-inclusive" → confidence bar (track with band fill + mid marker) → 3-label scale ("Lean cover / Typical fit / Comprehensive") → small note explaining why a range.
- **Burgundy CTA card** ("Want a real number?"): 28px white headline + supporting copy + white "Talk to ICICI Lombard →" button (white fill, burgundy text, hover flips to orange fill / white text). Below: secondary "Email me the summary" underlined link.
- Final nav: ← Back / progress dots / spacer.

**Critical content rules**:
- Never show a precise quote number — always a range with a confidence band.
- Never use technical cover keys (`cyber_liability`, etc.) — translation table in `founder-app.jsx → RISK_PLAIN` and `BUNDLE_CONCEPT`.
- No scores, no ROL bands, no UW flags, no policy wording.

---

## API contract

Each persona view consumes the same backend response. In the prototype this is mocked in-browser via `data.js → window.runAnalysis(profile)`. In production:

```ts
POST /api/analyze
Request:  StartupProfile
Response: AnalyzeResult {
  overall: number;                           // 0–100
  tier: "Low" | "Moderate" | "High";
  scores: Record<RiskKey, number>;           // 13 dimensions
  bundle_match: {
    id: string;
    name: string;
    tagline: string;
    mandatory_covers: CoverKey[];
    optional_covers: CoverKey[];
    rationale: string;                       // human-readable
  };
  bundle_alternatives: Array<{               // near-miss bundles
    ...bundle;
    rejectReason: string;
  }>;
  recommendations: Array<{ key, name, priority, score, why }>;
  pricing_engine_quote: {
    covers_priced: Array<{ key, label, si, premium, mandatory }>;
    gross_premium_lakh: number;
    net_premium_lakh: number;
    gst_lakh: number;
    total_payable_lakh: number;
  };
  outreach_prompts: { subject: string; body: string };
  genai_adjustment: { changed: bool; from_bundle?: string; to_bundle?: string; reason?: string };
  v2_insights: {
    risk_clusters: string[];
    triggers: Array<{ key, severity, ruleKey, title, finding, action }>;
    mitigations: string[];
  };
}
```

The `scores`, `triggers`, `assumptions`, `inputs_required` helpers in `data.js` / `uw-data.js` give a working shape — your real engine should drive them.

**Persona-specific filtering** happens client-side: each view picks the fields it cares about and ignores the rest. The RM view never renders `scores` directly; the UW view never renders `outreach_prompts`; the Founder view never renders ROL or cover keys.

---

## Interactions & behaviour

### Cross-view navigation
- Persona selector → each persona view. Each view has a back link to `index.html` in its top bar.
- RM verdict bar → "Hand to UW desk ↗" deep-links to the UW workbench (production: scoped to the current case ID).
- UW top bar → "RM view ↗" navigates back to the RM workspace.

### Transitions
- Loading: 1.1s for founder, 1.3s for RM. Show a spinner + step list (animates step-by-step every 280ms). No skeleton states.
- Drawer open/close (RM proof drawers): 220ms ease-out, chevron rotates 90° on open.
- Hover lifts on cards: `translateY(-1px)` to `(-3px)`, 180ms cubic-bezier.
- Active filter chips and segmented controls: instant background swap, 150ms color transition.

### State
Each persona view holds its own local state — the prototype uses `useState` in the root component:
- **RM**: `stage` (`intake` | `loading` | `results`), `profile` (form state), `result` (AnalyzeResult).
- **UW**: `queue` (case list), `activeId` (selected), `caseEdits` per case (lines, loadings, discounts, audit note, check overrides).
- **Founder**: `stage` (`intake` | `loading` | `result-1|2|3`), `intake` (5-field form), `result`.

In production, lift to your global store / URL params as appropriate. Case IDs and persona route should be in the URL.

### Form validation
- RM intake: `canAnalyze = name && sector && stage && team`. CTA is disabled at 35% opacity until all 4 are present.
- UW: `canApprove = allChecksCleared && auditNote.length >= 12`. Other decisions only require an audit note.
- Founder: all 5 fields required, no other validation.

### Tweaks panel
`tweaks-panel.jsx` is a prototype-only design tool — drop it from production. The `__edit_mode_*` postMessage protocol it implements is specific to this design environment.

---

## Component inventory

| Component        | Used in                       | Purpose |
|------------------|-------------------------------|---------|
| `<TopBar>`       | RM, UW, Founder, Landing      | Per-persona header with brand + context + actions. |
| `<RecentChip>`   | RM intake                     | One-click company prefill chip. |
| `<Typeahead>`    | RM intake                     | Company-name search with dropdown. |
| `<FdField>`      | Founder intake                | Numbered field row with label + control + hint. |
| `<Segmented>`    | RM intake, Founder            | Pill-segmented option control. |
| `<NumberInput>`  | RM intake, UW pricing         | Number input with suffix. |
| `<Drawer>`       | RM results                    | Collapsible proof section. |
| `<RiskHeatmap>`  | RM results                    | Opacity-graded grid of 13 risk cells. |
| `<RiskGrid>`     | UW                            | Dense 13-cell grid with signals. |
| `<AssumptionsTable>` | UW                        | Three-column input/value/source table. |
| `<CheckRow>`     | UW                            | Pre-flight check row with status pill + resolve. |
| `<TriggersTable>`| UW                            | Reg trigger with rule-reference card. |
| `<InputsList>`   | UW                            | Critical/optional input request rows. |
| `<DecisionPane>` | UW                            | Sticky right pane with live premium + audit + 4 decisions. |
| `<ScoreArc>`     | RM results (alt)              | Semi-circle gauge for overall risk. |
| `<RiskIcon>`     | Founder result-1              | Inline line-art SVG icon set (lock / scale / doc / shield / etc.) |

---

## Assets

- **Fonts**: Google Fonts — Space Grotesk (display), DM Sans (body), JetBrains Mono (data). Already linked in every HTML file's `<head>`.
- **Icons**: inline SVG only. No icon font, no external library. Founder risk icons are stroked line art (1.7 stroke-width, rounded caps) in a swatch of about 12 glyphs — see `founder-app.jsx → RiskIcon`.
- **Logo**: prototype uses a generic "SP" monogram in a burgundy square. In production, use the real ICICI Lombard wordmark and the SPARC sub-brand (whatever the brand team provides).

---

## Implementation notes for Claude Code

1. **Don't ship the prototype HTML.** Re-implement in the SPARC codebase's existing React/Vue/whatever environment using its component library. The HTML here is faster to read than a spec doc but is not production-grade.
2. **Move `runAnalysis` to the server.** It's in `data.js` as a deterministic stand-in. Replace every call site with a `fetch('/api/analyze', ...)` (or your data-fetching library of choice — TanStack Query, SWR, RTK Query).
3. **Persist UW state.** The UW edits (per-line SI/loading, applied loadings/discounts, audit note, check overrides) should be saved per case to whatever backing store you use (server-side draft, or local optimistic store). A reload should not lose 10 minutes of UW pricing work.
4. **Mobile.** The prototypes are responsive but optimised for desktop (the UW workbench in particular). Founder view should look great on phones — that's its primary surface in real life. The other two are desktop-first.
5. **Accessibility.** All interactive elements are real `<button>` and `<a>` tags in the prototype. Keep that in production. Tab order is sensible top-to-bottom in each view. The UW pricing-builder number inputs need `aria-label`s in production (the visual label is the column header).
6. **Tokens, not values.** Map every `var(--xxx)` to your design-token system. Don't hardcode hex values in components.
7. **Three personas, one repo.** Route prefix: `/rm`, `/uw`, `/founder` (or whatever your routing convention is). The `data-persona` attribute on `<html>` drives the density variant — keep that mechanism or replicate it with a layout prop.

If anything in this README contradicts the prototype, **the prototype is the source of truth** — re-read the HTML/JSX. The README is for orientation, not exhaustive spec.
