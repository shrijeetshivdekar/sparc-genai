---
name: SPARC | Startup Shield
description: ICICI Lombard's insurance risk analysis and bundle recommendation engine for startup sales meetings
colors:
  primary: "#AD1E23"
  primary-deep: "#8A1519"
  primary-mid: "#C9282E"
  ink: "#0F172A"
  ink-2: "#1E293B"
  ink-muted: "#64748B"
  ink-faint: "#94A3B8"
  ink-ghost: "#CBD5E1"
  bg: "#FAFAF8"
  surface: "#F1F1EE"
  surface-2: "#E8E8E4"
  border: "#E2E2DC"
  white: "#FFFFFF"
  status-green: "#059669"
  status-amber: "#D97706"
  status-blue: "#3B82F6"
typography:
  display:
    fontFamily: "'Space Grotesk', 'DM Sans', ui-sans-serif, system-ui, sans-serif"
    fontSize: "clamp(30px, 4vw, 52px)"
    fontWeight: 800
    lineHeight: 1.02
    letterSpacing: "-0.03em"
  headline:
    fontFamily: "'Space Grotesk', 'DM Sans', ui-sans-serif, system-ui, sans-serif"
    fontSize: "22px"
    fontWeight: 700
    lineHeight: 1.15
    letterSpacing: "-0.03em"
  title:
    fontFamily: "'Space Grotesk', 'DM Sans', ui-sans-serif, system-ui, sans-serif"
    fontSize: "17px"
    fontWeight: 700
    lineHeight: 1.25
    letterSpacing: "-0.02em"
  body:
    fontFamily: "'DM Sans', 'Inter', ui-sans-serif, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.7
    letterSpacing: "normal"
  label:
    fontFamily: "'DM Sans', ui-sans-serif, system-ui, sans-serif"
    fontSize: "11px"
    fontWeight: 800
    lineHeight: 1
    letterSpacing: "0.12em"
rounded:
  sm: "9px"
  md: "14px"
  lg: "20px"
  pill: "999px"
spacing:
  xs: "8px"
  sm: "14px"
  md: "24px"
  lg: "40px"
  xl: "80px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.white}"
    rounded: "{rounded.sm}"
    padding: "0 24px"
    height: "48px"
  button-primary-hover:
    backgroundColor: "{colors.primary-deep}"
  button-ghost:
    backgroundColor: "{colors.white}"
    textColor: "{colors.ink-muted}"
    rounded: "{rounded.sm}"
    padding: "0 24px"
    height: "48px"
  button-lg:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.white}"
    rounded: "{rounded.md}"
    padding: "0 32px"
    height: "56px"
  chip-default:
    backgroundColor: "{colors.white}"
    textColor: "{colors.ink-muted}"
    rounded: "{rounded.pill}"
    padding: "9px 15px"
  chip-active:
    backgroundColor: "#F5E7E7"
    textColor: "{colors.primary}"
    rounded: "{rounded.pill}"
    padding: "9px 15px"
  card:
    backgroundColor: "{colors.white}"
    rounded: "{rounded.md}"
    padding: "24px"
---

# Design System: SPARC | Startup Shield

## 1. Overview

**Creative North Star: "The Risk War Room"**

SPARC is not a dashboard — it is a command briefing. Every surface exists to make one person look like the most credible expert in the room within two minutes of opening the laptop. The RM does not browse SPARC; they deploy it. The interface should feel like classified intelligence prepared in advance and handed over at exactly the right moment.

The visual system is serious, fast, and unapologetically dense where density earns trust. Assessment Paper backgrounds with Underwriter's Ink type establish institutional authority without the sterility of a bank portal. The single accent — Signal Red, the same red as IRDAI enforcement notices — appears rarely and only to mark decisions, alerts, and the primary action. Its rarity is the point.

Motion is responsive, not choreographed. Components acknowledge interaction immediately and without fuss. The system never asks for the RM's attention; it responds to commands. When the RM expands the 21-step methodology, the interface shifts into expert mode: dark, sourced, unimpeachable.

This system explicitly rejects: generic SaaS admin aesthetics (Tailwind Admin card grids, teal accent, "Overview" headings), consumer fintech gradient blobs and rounded-everything phone-app energy, and legacy insurance portal density for its own sake.

**Key Characteristics:**
- Assessment Paper canvas (`#FAFAF8`) that reads as document, not app
- Signal Red used on ≤10% of any screen — reserved for decisions and critical risk flags
- Underwriter's Ink (`#0F172A`) as the dominant text color — deep, not pure black
- Space Grotesk for headings, tight tracking (-0.03em), heavy weights — authority through typography
- Content cards float with diffuse ambient shadow; data rows are flat on a tonal surface
- Physical press feedback (`scale(0.97)`) on every interactive element; nothing feels passive

## 2. Colors: The Enforcement Palette

A restrained palette centered on one high-stakes accent and an off-white document ground. Color is never the only signal for risk severity — every color is paired with a label or icon.

### Primary
- **Signal Red** (`#AD1E23`): The ICICI Lombard and IRDAI enforcement red. Primary CTA button, active nav states, risk flags, the brand mark, and checkbox accents. ≤10% of any screen. Its presence signals a decision point, never decoration.
- **Signal Red Deep** (`#8A1519`): Hover state for red elements only. Never used as a flat fill.
- **Signal Red Mid** (`#C9282E`): Used in hero button contexts at larger scale where `#AD1E23` reads too dark against white.

### Secondary
- **Clearance Green** (`#059669`): Coverage confirmed, risk resolved, within acceptable range. Always paired with a label.
- **Caution Amber** (`#D97706`): Moderate risk, partial coverage, attention needed.
- **Reference Blue** (`#3B82F6`): Informational metadata, regulatory references, non-critical links.

### Neutral
- **Underwriter's Ink** (`#0F172A`): Primary text and headlines. Deep near-black tinted toward slate — reads as premium, not harsh.
- **Board Navy** (`#1E293B`): Dark hero surfaces for the results banner and RM role card. Slightly lighter than Ink for readability at large type sizes.
- **Ink Muted** (`#64748B`): Secondary body copy, descriptive text, supporting labels.
- **Ink Faint** (`#94A3B8`): Placeholder text, disabled labels, tertiary metadata.
- **Ink Ghost** (`#CBD5E1`): Dividers and ghost button stroke borders.
- **Assessment Paper** (`#FAFAF8`): The page canvas. Barely-warm off-white — a document, not a screen. Never the inside of a card.
- **Document Surface** (`#F1F1EE`): Tonal lift above the canvas for sidebar steps, filter chips, and secondary content areas.
- **Surface 2** (`#E8E8E4`): Secondary tonal layer for nested groupings inside panels.
- **Assessment Border** (`#E2E2DC`): Structural dividers, card stroke borders, row separators.
- **Pure White** (`#FFFFFF`): Card fill only. Never the page background.

**The One Voice Rule.** Signal Red is used on ≤10% of any given screen. Its rarity is the point — it marks decisions, not decoration. When everything is red, nothing is urgent.

**The Status Pairing Rule.** Status colors (green, amber, blue) are never the only indicator of meaning. Always pair with a label or icon so the signal survives monochrome, color blindness, and printing.

## 3. Typography: The Briefing Hierarchy

**Display Font:** Space Grotesk (fallback: DM Sans, system sans)
**Body Font:** DM Sans (fallback: Inter, system sans)

**Character:** Space Grotesk carries institutional authority — tight tracking, heavy weights, the confidence of something typeset for a board presentation. DM Sans softens the reading experience for dense paragraphs without compromising credibility. Together they read like a forensic report written for a C-suite.

### Hierarchy
- **Display** (800 weight, `clamp(30px, 4vw, 52px)`, 1.02 line-height, -0.03em tracking): Results hero headlines and the landing page primary H1. Appears once per screen. Space Grotesk.
- **Headline** (700 weight, 22–30px, 1.08–1.15 line-height, -0.03em tracking): Section headers, card titles, modal headings. Space Grotesk throughout.
- **Title** (700 weight, 17–20px, 1.25 line-height, -0.02em tracking): Subsection labels, sidebar card labels, component group headings.
- **Body** (400–500 weight, 14–15px, 1.65–1.7 line-height): Explanatory text, bundle descriptions, methodology copy. Max line length 65–70ch.
- **Label** (800 weight, 10–13px, 1.0 line-height, 0.08–0.13em tracking, uppercase): Eyebrow kickers, section navigation pills, metadata tags, sidebar section markers. Always uppercase.

**The -0.03em Rule.** Every heading at Title size and above uses -0.03em letter-spacing. This single constraint creates visual cohesion across the entire interface and separates Space Grotesk from generic web typography. Tighter tracking at heavier weights; letter-spacing loosens only for label-size uppercase text where readability requires it.

## 4. Elevation

SPARC uses a mixed elevation model: content cards that carry recommendations and scores float visibly above the document surface; data rows, risk score breakdowns, and table entries are flat on a tonal background.

Depth communicates information importance, not interactivity. A KPI card always casts a diffuse shadow because it holds a decision-relevant number. A risk breakdown row in a methodology table is flat because it is reference data, not a choice.

### Shadow Vocabulary
- **Card ambient** (`0 1px 2px rgba(15,23,42,.04), 0 4px 12px rgba(15,23,42,.06), 0 12px 32px rgba(15,23,42,.05)`): Default shadow for content cards (KPI cards, bundle cards, role cards). Always visible at rest, before any interaction.
- **Card hover** (`0 2px 4px rgba(15,23,42,.04), 0 16px 48px rgba(15,23,42,.13), inset 0 1px 0 rgba(255,255,255,.9)`): Applied on pointer hover. Combined with `translateY(-3px)` lift. The top inset highlight strengthens the "card lifted off the table" reading.
- **Card inset** (`0 1px 1px rgba(15,23,42,.03), 0 4px 16px rgba(15,23,42,.07), inset 0 1px 0 rgba(255,255,255,.8)`): Sidebar cards and right-column panels. Slightly lighter with the same inset top highlight.
- **Red glow** (`0 2px 8px rgba(173,30,35,.3)`): The primary button shadow at rest — the only colored shadow in the system. Amplifies to `rgba(173,30,35,.4)` and spreads on hover.
- **Flat (none)**: Risk score rows, data table rows, sidebar step items, form field rows, and all reference data. Tonal separation via background color only.

**The Structural Shadow Rule.** Shadows exist to communicate information hierarchy, not to add visual interest. If removing a shadow doesn't change what a user understands about an element's importance, the shadow should not be there.

## 5. Components

### Buttons
Buttons feel immediate and deliberate. The press state (`scale(0.97)`) is applied to every button without exception — every click is physically acknowledged.

- **Shape:** Gently curved edges — 9px radius (standard), 14px (`.btn-lg`), `999px` (pill/eyebrow variants)
- **Primary:** Signal Red background, white text, 0 24px padding, 48px height. Red glow shadow. Darkens to `#8A1519` on hover with amplified glow. Scales to `0.97` on press.
- **Analyse-ready pulse:** When all intake fields are complete, the primary CTA gains a repeating red glow ring animation (`analysePulse`). The only ambient animation in the system — it marks readiness without alarm.
- **Ghost:** White fill, `#CBD5E1` border (1.5px), `#64748B` text. Border darkens to Ink Ghost, text shifts to Ink on hover. Same press scale.
- **Large:** 56px height, 14px radius, 32px horizontal padding. Used in results and hero contexts.
- **Hero ghost:** White text, transparent fill, white border at low opacity, on dark hero surfaces only.

### Chips / Pills
Used for role selection (sector, funding stage, employee count) and risk category filters.

- **Default:** White fill, `#E2E2DC` border at 1.5px, `#64748B` text, 999px radius, 9px 15px padding, 13px 700 weight.
- **Active:** `rgba(173,30,35,.07)` red-tint fill, Signal Red text, Signal Red border. The selection state is a hint of red, not a flood of it.
- **Eyebrow label:** Red tint fill, red text, low-opacity red border — pill shaped, 11px, 0.08em tracking, uppercase. Used to mark the current step or category above a heading.

### Cards / Containers
One rule: content cards float, reference data is flat.

- **Content card (`.r-card`, `.kpi-card`):** White fill, `#E2E2DC` border (1px), 14px radius, card-ambient shadow always on. Hover: `translateY(-3px)` lift + shadow intensification + red border tint. Padding 20–24px.
- **Dark card (results hero, RM role selector):** `#151923` fill, white type, 8–14px radius. The command surface — where the RM's identity and the final recommendation live.
- **Sidebar card:** Glassmorphism fill (`rgba(255,255,255,.72)` + `backdrop-filter: blur(14px)`). Sticky context panel in the right column. Glassmorphism is deliberate here: the sidebar is a secondary surface observed through the main content, not a primary surface the RM acts on.
- **Role selection card:** Same glassmorphism treatment on the landing screen's role-choice cards. The one other context where the "looking through glass" reading is intentional — the RM is choosing their seat, not yet inside the tool.
- **Form panel:** White fill, 8px radius, 1px border, lighter shadow. Below content cards in the hierarchy.

### Inputs / Fields
- **Style:** `#FAFAF8` fill, `#E2E2DC` border at 1–1.5px, 8–9px radius. Body font, 14px, Ink text.
- **Focus:** Signal Red border shift + `rgba(173,30,35,.07)` outer glow (3.5px spread). The focus state uses the same red system as selection — consistent language for "this is active."
- **Code textarea (profile import):** `#0F172A` fill, `#e2e8f0` monospace text. A deliberate dark-surface inset within the light page — signals "this is machine input, not human prose."
- **Checkbox accent:** `accent-color: #AD1E23` throughout. Red ticks.

### Navigation

**Top bar:** Fixed, 60px height, `rgba(250,250,248,.92)` frosted fill with `backdrop-filter: blur(12px)`, 1px bottom border. The brand mark is a 34×34px Signal Red square (9px radius) with "SP" in Space Grotesk 800. The topbar blur is purposeful: it signals the fixed layer without a hard opaque mask.

**Section nav (results tabs):** Segmented control tray. Tray: `#F1F1EE` fill, 12px radius, 4px inner padding. Pills: 34px height, 12px radius, `#64748B` Ink Muted text at rest. **Active pill:** white card within the tray, Signal Red text, subtle shadow — not a filled-red pill. The active state is calm: the selection is marked by white elevation and red text, not by flooding the tab with color.

**Sidebar steps:** Left-column sequential nav. Transparent at rest, `#F1F1EE` on hover. Active: red-tint fill, red border, red text. Done: green icon.

### Signature Component: Methodology Reveal

The "How was this calculated?" button is the most important trust component in the system. It sits at the bottom of the Risk Scores tab and collapses or expands 400+ lines of sourced actuarial reasoning.

At rest: dark gradient pill (`linear-gradient(135deg, #0F172A, #1E293B)`), white text, 🔬 icon, "▼ expand" tag. Hover: shadow lifts, cursor pointer. Expanded: shifts to red gradient (`linear-gradient(135deg, #B91C1C, #DC2626)`), text changes to "Hide methodology." This is the one interactive element in the system that changes its own color on toggle — because it marks the transition from summary view to expert mode.

## 6. Do's and Don'ts

### Do:
- **Do** use Signal Red (`#AD1E23`) only on primary actions, active selection states, and critical risk flags. Keep it below 10% surface coverage per screen — its rarity is the signal.
- **Do** pair every status color (green/amber/blue) with a label or icon. Color is never the only indicator of severity.
- **Do** use `-0.03em` letter-spacing on all Space Grotesk headings at Title size and above, without exception.
- **Do** show diffuse ambient shadows on content cards (KPI cards, bundle cards) at rest, before hover. The shadow communicates that the card holds a decision-relevant number.
- **Do** keep data rows, risk breakdown tables, and sidebar list items flat. Tonal separation via background color only — shadows on reference data suggest false importance.
- **Do** use `scale(0.97)` press feedback on every button. Every click must be physically acknowledged.
- **Do** use specific Indian figures, named IRDAI/RBI regulations, and sector-specific language in every output. Generic global statements erode trust.
- **Do** respect `prefers-reduced-motion`. Every animation and transition has a no-motion fallback that preserves layout but removes movement.

### Don't:
- **Don't** build generic SaaS admin dashboards: teal/blue accent, sidebar nav with icons, identical card grids, hero-metric number strips, "Overview" headings. This is the exact aesthetic SPARC rejects. If it looks like a Tailwind Admin template, it's wrong.
- **Don't** use `border-left` greater than 1px as a colored accent stripe on cards, callouts, or alerts. It is the most common SaaS cliché and reads immediately as amateur. Rewrite with full borders, background tints, or leading numbers.
- **Don't** use gradient text (`background-clip: text`). Decorative, never meaningful. Use Signal Red solid color for emphasis; use weight or size for hierarchy.
- **Don't** use glassmorphism (`backdrop-filter: blur`) on primary content cards, KPI cards, or results surfaces. It is reserved for the topbar, the role-selection landing screen, and the sticky sidebar — contexts where the "looking through glass" reading carries meaning. Applied to every card, it becomes a generic fintech cliché.
- **Don't** use consumer fintech aesthetics: gradient blobs, bright primary colors, rounded-everything phone-app energy. SPARC is a B2B tool used on laptops in meeting rooms.
- **Don't** use legacy insurance portal aesthetics: dense unnested form tables, flat corporate blue (#003087 type), 2008 banking software energy.
- **Don't** use `transition: all`. Specify only the properties that animate (`background`, `box-shadow`, `transform`, `border-color`). `transition: all` produces unexpected repaints and overrides `prefers-reduced-motion` suppression.
- **Don't** use identical card grids — same-sized cards with icon + heading + body text, repeated in a uniform grid. Vary card types, sizes, and content density to communicate hierarchy.
- **Don't** use `#000000` pure black or `#ffffff` pure white as the page background. Assessment Paper (`#FAFAF8`) is the canvas; Pure White is card fill only.
- **Don't** animate CSS layout properties (`width`, `height`, `padding`, `margin`, `top`, `left`). Animate `transform` and `opacity` only for motion that won't trigger layout reflow.
