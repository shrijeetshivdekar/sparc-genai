# Claude Code Prompt - SPARC SVP Infographic Presentation

Paste everything in this file into Claude Code from the root of this repository. The goal is to generate a dense, infographic-rich executive presentation for the selected SPARC SVP pitch.

## Build Task

Create a standalone presentation deck for:

**SPARC - Startup Protection and Risk Classification engine**  
**Client/audience:** Senior Vice President, ICICI Lombard Commercial Lines  
**Format:** 15-20 minute executive pitch with live app demo cues  
**App demo URL:** `http://localhost:5174`

Use the existing narrative from `SVP_PRESENTATION_SCRIPT.md`, but turn it into a visually dense, infographic-led presentation. The result must be suitable for a senior insurance executive: commercially sharp, data-heavy, risk-aware, and demo-oriented.

## Files To Create

Create these files:

1. `startup_shield_web/svpi_infographic_deck.html`
2. `startup_shield_web/svpi_infographic_deck.css`
3. `startup_shield_web/svpi_infographic_deck.js`
4. `startup_shield_web/SVPI_DECK_RUNBOOK.md`

The deck must run locally by opening the HTML file directly in a browser. Do not require a build step. Use only HTML, CSS, and vanilla JavaScript. Use inline SVG/CSS shapes for the infographics. Do not depend on external images, CDNs, fonts, or network calls.

## Design Direction

Make the deck dense, infographic-rich, and executive. This is not a marketing landing page. Each slide should feel like an analyst briefing page with multiple charts, callouts, counters, diagrams, and compact labels.

Rules:

- Use all 36 infographic patterns listed in the "Mandatory Infographic Matrix" below.
- Each infographic pattern must appear as a distinct visual component in the deck.
- Use a mix of dark-background slides and white-background slides, matching the source infographic families.
- Avoid empty whitespace. Prefer compact dashboards, side-by-side analysis panels, small multiples, and annotated diagrams.
- Keep all text legible on 16:9 presentation screens.
- Use ICICI Lombard-adjacent colors without copying a logo: deep navy, white, orange, teal, green, red, graphite, and light grey.
- Add slide numbers, section labels, and presenter notes.
- Add keyboard navigation: left/right arrows, space, and on-screen prev/next controls.
- Add a print mode so the deck can be exported to PDF from the browser.
- Use `INR`, not the rupee symbol, for ASCII compatibility.

## Mandatory Infographic Matrix

Use every infographic pattern below. The deck can combine two patterns on one slide, but each pattern must be visually recognizable.

| ID | Infographic Pattern | Use On Slide |
|---|---|---|
| I1.1 | Dark 7-segment donut/wheel with icons and outside labels | Slide 2 - Thirteen-risk surface, part A |
| I1.2 | Dark 5-slice circular arrow infographic | Slide 6 - Regulatory trigger logic |
| I1.3 | Dark 8-segment donut with numbered tabs and icons | Slide 4 - Risk-scoring model |
| I1.4 | Dark 7-blade pinwheel/fan diagram | Slide 10 - Deeptech risk pivot |
| I1.5 | Dark 9-segment shutter diagram with checklist | Slide 5 - Nine bundle architecture |
| I1.6 | Dark 3-circle Venn/trisected circle | Slide 1 - Market gap |
| I1.7 | Dark 4-level funnel | Slide 3 - SPARC engine architecture |
| I1.8 | Dark 2018-2023 horizontal timeline | Slide 13 - Risk/compliance evolution |
| I1.9 | White 10-spoke gear attribute wheel | Slide 4 - Underwriting attributes |
| I2.1 | Road perspective with 4 milestones and skyline | Slide 1 - Startup lifecycle road |
| I2.2 | Vertical stepped process with years and walking figure | Slide 15 - 60-day pilot plan |
| I2.3 | 3-link chain infographic | Slide 3 - Data-to-recommendation chain |
| I2.4 | Megaphone with three promotion items | Slide 16 - RM enablement |
| I2.5 | 3-step chevron progression with megaphone | Slide 9 - Estimated quote workflow |
| I2.6 | Brain/mind with 6 connected label boxes | Slide 2 - Risk intelligence model |
| I2.7 | 3-layer isometric stack | Slide 10 - Deeptech asset stack |
| I2.8 | Hub-and-spoke with central "Because" hexagon | Slide 16 - Why RMs convert faster |
| I2.9 | Hot-air-balloon mixed layout with 6 surrounding blocks | Slide 17 - Strategic lift |
| I3.1 | Gear-tree or mechanical brain with 3 options | Slide 17 - Operating choices |
| I3.2 | 4-level stacked arrow infographic | Slide 7 - Fintech demo setup |
| I3.3 | Annual report grouped monthly bar chart | Slide 8 - TAM/revenue view |
| I3.4 | Concentric market structure donut with 4 percentage labels | Slide 8 - Market structure |
| I3.5 | Bullseye target with 3 label boxes | Slide 7 - Target customer profile |
| I3.6 | 5-petal flower/leaf infographic | Slide 18 - Combined value proposition |
| I3.7 | 3-step winding/snake arrow | Slide 12 - D2C manufacturing progression |
| I3.8 | 8-item numbered two-column grid | Slide 5 - Bundle catalogue grid |
| I3.9 | 5-level triangle pyramid | Slide 11 - Drone compliance escalation |
| I4.1 | 5-step 3D staircase pyramid | Slide 12 - Corporate Cover II graduation |
| I4.2 | 6-level funnel with content boxes | Slide 6 - Six regulatory signals |
| I4.3 | Horizontal 5-stage narrowing funnel | Slide 9 - Quote estimation funnel |
| I4.4 | 2014-2018 hexagon timeline | Slide 13 - Versioned roadmap |
| I4.5 | 2018-2022 company achievement timeline | Slide 14 - Commercial rollout milestones |
| I4.6 | Four circular percentage indicators | Slide 14 - Revenue/profit metrics |
| I4.7 | Radial comparison timeline | Slide 11 - Bundle gap comparison |
| I4.8 | Curved-arrow planning timeline | Slide 15 - Pilot execution |
| I4.9 | Heart-shaped 4-piece puzzle | Slide 18 - Final ask and alignment |

## Slide Plan And Presenter Script

Build exactly 18 main slides. Each slide must include a visible "Presenter note" drawer or note panel that can be toggled.

### Slide 1 - The Market Gap

Infographics: I1.6 and I2.1.

Visual content:

- Large headline: "112,000+ recognized startups. Underinsured by design, not by intent."
- Venn labels: "Assets", "Liabilities", "Regulation"; center label: "Uninsured startup exposure".
- Road milestones: "Seed", "Series A", "Series B", "Growth".
- KPI strip:
  - 112,000+ DPIIT-recognized startups
  - 12 lakh+ employees
  - USD 140B+ funding raised
  - INR 29,780 Cr bundle TAM

Presenter note:

"Let me start with the gap. India now has more than 112,000 DPIIT-recognized startups. These companies employ more than 12 lakh people and have raised more than USD 140 billion. But most of them still think of insurance as a group health policy bought because an investor required it. Their actual exposure sits at the intersection of assets, liabilities, and regulation. That intersection is the opportunity."

### Slide 2 - Startup Risk Is Not Generic SME Risk

Infographics: I1.1 and I2.6.

Visual content:

- 7-segment donut: "Cyber", "Data", "Governance", "Liability", "Property", "IP", "Labour".
- Brain boxes: "Policy velocity", "ESG pressure", "Gig labour", "Chinese supplier dependency", "DPDP", "Investor scrutiny".
- Add side note: "13 dimensions scored. Startup-specific weights. Config-driven."

Presenter note:

"SPARC does not treat a startup as a small factory with a website. It scores 13 dimensions calibrated to the startup landscape: cyber, data privacy, governance, IP, regulatory pressure, policy velocity, gig labour, climate, and geopolitical exposure. These are risks that standard SME tooling generally does not score with enough precision."

### Slide 3 - What SPARC Does

Infographics: I1.7 and I2.3.

Visual content:

- Four-level funnel:
  1. Startup profile intake
  2. 13-risk scoring
  3. Bundle matching
  4. Regulatory and quote output
- Chain links:
  - "Profile"
  - "Risk"
  - "Revenue"
- Add compact architecture strip: `research_config.json -> risk_engine.py -> bundle_recommender_v2.py -> pricing_engine.py -> web app`.

Presenter note:

"SPARC is a recommendation engine with three jobs. It ingests the startup profile, scores the risk, maps the profile to one of nine curated insurance bundles, and then fires compliance and pricing intelligence. The key point is that the product team can update the research config without rewriting the engine."

### Slide 4 - The Scoring Model

Infographics: I1.3 and I1.9.

Visual content:

- 8-segment donut for major score families:
  - Cyber/Data
  - Governance/Fraud
  - Liability
  - IP
  - Property
  - Regulatory
  - ESG/Geo
  - Labour/Reputation
- Gear wheel with 10 spokes:
  - Sector multiplier
  - Stage multiplier
  - Asset band
  - Data sensitivity
  - Investor status
  - Regulatory license
  - Physical footprint
  - Export/supplier exposure
  - Claims control flag
  - Quote inputs

Presenter note:

"The model is deterministic and auditable. A fintech Series A profile gets a different loading than a D2C manufacturing profile because the sector, funding stage, data handling, regulation, and asset footprint all change the risk surface. That is what lets the RM walk into a meeting with a recommendation rather than a catalogue."

### Slide 5 - Nine Curated Bundles

Infographics: I1.5 and I3.8.

Visual content:

- Shutter diagram with 9 bundle segments:
  - Startup Shield Pack
  - Corporate Cover II
  - MSME Suraksha Kavach
  - Bharat Sookshma Udyam Suraksha
  - Deeptech Innovation Bundle
  - Employee Welfare Bundle
  - Marine Trade Credit Bundle
  - Engineering Project Bundle
  - Climate Parametric Bundle
- Right checklist: bundle, target segment, base premium, margin, graduation stage.
- 8-item grid should show 8 bundles; the 9th should be highlighted in the shutter center.

Presenter note:

"The recommendation output is not one product. It is a bundle decision. SPARC chooses from nine curated bundles and explains the fit score, premium estimate, margin context, and graduation path. That makes it useful both for sales and portfolio strategy."

### Slide 6 - Regulatory Trigger Engine

Infographics: I1.2 and I4.2.

Visual content:

- 5-slice circle:
  1. Data handled
  2. Licensed activity
  3. Physical operation
  4. Sector-specific rule
  5. Mandatory cover
- 6-level funnel:
  - DPDP/CERT-In
  - RBI digital lending
  - DGCA Drone Rule 44
  - Companies Act D&O
  - Labour/gig exposure
  - Environmental/EPR
- Use small citation chips: "Trigger", "Citation", "Mandatory cover", "RM action".

Presenter note:

"The regulatory module is the feature that changes the RM conversation. If a startup handles KYC data, DPDP and CERT-In flags appear. If it is RBI-licensed, the digital lending direction appears. If it operates drones, DGCA Rule 44 triggers Drone RPAS. The RM does not need to remember every regulation. SPARC checks every profile every time."

### Slide 7 - Live Demo 1: Fintech Series A Setup

Infographics: I3.5 and I3.2.

Visual content:

- Bullseye target: "NBFC digital lending fintech".
- Three target boxes:
  - "Series A"
  - "55 employees"
  - "KYC + payments data"
- Stacked arrows:
  - Initial profile
  - Risk scoring
  - Bundle match
  - Compliance triggers
- Demo cue panel:
  - Sector: Fintech
  - Sub-sector: Fintech.NBFC_Digital_Lending
  - Funding Stage: Series A
  - Team Size: 55
  - Operations: Digital-only
  - Data handled: Payments + KYC/Aadhaar
  - Regulatory: RBI/SEBI/IRDAI licensed + DPDP Act obligations
  - Data sensitivity: High
  - Physical assets: Office/coworking

Presenter note:

"For the first live profile, I am using a digital lending fintech. Series A, 55 employees, Bangalore-based, high data sensitivity, payments and KYC data, RBI licensing, and DPDP obligations. This is exactly the kind of account where the RM knows there is opportunity but may not know the full coverage map."

### Slide 8 - Live Demo 1: Recommendation Output

Infographics: I3.3 and I3.4.

Visual content:

- Annual-report style bar chart:
  - Startup Shield Pack TAM: INR 1,760 Cr
  - Corporate Cover II TAM: INR 880 Cr
  - Employee Welfare: INR 4,200 Cr
  - MSME Suraksha: INR 16,250 Cr
- Market structure donut:
  - 89% fit score
  - Cyber 82
  - Data privacy 85
  - Regulatory 78
  - Governance 72
- Show rank 1 card:
  - Startup Shield Pack
  - Mandatory covers: Cyber, D&O, PI/Tech E&O, Crime/Fidelity
  - Triggers: DPDP/CERT-In and RBI digital lending

Presenter note:

"The engine returns Startup Shield Pack as rank one. The important part is not only the bundle name. It tells us why: cyber and data privacy are elevated, regulatory compliance is high, and governance has moved into investor scrutiny territory. The RM also sees DPDP/CERT-In and RBI digital lending triggers with a mandatory cover path."

### Slide 9 - Live Demo 1B: Estimated Quote Feature

Infographics: I4.3 and I2.5.

Visual content:

- Horizontal 5-stage quote funnel:
  1. Recommendation generated
  2. Quote inputs requested
  3. Underwriting values entered
  4. Bundle-only quote calculated
  5. Full priced cover set calculated
- Chevron progression:
  - "Informing: required inputs"
  - "Persuading: price range becomes tangible"
  - "Reminding: quote remains indicative, subject to underwriting"
- Quote input table:
  - Cyber limit: 7.5 Cr
  - D&O limit: 5 Cr
  - PI/Tech E&O limit: 5 Cr
  - Crime/Fidelity limit: 1 Cr
  - Receivables on credit: 2 Cr
  - Public liability limit: 2 Cr
- Quote output snapshot:
  - Bundle-only quote: approx INR 45.24L gross incl. GST
  - Full cover quote: approx INR 56.13L gross incl. GST
  - Bundle-only covers priced: 4
  - Full cover set priced: 7
  - Referral flag: Cyber risk score is 85+, require control questionnaire before firm pricing
  - Source of truth: live app calculation

Demo cue:

`[DEMO: In the Fintech result screen, scroll to Estimated quote. Enter cyber_limit_cr = 7.5, dno_limit_cr = 5, pi_limit_cr = 5, crime_limit_cr = 1, receivables_on_credit_cr = 2, public_liability_limit_cr = 2. Click "Generate estimated quote". Show Bundle quote and Full cover price cards.]`

Presenter note:

"This is where the RM moves from recommendation to commercial action. SPARC does not calculate a premium until the underwriting inputs are supplied. Once I enter the SI and exposure values, the pricing engine produces an indicative quote. In this profile the current engine shows approximately INR 45.24 lakh gross for the bundle-only quote and INR 56.13 lakh gross for the fuller priced cover set, including GST. It also shows the basis, covers priced, discount, GST, and referral flags. This is still subject to underwriting, but it gives the RM a credible number in the first meeting."

### Slide 10 - Live Demo 2: Deeptech Drone Startup

Infographics: I1.4 and I2.7.

Visual content:

- Pinwheel blades:
  - Lab equipment
  - Drone hull
  - Product liability
  - IP
  - DGCA
  - Property
  - D&O
- 3-layer stack:
  - Physical assets: lab + drones
  - Operational risk: hardware-heavy logistics
  - Mandatory cover: Drone RPAS
- Demo inputs:
  - Sector: Deeptech / AI / Robotics
  - Stage: Series A
  - Team: 30
  - Physical assets: Lab/R&D equipment + Drones/UAV equipment
  - Hardware/software split: 55%
  - Regulatory: DGCA/drone operations

Presenter note:

"The second case is intentionally harder: a deeptech robotics company doing AI-powered drone logistics. This is not a standard cyber and D&O conversation. The asset profile has shifted. Hardware and regulated aviation exposure now matter."

### Slide 11 - Drone Compliance And Bundle Gap

Infographics: I3.9 and I4.7.

Visual content:

- Pyramid:
  1. Startup profile
  2. DGCA exposure
  3. Drone Rule 44 trigger
  4. Drone RPAS mandatory cover
  5. Bundle gap warning
- Radial comparison:
  - Deeptech Innovation Bundle: covers Drone RPAS, Engineering, Product Liability, D&O
  - Startup Shield Pack: gap - lacks Drone RPAS
  - Corporate Cover II: graduation option
  - Standalone add-on: tactical option
  - RM action: upgrade/bundle pivot
  - Claims risk: underinsurance gap

Presenter note:

"SPARC correctly pivots from Startup Shield Pack to Deeptech Innovation Bundle. It also tells the RM why Startup Shield is insufficient for this profile: it lacks Drone RPAS. That is a compliance gap, not just a product preference."

### Slide 12 - Live Demo 3: D2C Series B Manufacturing

Infographics: I4.1 and I3.7.

Visual content:

- 3D staircase:
  - Seed: Startup Shield Pack
  - Series A: MSME / Engineering
  - Series B: Corporate Cover II
  - Growth: Corporate Cover II + specialty add-ons
  - Enterprise: portfolio renewal
- Winding arrows:
  - Warehouse
  - Factory
  - Liability + D&O
- Demo inputs:
  - Sector: D2C / Consumer Brands
  - Funding Stage: Series B+
  - Team: 200
  - Physical assets: Manufacturing plant + warehouse
  - Hardware split: 75%
  - Operations: Hybrid

Presenter note:

"The third demo shows the graduation path. A D2C electronics brand at Series B with a manufacturing plant is no longer a simple startup account. Corporate Cover II should become the lead recommendation because the liability, property, employer, governance, and cyber surfaces have converged."

### Slide 13 - Lifecycle And Versioned Intelligence

Infographics: I1.8 and I4.4.

Visual content:

- 2018-2023 timeline:
  - Startup formation
  - Data protection pressure
  - Funding growth
  - Drone/digital lending regulation
  - Climate/ESG pressure
  - AI and cyber escalation
- Hex timeline:
  - v2026.05 config
  - weight updates
  - regulatory citations
  - product refresh
  - CRM feedback loop
- Note: "No code deployment needed for research-config changes."

Presenter note:

"The risk landscape changes faster than insurance product cycles. SPARC is config-driven so the product team can update weights, citations, and multipliers as regulations change. The engine becomes a living research layer rather than a frozen spreadsheet."

### Slide 14 - Commercial Impact

Infographics: I4.6 and I4.5.

Visual content:

- Circular percentage indicators:
  - 3x conversion lift
  - 2 weeks target sales cycle
  - INR 63 Cr incremental GWP from Startup Shield cohort
  - INR 6.9 Cr incremental operating profit
- Company achievement timeline:
  - Pilot
  - CRM logging
  - Claims calibration
  - Bundle penetration lift
  - Portfolio optimization
- TAM table:
  - MSME Suraksha Kavach: INR 16,250 Cr TAM, 6% margin, 5% adoption, INR 48.75 Cr annual revenue potential
  - Employee Welfare Bundle: INR 4,200 Cr TAM, 9% margin, 32% adoption, INR 120.96 Cr annual revenue potential
  - Bharat Sookshma Udyam Suraksha: INR 2,560 Cr TAM, 18% margin, 5% adoption, INR 23.04 Cr annual revenue potential
  - Startup Shield Pack: INR 1,760 Cr TAM, 11% margin, 22% adoption, INR 42.59 Cr annual revenue potential
  - Corporate Cover II: INR 880 Cr TAM, 13% margin, 40% adoption, INR 45.76 Cr annual revenue potential

Presenter note:

"The top five bundles alone represent INR 281 crore of annual revenue potential at current adoption assumptions. SPARC changes the economics because it lets the RM walk in with the right recommendation, the regulatory angle, and a quote path. Moving Startup Shield conversion from 10 percent to 30 percent creates an incremental INR 63 crore of GWP and INR 6.9 crore of operating profit from one bundle cohort."

### Slide 15 - Pilot Plan

Infographics: I2.2 and I4.8.

Visual content:

- Vertical step process:
  - Day 0: leadership endorsement
  - Day 7: RM cohort selected
  - Day 14: training complete
  - Day 30: first conversion review
  - Day 60: SVP readout
- Curved timeline:
  - Mumbai + Bengaluru
  - 50 RM accounts
  - fintech, deeptech, D2C clusters
  - conversion and quote click-through
  - CRM audit trail

Presenter note:

"The ask is not a large transformation program. It is a 60-day pilot with 50 RM accounts in Mumbai and Bengaluru. We measure recommendation acceptance, estimated quote click-through, conversion, sales-cycle duration, and coverage gaps surfaced."

### Slide 16 - RM Enablement

Infographics: I2.4 and I2.8.

Visual content:

- Megaphone list:
  - "Conversation opener: quantified risk"
  - "Sales motion: bundle recommendation"
  - "Close path: estimated quote"
- Hub-and-spoke around "Because":
  - Because the RM has a fit score
  - Because citations are attached
  - Because premium is estimated
  - Because graduation is mapped
  - Because gaps are visible
  - Because CRM can log the event

Presenter note:

"The operational benefit is simple: SPARC turns every RM into a specialist. They can explain why the client needs Cyber, D&O, Drone RPAS, Engineering, or Corporate Cover II without manually researching the sector each time."

### Slide 17 - Strategic Operating Choices

Infographics: I2.9 and I3.1.

Visual content:

- Hot-air-balloon center: "Scale specialty lines without scaling specialist headcount one-for-one."
- Six surrounding blocks:
  - RM productivity
  - Claims-quality feedback
  - Underwriting calibration
  - Product-bundle governance
  - CRM data asset
  - Regulatory auditability
- Gear-tree options:
  1. Pilot as RM assist tool
  2. Integrate into CRM
  3. Calibrate with claims/GWP data

Presenter note:

"Strategically, SPARC is not just a demo app. It is a data asset. Every recommendation, quote request, override, and conversion can be logged. That gives underwriting and product teams the dataset they need to improve pricing and portfolio decisions."

### Slide 18 - Final Ask

Infographics: I3.6 and I4.9.

Visual content:

- Flower petals:
  - Revenue
  - Risk quality
  - RM productivity
  - Compliance
  - Data asset
- Heart puzzle pieces:
  - 50 RMs
  - 2 cities
  - 60 days
  - claims/GWP access
- Closing statement:
  - "Let us put SPARC in front of 50 RMs for 60 days. The numbers will make the case."

Presenter note:

"To summarize: SPARC scores 13 risks, maps startups to nine bundles, fires mandatory regulatory triggers, estimates premium potential, generates an indicative quote when underwriting inputs are supplied, and creates a lifecycle roadmap. The ask is a 50-RM, two-city, 60-day pilot with access to claims and GWP data for calibration."

## Live Demo Runbook

Add this runbook to `startup_shield_web/SVPI_DECK_RUNBOOK.md`.

### Before Starting

1. Start the app at `http://localhost:5174`.
2. Open `startup_shield_web/svpi_infographic_deck.html` in a browser.
3. Keep the app and the deck in adjacent browser tabs.
4. Use the deck for narrative and switch to the app at slides 7, 9, 10, and 12.

### Demo 1 - Fintech Series A

Inputs:

- Sector: Fintech
- Sub-sector: Fintech.NBFC_Digital_Lending
- Funding Stage: Series A
- Team Size: 55
- Operations: Digital-only
- Data handled: Payments / financial transactions; Personal identity data (KYC / Aadhaar)
- Regulatory: RBI / SEBI / IRDAI licensed; DPDP Act obligations
- Data sensitivity: High
- Physical assets: Office / coworking space
- Has investors: Yes

Expected output:

- Startup Shield Pack rank 1
- DPDP/CERT-In and RBI triggers fired
- Mandatory covers include Cyber, D&O, PI/Tech E&O, Crime/Fidelity
- Premium potential range appears
- Estimated quote panel requests underwriting inputs by default

### Demo 1B - Estimated Quote

After the Fintech recommendation appears, scroll to the Estimated quote panel.

Enter:

- `cyber_limit_cr`: 7.5
- `dno_limit_cr`: 5
- `pi_limit_cr`: 5
- `crime_limit_cr`: 1
- `receivables_on_credit_cr`: 2
- `public_liability_limit_cr`: 2

Click: `Generate estimated quote`.

Expected current-engine output:

- Bundle-only quote: approx INR 45.24L gross incl. GST
- Full cover quote: approx INR 56.13L gross incl. GST
- Bundle-only covers priced: 4
- Full cover set priced: 7
- Referral flag: Cyber risk score is 85+, require control questionnaire before firm pricing
- Show net premium, GST, total SI, cover rows, bundle discount, and assumptions

Talk track:

"The quote is not automatic until underwriting inputs are supplied. This prevents false precision. Once the RM enters SI and exposure values, the system produces an indicative quote with cover-level pricing, GST, bundle discount, assumptions, and referral flags. It is not a bindable quote, but it lets the RM move the first meeting from interest to commercial discussion."

### Demo 2 - Deeptech Drone

Inputs:

- Sector: Deeptech / AI / Robotics
- Funding Stage: Series A
- Team Size: 30
- Physical assets: Lab / R&D equipment; Drones / UAV equipment
- Hardware/software split: 55%
- Regulatory: DGCA / drone operations
- Operations: Hardware / IoT or Hybrid

Expected output:

- Deeptech Innovation Bundle rank 1
- DGCA Drone Rule 44 trigger fired
- Drone RPAS mandatory cover appears
- Startup Shield Pack shows a compliance gap if it lacks Drone RPAS

### Demo 3 - D2C Series B Manufacturing

Inputs:

- Sector: D2C / Consumer Brands
- Funding Stage: Series B+
- Team Size: 200
- Physical assets: Manufacturing plant / factory; Warehouse / fulfilment centre
- Hardware/software split: 75%
- Operations: Hybrid

Expected output:

- Corporate Cover II rank 1
- Fit score 90% or higher if current config matches existing demo assumptions
- Liability, property, D&O, and employer/commercial covers visible
- Graduation roadmap visible

## Implementation Notes For Claude Code

- Build reusable SVG/CSS components for each infographic family.
- Put infographic data in JavaScript arrays so the deck is maintainable.
- Use deterministic placeholder icons made from inline SVG paths or CSS glyphs. Do not fetch icon libraries.
- Add a `data-infographic-id` attribute to every required visual component so it is easy to verify all 36 are present.
- Add a small verification checklist in the runbook listing all 36 IDs and the slide where each appears.
- Include a "source" note in the footer: "SPARC research_config v2026.05; current pricing_engine output subject to code/config changes."
- Do not alter the existing app behavior unless necessary. This task is deck generation, not product modification.

## Acceptance Criteria

The work is complete only when:

1. The HTML deck opens locally with all 18 slides.
2. All 36 infographic IDs appear in the DOM as `data-infographic-id`.
3. Keyboard navigation works.
4. Presenter notes can be toggled.
5. Print/PDF mode is usable.
6. The estimated quote demo is included on Slide 9 and in the runbook.
7. The deck explicitly includes the three live demo scenarios and the exact quote inputs.
8. The visual density is high: no slide should be only text.
9. The runbook tells the presenter exactly what to click and what output to expect.

