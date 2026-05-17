---
timestamp: 2026-05-17T05-21-44Z
slug: startup-shield-web-index-html
---
## Design Health Score

| # | Heuristic | Score | Key Issue |
|---|-----------|-------|-----------|
| 1 | Visibility of System Status | 3 | Step sidebar and analyse-ready pulse are good; no explicit progress bar during long API call |
| 2 | Match System / Real World | 3 | Insurance terminology matches RM domain; methodology panel dense for founders |
| 3 | User Control and Freedom | 2 | "Edit inputs" back button exists; no per-parameter adjustment without full re-run |
| 4 | Consistency and Standards | 3 | Token system is highly consistent; customer flow uses side-stripe borders that RM flow doesn't |
| 5 | Error Prevention | 2 | Categorical chips prevent invalid input; free-text fields have no format hints or inline validation |
| 6 | Recognition Rather Than Recall | 3 | All tabs labeled; step sidebar visible; risk category meaning requires methodology expand |
| 7 | Flexibility and Efficiency | 1 | No keyboard shortcuts; no session save; no compare-two-startups; only power feature is company profile import |
| 8 | Aesthetic and Minimalist Design | 3 | Progressive disclosure (summary → tabs → methodology) is well-executed; 13 identical risk cards are monotonous |
| 9 | Error Recovery | 2 | Generic "Failed to fetch" with no actionable guidance; no form state preservation on network error |
| 10 | Help and Documentation | 2 | Methodology expand is elegant documentation-in-place; no inline tooltips on score categories |
| **Total** | | **24/40** | **Acceptable — significant improvements available** |

## Anti-Patterns Verdict

**Does this look AI-generated?** Not obviously — and that is a genuine achievement. The Signal Red palette is restrained and specific (ICICI Lombard brand color, not generic purple or teal). The typography pairing (Space Grotesk + DM Sans) is overused industry-wide (flagged by detector: `overused-font` warning) but used with enough discipline that it reads intentional rather than default. The methodology reveal button is a genuinely custom component with no AI-template parallel.

**What keeps it from being fully distinctive:**
1. The `border-left` side-stripe pattern appears on 12+ elements across the codebase. Impeccable's absolute ban on this pattern exists precisely because it is the most common SaaS/dashboard cliché. When the action banner, bundle cards, product priority cards, and RM referral banner all use the same 3-4px red left border as their primary differentiator, the interface signals "AI-assembled components" even though the individual tokens are carefully chosen.
2. The 13 risk score cards are structurally identical (badge + category name + score number + supporting text, repeated in a uniform grid). Visually distinct due to different numbers, but the grid composition reads as a default AI-generated card array.

**Deterministic scan:** 9 findings — all `overused-font` severity `warning`. The `font-family:Arial` hits are in the radar chart SVG (app.js lines 3656–3757), which renders chart axis labels outside the CSS token system. Space Grotesk flagged in index.html line 0. No errors, no critical violations from the automated detector.

## Overall Impression

The foundation is right: the design system is specific, restrained, and non-generic. The PRODUCT.md principles (Show the math, Trust through specificity, Speed to credibility) are actually expressed in the UI rather than ignored. The single biggest opportunity is eliminating the side-stripe border pattern — it appears 12+ times and is the most visible signal that components were assembled rather than designed. Fix that, differentiate the risk score grid by severity, and this interface reads as genuinely expert rather than competent.

## What's Working

1. **The Methodology Reveal button** — dark gradient pill that shifts to red on expand is the interface's most distinctive moment. The color state change signals "you are now in expert mode" in a way no tooltip or label could. This is the design's personality.

2. **Section nav segmented control** — the tray with white-card active state (not filled-red pill) is subtly correct. The active tab is marked by white elevation and red text, not by flooding the tab with color. This is restrained in exactly the way PRODUCT.md prescribes.

3. **Dark results hero (`.customer-results-hero`, `#151923`)** — the black command surface for the final recommendation creates an instant authority signal. The RM opens the results and sees a dark, confident panel with the bundle name in large white type. This is the "Risk War Room" north star made visible.

## Priority Issues

**[P1] Side-stripe border pattern — 12+ violations across styles.css and app.js**
- **What**: `border-left: 3-4px solid var(--red/--amber/--border)` used as the primary status signal on `.customer-bundle-card` (line 449), `.customer-bundle-why` (line 490), `.customer-rm-banner` (line 590), `.action-banner` (line 2102), `.product-card.critical` (line 2400), `.product-card.recommended` (line 2404), `.product-row.critical` (line 3047), `.product-row.recommended` (line 3048), and more.
- **Why it matters**: Impeccable's absolute ban exists because this pattern is the #1 SaaS dashboard cliché. It signals "assembled from components" regardless of how good the surrounding tokens are. In a tool that positions itself as intelligent and clinical, the side-stripe reads as lazy shorthand.
- **Fix**: Replace with (a) full-border + tint background (already done correctly on `.sidebar-step.active` — use that pattern), (b) a colored leading badge/number/icon, or (c) a background tint alone. The `.action-banner` should become a full-border red-tint callout. Product priority cards should use a colored rank badge rather than a border stripe.
- **Suggested command**: `/impeccable harden startup_shield_web/styles.css`

**[P1] 13 identical risk score cards in a uniform grid**
- **What**: The Risk Scores tab renders all 13 categories as structurally identical 4-column cards. Score badges differ numerically but the layout pattern is identical for every card.
- **Why it matters**: The RM in a live meeting needs to immediately see WHAT IS CRITICAL vs. what is fine. A uniform grid puts a 9.2/10 cyber risk card and a 2.1/10 IP risk card in identical visual containers. The grid doesn't communicate priority.
- **Fix**: Group cards by severity tier (Critical ≥8, High 6–7.9, Moderate 3–5.9, Low <3). Show Critical cards in a featured band at the top (larger, red-tinted, 2-column or 1-column). Show High cards in a reduced grid. Collapse Moderate and Low into a summary row by default.
- **Suggested command**: `/impeccable layout startup_shield_web/app.js`

**[P2] Glassmorphism on sidebar cards throughout intake and results**
- **What**: `.sidebar-card` uses `background: var(--glass-bg); backdrop-filter: blur(14px)` — this is the glass treatment reserved per DESIGN.md for the role-selection landing screen and topbar. The sidebar card is visible throughout the entire RM workflow, making glassmorphism a default rather than a deliberate choice.
- **Why it matters**: "Glassmorphism as default" is an impeccable absolute ban. Applied to every sidebar card, it reads as a generic SaaS aesthetic choice rather than a meaningful "looking through glass" treatment.
- **Fix**: Change `.sidebar-card` to `background: var(--white); border: 1px solid var(--border); box-shadow: var(--shadow);`. Reserve the glass treatment for `.role-card` and `.step-sidebar` (the role-selection landing screen) only.
- **Suggested command**: `/impeccable distill startup_shield_web/styles.css`

**[P2] Arial font in radar chart SVG breaks the typographic system**
- **What**: The radar chart renders all axis labels and legend text with `font-family:Arial` (app.js lines 3656, 3683, 3706, 3715, 3722, 3730, 3737, 3746, 3757). Arial is the system fallback, not the DM Sans brand font.
- **Why it matters**: The Risk Scores tab is the most data-dense view. The radar chart is a key visualization. Arial text in the chart creates a visible typographic break — it looks like a placeholder rather than a finished product.
- **Fix**: Replace `font-family:Arial` with `font-family:'DM Sans',system-ui,sans-serif` in all SVG text generation (app.js lines 3656–3757).
- **Suggested command**: Fix directly in app.js.

**[P2] No inline progress feedback during API analysis**
- **What**: When the RM clicks "Analyse Risk Profile," the tool makes an async POST to `/api/analyze`. The current loading state is a text message only; no progress bar, no step counter, no estimated time.
- **Why it matters**: In a live sales meeting, 5–15 seconds of silent loading is anxiety-inducing for both the RM and the founder. The RM loses control of the room.
- **Fix**: Add a stepped progress indicator during analysis: "Scoring regulatory exposure... (3/13)", "Calculating premium estimate...", "Building outreach brief...". This can be simulated with a deterministic timer sequence since the API is a black box from the frontend's perspective.
- **Suggested command**: `/impeccable onboard startup_shield_web/app.js`

## Persona Red Flags

**Shrijeet, the RM (primary user — under time pressure in a live meeting):**
- The 5-tab results view requires the RM to mentally map which tab holds the CFO pricing sheet vs. the risk rationale. The tabs are labeled but there's no visible preview of what each tab holds until you click it.
- After seeing results, adjusting one parameter (e.g., updating employee count) requires clicking "← Edit inputs", re-navigating the 3-step form, and re-running the full analysis. In a 30-minute meeting, this is a full context-switch. The RM loses the room.
- The methodology expand requires the RM to scroll to find the button (it's at the bottom of the Risk Scores tab). If the founder challenges a score in the meeting, the RM must navigate: click Risk Scores tab → scroll to bottom → click methodology button → scroll back up to the challenged section.

**Startup Founder (secondary user — self-serve validation):**
- Category names like "Directors & Officers Liability" and "Marine/Cargo" appear without inline explanation. A 15-person fintech founder may not know what D&O covers or why SPARC thinks it's relevant to them.
- The pricing figure on the results hero is a range ("₹2.4L – ₹3.8L/year"), not a single number. Founders need a bottom line for CFO sign-off; a range invites negotiation friction.
- The "customer" self-serve flow (founder-facing pages) has `border-left` side-stripes on bundle and RM referral cards that the RM flow doesn't. The flows look like they were designed by different people.

## Minor Observations

- `.pill:hover` changes the border color to `var(--red-glow)` (rgba value) rather than `var(--red)`. This creates a slightly muddy hover — the border lightens when it should sharpen. Should be `var(--red)` at reduced opacity for consistency with `.pill.active`.
- The topbar has no current-step context indicator. At step 2 of the intake, the topbar just shows "SPARC | Startup Shield" with no progress signal. Adding a minimal step indicator (e.g., "Step 2 of 3") to the topbar right side would help.
- The `@media print` and PDF export functionality (if it exists) hasn't been verified for typographic consistency — the pricing sheet the RM "leaves with" may render differently on paper.

## Questions to Consider

- What if the Risk Scores tab showed an "urgency stack" — the 3 most critical risks displayed prominently above the full grid, with explicit "Why this matters for [sector]" language pre-expanded?
- What if each results tab had a 1-line subtitle in the section nav itself? "Bundle — ₹3.1L/year" as the tab label instead of just "Bundle."
- What would it look like to make the "Adjust one parameter" flow a core feature — a persistent parameter chip strip at the top of results that lets the RM change funding stage or headcount in-place?
