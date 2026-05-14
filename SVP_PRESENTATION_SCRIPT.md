# SPARC — SVP Presentation Script
### ICICI Lombard: Startup & SME Insurance Intelligence Platform
**Audience:** Senior Vice President, ICICI Lombard  
**Duration:** 15–20 minutes  
**Format:** Live app demo + narrative  
**Presenter Notes:** Cues marked `[DEMO]`, `[PAUSE]`, `[SLIDE]` throughout

---

## SEGMENT 1 — OPENING HOOK (1.5 min)

"Let me start with a number: there are over **1,12,000 DPIIT-recognised startups in India** today. That's more than any country in the world except the US and China.

These companies collectively employ over **12 lakh people**, have raised more than **$140 billion in funding**, and are sitting on assets, liabilities, intellectual property, customer data, and regulatory obligations worth trillions of rupees.

And yet — if you ask their founders what insurance they have — the honest answer from most of them is: a group health policy they bought because their Series A term sheet required it.

**That is our gap. And that is our opportunity.**

The average Indian startup at Series A stage is carrying at least five material, uninsured risks. A DPDP Act breach, a D&O claim from an investor, a key-person event, a ransomware attack, a product liability suit — any one of these can be an existential event.

ICICI Lombard has the products to cover every single one. The problem isn't the product shelf. The problem is that **we have no systematic way to match the right bundle to the right startup at the right moment in their lifecycle.**

What I'm going to show you today is how we solved that."

---

## SEGMENT 2 — WHAT IS SPARC (2 min)

"The product is called **SPARC — Startup Protection and Risk Classification engine**.

At its core, SPARC does three things:

**First**, it ingests a startup's profile — sector, funding stage, team size, data they handle, regulatory exposure, physical assets, geographic footprint — and runs it through a **13-dimension risk scoring model** calibrated specifically to the Indian startup risk landscape. Not generic SME weights. Startup-specific: policy velocity, gig labour exposure, ESG pressure, geopolitical risk from Chinese supplier dependency — dimensions that no standard underwriting tool in our industry is scoring today.

**Second**, it maps that risk profile to the implemented **13-bundle catalog** in `research_config.json` — including Business Shield SME, I-select Liability Insurance, Industrial All Risk, Group Safeguard, Enterprise Secure, Corporate Cover II, and asset-tiered Bharat products — each with a computed fit score, premium estimate, and deterministic rationale that a Relationship Manager can use in a client conversation immediately.

**Third**, where enabled, it runs a guarded GenAI reranker on top of the deterministic shortlist. GenAI can reorder only products and bundles that the rules engine has already admitted. If the model is unavailable, malformed, slow, or tries to recommend an ineligible cover, SPARC falls back to deterministic output and records the reason in the API response.

**Fourth**, it fires **regulatory compliance triggers** automatically. If a startup operates drones, the DGCA Drone Rule 44 trigger fires and Drone RPAS cover becomes mandatory in the recommendation. If they handle personal data above a threshold, DPDP Act compliance flags are raised. If they're RBI-licensed, the digital lending direction is cited. The RM never misses a mandatory cover again.

The whole engine is backed by a **config-driven research layer** — `research_config.json` — which means every weight, every multiplier, every regulatory citation can be updated by the product team without touching a line of code. We can push new IRDAI regulation changes to the recommendation engine in minutes.

Let me show you this live."

---

## SEGMENT 3 — LIVE DEMO: SCENARIO 1 — Fintech Series A (4 min)

`[DEMO: Open the app. Navigate to the onboarding form.]`

"Let's take a real-world profile. An NBFC — digital lending fintech. Series A, 55 people, Bangalore-based.

`[DEMO: Select sector = Fintech, Sub-sector = Fintech.NBFC_Digital_Lending, Funding Stage = Series A, Team Size = 55]`

They handle payments and KYC data — so tick 'Payments / financial transactions' and 'Personal identity data (KYC / Aadhaar)'. They're RBI licensed. DPDP Act obligations apply.

`[DEMO: Check RBI / SEBI / IRDAI licensed, DPDP Act obligations. Data sensitivity = High.]`

No physical assets beyond an office. Digital-only operations.

`[DEMO: Physical assets = Office / coworking space. Hit Analyse.]`

`[PAUSE — let results load]`

Look at what the engine returns.

**Risk scores first.** Cyber Technical Risk at 82. Data Privacy at 85. Regulatory Compliance at 78. Governance & Fraud at 72. These aren't guesses — the 13-weight model has applied a 1.5x fintech multiplier to cyber and data privacy, a 1.5x regulatory compliance multiplier, and a 1.4x governance multiplier because they're at Series A stage, which is exactly when founder-level governance starts coming under investor scrutiny.

**Now the bundle recommendation.** The current v2 catalog ranks **Business Shield SME** for this profile, with I-select Liability Insurance also surfaced for liability and professional indemnity exposure. The output shows the deterministic score and, when `SPARC_GENAI_MODE` is `shadow` or `primary`, whether GenAI agreed with or reordered the shortlist.

The mandatory covers: Cyber, D&O, Professional Indemnity / Tech E&O, Crime Fidelity.

**And look at the regulatory triggers panel.** Two triggers have fired: DPDP Act / CERT-In — because sdf_probability crossed 0.6 from KYC data handling — and the RBI digital lending direction. These aren't warnings. They're citations: regulation name, citation URL, mandatory product. The RM clicks through to the MEITY gazette reference directly from the card.

**The revenue intelligence panel** shows the config-backed TAM, adoption, margin, and trajectory fields for the ranked bundles. These are sourced from `research_config.json`, not from invented pilot assumptions.

Corporate Cover II appears in the list as well — but correctly staged out. It's flagged as ineligible at Series A, with a graduation path to later-stage cover. That's the graduation path feature — we're not just selling the first policy. We're building the relationship roadmap."

---

## SEGMENT 4 — LIVE DEMO: SCENARIO 2 — Deeptech Drone Startup (3.5 min)

`[DEMO: Clear form. New profile.]`

"Now let's look at a harder case. A deeptech robotics company — AI-powered drone logistics. Series A. Hardware-heavy.

`[DEMO: Sector = Deeptech / AI / Robotics, Funding Stage = Series A, Team Size = 30]`

Physical assets: Lab / R&D equipment, Drones / UAV equipment. Hardware split is 55%. Add the insurable asset value if you want the v2 catalog to route into an industrial policy rather than falling back to the older bundle logic.

`[DEMO: Physical assets = Lab / R&D equipment + Drones / UAV equipment. Hardware/Software split = 55%. Regulatory = DGCA / drone operations. Hit Analyse.]`

`[PAUSE]`

**Watch the regulatory trigger section.**

DGCA Drone Rules 2021 Rule 44 — fired. Mandatory product: Drone RPAS. There is a legal obligation here. An RM who goes into this meeting without this knowledge is creating liability for us, not just missing a sale.

With sufficient asset value, the v2 catalog routes to **Industrial All Risk (IAR) Policy** because that is the implemented drone-compliant industrial bundle. It includes Drone RPAS in the bundle components and keeps non-compliant bundles out of the primary recommendation.

Premium estimate: INR 8 lakh. Margin: 10%. This is not a health policy conversation. This is a specialty lines conversation.

And here's the insight for the RM: the compliance flag panel shows when a candidate bundle lacks Drone RPAS for this profile. So if the client pushes back and says they already have a generic package, the RM has a documented reason to recommend an add-on or a bundle upgrade.

That's the difference between a reactive RM and a consultative one."

---

## SEGMENT 5 — LIVE DEMO: SCENARIO 3 — D2C Series B Manufacturing (2 min)

`[DEMO: Clear form. New profile.]`

"One more. A D2C brand — consumer electronics. Series B. They've just opened a manufacturing plant in Pune.

`[DEMO: Sector = D2C / Consumer Brands, Funding Stage = Series B+, Team Size = 200, Physical assets = Manufacturing plant / factory + Warehouse / fulfilment centre. Hardware split = 75%. Hit Analyse.]`

`[PAUSE]`

**Enterprise Secure Package Policy. Rank 1 in the current v1-style catalog.** Corporate Cover II remains in the later-stage shortlist and is shown as another eligible enterprise option.

This is our highest-value bundle — base premium INR 22 lakh. It includes CGL I-Elite, Public Liability, Employers' Compensation, D&O, and Cyber. TAM: INR 880 crore. Adoption already at 40%.

The graduation map shows the configured path across Seed, Series A, Series B, and Growth. This is a lifecycle relationship, not a one-time sale.

Liability Risk is at 86. Property Risk at 82. The Reputation Risk trigger at 78 has also fired — mandatory covers for the Companies Act 2013 D&O obligation are flagged because they're at Series B.

For reference: the premium estimates shown in the app are indicative outputs from the pricing engine and depend on declared underwriting inputs such as asset value, limits, payroll, and claims history."

---

## SEGMENT 6 — REVENUE AND PROFIT IMPACT (3 min)

`[SLIDE: TAM summary table]`

"Let me put the commercial picture together.

The 13 implemented bundles in SPARC collectively address a **configured TAM of INR 47,100 crore** in the Indian startup and SME segment. That number is the sum of the `tam_cr` fields in `research_config.json`; it is a configurable product-planning assumption, not a measured sales outcome.

The top five by addressable market:

| Bundle | TAM (Cr) | Margin | Adoption | Annual Revenue Potential |
|---|---|---|---|---|
| MSME Suraksha Kavach | 16,250 | 6% | 5% | INR 48.75 Cr |
| Business Edge Policy | 8,500 | 10% | 8% | INR 68.00 Cr |
| Bharat Laghu Udyam Suraksha | 5,200 | 16% | 7% | INR 58.24 Cr |
| Group Safeguard Insurance Policy | 4,200 | 9% | 32% | INR 120.96 Cr |
| Merchants Cover III | 2,800 | 10% | 8% | INR 22.40 Cr |

**Combined configured annual revenue potential from these five bundles alone: INR 318.35 crore.** This is calculated from TAM x adoption x margin in the config.

The point is not to claim a measured conversion uplift yet. The code supports a repeatable recommendation workflow, auditable trigger evidence, premium input capture, and shadow logging for deterministic-vs-GenAI comparison. Those are the prerequisites for measuring conversion and loss-ratio impact in a real pilot."

---

## SEGMENT 7 — ACCURACY, RISK REDUCTION, AND UNDERWRITING QUALITY (2 min)

"A word on accuracy — because this matters for underwriting quality, not just sales.

The SPARC engine is covered by the repo test suite, currently **121 passing tests**, covering combinations of sector, stage, asset profile, regulatory exposure, pricing, Bharat Sookshma SI cap rejection above INR 5 crore, drone trigger precision, life insurer routing for Group Term Life and Key Person products outside general-insurance composite bundles, v1-to-v2 shadow logging, and guarded GenAI reranking.

Every test passes with deterministic, reproducible results. GenAI tests use mocked structured responses so failure, malformed output, and hard-gate enforcement remain auditable.

The regulatory trigger module is particularly relevant for loss ratio management. When Drone RPAS is not included in a bundle for a drone-operations startup, and we're exposed to a DGCA-regulated liability event, the claims consequence is a problem of under-insurance and potential policy voidance. SPARC eliminates that gap systematically — not by relying on the RM to know every regulation, but by checking 6 live regulatory signals against every profile, every time.

This means: **better-matched policies, fewer coverage gaps at claims time, and a structurally lower loss ratio** on the startup segment — which has historically been poorly priced due to thin data.

The config is versioned — currently `research_config v2026.05` — and every weight, multiplier, and regulatory citation is auditable. If IRDAI issues a new circular, the product team updates one JSON file. No code deployment. The engine reflects the change within minutes."

---

## SEGMENT 8 — WHAT IT TAKES TO GO LIVE (1.5 min)

"The technology is demo-ready and structured for deployment hardening. The server runs as a standalone Python service, and the frontend is a clean RM-facing web app.

Three things we need from leadership to move from pilot to commercial rollout:

**One:** Endorsement to define a controlled pilot design, including account selection, success metrics, and compliance review before any conversion or sales-cycle claims are made.

**Two:** Access to our claims and historical GWP data for the startup segment, so we can calibrate the risk weights against actual loss experience and move from research-derived weights to actuarially-validated weights. That's the path from 'high accuracy' to 'actuarially defensible.'

**Three:** Integration with the CRM so every SPARC recommendation is logged against the RM-client record. This builds the dataset we need to continuously improve the model and creates the audit trail for regulatory review.

What we're asking for is access to the data and governance needed to validate the recommendation workflow in the field."

---

## SEGMENT 9 — CLOSING (1 min)

"To summarise.

India's startup segment represents a **configured INR 47,100 crore TAM** across the implemented bundle catalog, based on `research_config.json`.

SPARC is a recommendation engine that scores 13 risk dimensions, matches startups to the implemented 13-bundle catalog, fires mandatory regulatory triggers, estimates premium potential, and exposes whether GenAI influenced, shadowed, or fell back from the recommendation.

It gives every RM a structured risk conversation, reduces missed regulatory coverage gaps, and builds an auditable data asset we can validate over time.

We're not asking you to replace any existing system. We're asking for the governance and data access needed to run a controlled validation.

The numbers will make the case."

`[PAUSE]`

"I'm happy to take questions — or we can go deeper on any of the three demo scenarios right now."

---

## APPENDIX — QUICK-REFERENCE DEMO CHEAT SHEET

Use these exact inputs for a clean, rehearsed demo run:

### Demo 1: Fintech Series A -> Business Shield SME / I-select Liability
- Sector: Fintech | Sub-sector: Fintech.NBFC_Digital_Lending
- Funding Stage: Series A | Team: 55 | Operations: Digital-only
- Data handled: Payments / financial transactions + Personal identity data (KYC / Aadhaar)
- Regulatory: RBI / SEBI / IRDAI licensed + DPDP Act obligations
- Data sensitivity: High | Physical assets: Office / coworking space
- **Expected output:** Business Shield SME in v2 output, I-select Liability in the v1-style catalog, DPDP + RBI triggers visible, Cyber + D&O surfaced in eligible shortlist

### Demo 2: Deeptech Drone -> Industrial All Risk when asset value supports it
- Sector: Deeptech / AI / Robotics | Funding Stage: Series A | Team: 30
- Physical assets: Lab / R&D equipment + Drones / UAV equipment
- Hardware/Software split: 55% | Regulatory: DGCA / drone operations | Total insurable asset value: 60 Cr
- **Expected output:** Industrial All Risk (IAR) Policy in v2, DGCA Drone Rule 44 mandatory trigger, Drone RPAS in mandatory covers

### Demo 3: D2C Series B Manufacturing -> Enterprise Secure / Corporate Cover II shortlist
- Sector: D2C / Consumer Brands | Funding Stage: Series B+ | Team: 200
- Physical assets: Manufacturing plant / factory + Warehouse / fulfilment centre
- Hardware/Software split: 75% | Operations: Hybrid
- **Expected output:** Enterprise Secure Package Policy rank 1 in the v1-style catalog, Corporate Cover II eligible in shortlist, property + liability + D&O visible, graduation roadmap visible

---

## KEY NUMBERS TO REMEMBER

| Metric | Value |
|---|---|
| Total addressable bundles | 13 |
| Risk dimensions scored | 13 |
| Validated test scenarios | 121 passing tests |
| Combined configured bundle TAM | INR 47,100 crore |
| GenAI recommendation modes | off, shadow, primary |
| Guardrail behavior | Deterministic fallback on unavailable, malformed, or ineligible GenAI output |
| Regulatory triggers monitored | 6 live signals |
| Config version | 2026.05 |
| Unsupported outcome claims | No conversion, sales-cycle, or pilot uplift claimed without field data |

---

*Script prepared for: SVP, ICICI Lombard Commercial Lines | May 2026*
*App runs at: http://localhost:5174*
