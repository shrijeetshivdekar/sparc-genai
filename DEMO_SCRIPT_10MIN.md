# SPARC — 10-Minute Live Demo Script
**Audience:** SVP, ICICI Lombard Commercial Lines  
**Duration:** 10 minutes  
**Format:** Story-driven narrative with live app demo  
**App:** http://localhost:5174  

> Presenter cues in `[BRACKETS]`. Inputs to type are in **bold**. Speak everything else out loud.

---

## THE SETUP — 60 seconds

"I want to tell you about three meetings that happened last quarter.

Three RMs. Three founders sitting across a table. All three left the meeting with a recommendation. None of them had the same one.

What I'm going to show you is the tool that made that possible — and then I want to show you exactly what it's doing under the hood, because the backing matters as much as the output.

The tool is called SPARC. It takes a startup profile — sector, funding stage, what data they handle, what assets they own, what regulations apply — and in about fifteen seconds, it returns a specific bundle recommendation with a risk score, a mandatory cover list, the exact regulations that triggered each requirement, and an indicative premium.

Let's run three real profiles."

---

## COMPANY 1: RAZORPAY — 3 minutes

### The Story

"First meeting. Razorpay.

If you don't know Razorpay — they're India's largest payment aggregator by transaction volume. Founded in 2014, RBI-authorized PA license, roughly 3,500 employees today, processing payments for over six million businesses. They handle KYC data, Aadhaar-linked payment records, PAN, GST — the full stack of sensitive financial identity data.

The RM walking into this meeting knows Razorpay is a big account. But what should they lead with? What's the actual risk surface?

Let's ask the engine."

### Demo Inputs

`[DEMO: Open the app at http://localhost:5174. Start a new profile.]`

Type these:
- **Sector:** Fintech
- **Sub-sector:** Fintech.NBFC_Digital_Lending (closest available — Razorpay is an RBI PA, same compliance surface)
- **Funding Stage:** Series D+ (Growth equivalent)
- **Team Size:** 3500
- **Data handled:** Payments / financial transactions ✓ · Personal identity data (KYC / Aadhaar) ✓
- **Regulatory:** RBI / SEBI / IRDAI licensed ✓ · DPDP Act obligations ✓
- **Data sensitivity:** High
- **Physical assets:** Office / coworking space
- **Operations:** Digital-only

`[Click Analyse. Pause for results.]`

### What the Engine Returns — and Why

"Look at the risk scores first.

**Cyber Technical: 82. Data Privacy: 85. Regulatory Compliance: 78. Governance & Fraud: 72.**

Here's the math behind those numbers. The engine runs base weights from the research config — Cyber is weighted at 12%, Data Privacy at 13%. Then it applies sector multipliers: for fintech, both cyber and data privacy get a 1.5× loading. Governance gets 1.4×. That's not a guess — it reflects the actual loss frequency in fintech from fraud, insider trading, and payment diversion.

Then it checks the regulatory signal layer. Two triggers fire automatically:

**Trigger 1 — DPDP Act 2023 + CERT-In Directions 2022.** Razorpay handles personal identity data above the threshold. Under DPDP, a data breach must be reported to the Data Protection Board within 72 hours. CERT-In Directions require mandatory incident reporting to the government. Civil penalty exposure under DPDP: up to INR 250 crore per incident. The engine flags Cyber as mandatory.

**Trigger 2 — RBI Digital Lending Directions 2025.** RBI-licensed payment aggregators are now subject to operational resilience and business continuity requirements under these directions. A regulatory action or licence suspension without cover is an existential event
The bundle recommendation: **I-select Liability Insurance. 93% profile fit.**

Notice this isn't Business Shield SME — and the reason matters. Razorpay is Growth-stage, 3,500 employees, and running payment operations at enterprise scale. The engine has pushed past the early-stage bundle and surfaced five mandatory covers instead of four.

The difference is the fifth cover: **Employment Practices Liability.** At 3,500 employees — with a mix of full-time engineers, contract staff, and a layoff cycle visible in the press over the last 18 months — wrongful termination, discrimination, and harassment claims are a live exposure. Business Shield SME doesn't carry Employment Practices. I-select does. That is a correct, deliberate recommendation, not a coincidence.

The full mandatory set: Professional Indemnity / Tech E&O (Razorpay's payment APIs are the liability surface), D&O (VC-backed board, Series D investor scrutiny), Cyber (DPDP and CERT-In mandated), Crime/Fidelity (internal payment fraud at this transaction volume is a named risk category), and Employment Practices.

The fit score is 93%. The next-ranked alternative is Corporate Cover II at 90% — the engine shows that too, and the RM can have a conversation about when to upgrade.

Now — and this is new — let me show the RM what happens when they click Estimated Quote."

### Estimated Quote Tab

`[DEMO: Click the 'Estimated Quote' tab in the section nav.]`

"The quote panel asks for underwriting inputs before it calculates anything. Razorpay's exposure is significant — let's enter realistic SI values.

Enter:
- **cyber_limit_cr:** 15 (INR 15 crore cyber limit — appropriate for a PA processing this volume)
- **dno_limit_cr:** 10
- **pi_limit_cr:** 7.5
- **crime_limit_cr:** 5

`[Click Generate estimated quote.]`

The engine is showing a bundle-only indicative quote. It shows gross premium with GST, the SI per cover, the bundle discount, and — this is the important bit — a **referral flag: Cyber risk score is above 85, requires a control questionnaire before firm pricing.**

The RM doesn't need to memorise that underwriting rule. The engine surfaces it. They walk out of the Razorpay meeting with a number, a basis, and a specific next step. That's not a brochure. That's a sales motion."

---

## COMPANY 2: IDEAFORGE TECHNOLOGY — 2.5 minutes

### The Story

"Second meeting. ideaForge.

ideaForge went public on the NSE in 2023. They make the SWITCH series of UAVs — drones used by the Indian Army, NDRF, and infrastructure survey firms. They're one of the few Indian companies that holds a DGCA Type Certificate for UAVs. Their manufacturing and R&D happens out of Navi Mumbai — lab equipment, drone assemblies, testing rigs, sensitive electronics.

The RM who walks into this meeting without knowing about DGCA Drone Rule 44 is going to miss the most important thing about this account."

### Demo Inputs

`[DEMO: Clear form. New profile.]`

- **Sector:** Deeptech / AI / Robotics
- **Funding Stage:** Series A
- **Team Size:** 400
- **Physical assets:** Lab / R&D equipment ✓ · Drones / UAV equipment ✓
- **Hardware/software split:** 55% (hardware-heavy)
- **Regulatory:** DGCA / drone operations ✓
- **Operations:** Hardware / IoT

`[Click Analyse. Pause.]`

### What the Engine Returns — and Why

"The top risk scores: **Property: 74. IP Infringement: 78. Key Person: 70.**

The property score has two multipliers stacked on it: 1.3× for deeptech sector (they have lab equipment) plus 1.5× for hardware split above 60%. That pushes property exposure up sharply. Key person gets a 1.3× deeptech multiplier — three or four engineers hold the institutional knowledge for the drone architecture. If they leave, the IP walks out the door.

But the most important thing on this screen is not a risk score. It's the regulatory trigger.

**DGCA Drone Rules 2021, Rule 44 — fired.**

Rule 44 requires operators of Remotely Piloted Aircraft Systems above a certain payload class to carry insurance covering third-party liability arising from drone operations. ideaForge is a Type Certificate holder and an operator. This is not optional. It is a legal requirement. The engine flags **Drone RPAS** as a mandatory cover with a direct citation to the Civil Aviation ministry.

An RM who goes into this meeting and sells only a standard property package without Drone RPAS has left ideaForge exposed to a liability event that voids their policy. More importantly — that RM has created a claims problem for us.

The recommended bundle: **Industrial All Risk (IAR) Policy.**

IAR bundles Property All Risk, Business Interruption, Machinery Breakdown, and Electronic Equipment cover — exactly the asset structure of a hardware R&D company. The engine surfaces Drone RPAS as a mandatory standalone add-on where the bundle doesn't include it natively.

Base premium: INR 8 lakh. The account is specialty lines, not health and motor. The RM knows that before they sit down."

---

## COMPANY 3: BOAT (IMAGINE MARKETING) — 2 minutes

### The Story

"Third meeting. boAt.

Aman Gupta's brand. India's leading earwear company by unit volume — over 10 million units a year. They are Series C, direct-to-consumer, contract manufacturing through partners in Noida and Bengaluru. They're building their own manufacturing capability. 600+ direct employees, thousands more in the supply chain.

The risk surface here has shifted from the first two profiles. This is no longer a pure cyber and D&O conversation. boAt has physical assets, consumer product liability exposure, employer obligations across a large workforce, and a brand worth protecting.

Let's run it."

### Demo Inputs

`[DEMO: Clear form. New profile.]`

- **Sector:** D2C / Consumer Brands
- **Funding Stage:** Series B+ (closest to Series C)
- **Team Size:** 600
- **Physical assets:** Manufacturing plant / factory ✓ · Warehouse / fulfilment centre ✓
- **Hardware/software split:** 75%
- **Operations:** Hybrid
- **Regulatory:** Consumer protection obligations ✓

`[Click Analyse. Pause.]`

### What the Engine Returns — and Why

"Top scores: **Liability: 80. Reputation: 71. Governance & Fraud: 72.**

Liability is at 1.5× for D2C sector — the Consumer Protection Act 2019 and product liability exposure from consumer electronics sold at scale. An earphone defect claim or a battery safety event at this volume creates a class action surface. Reputation gets a 1.3× D2C multiplier and a 1.3× Series B stage loading — they're in the press constantly.

The trigger: **Consumer Protection Act 2019 — flagged. Product Liability recommended.**

The bundle recommendation: **Enterprise Secure Package Policy.**

Enterprise Secure was built for exactly this profile — Series B or Growth, manufacturing or hybrid operations, multi-dimensional risk. It bundles CGL I-Elite (Commercial General Liability), Cyber, D&O, Professional Indemnity, and Employers' Compensation. Base premium: INR 35 lakh. Margin: 14%.

And look at the graduation map below the recommendation. This is the lifecycle view. The engine shows where boAt came from — Business Shield SME at Seed, where they are now — Enterprise Secure at Series B — and where they're going — Corporate Cover II when they hit Growth and are looking at a potential listing.

That graduation map is a multi-year account relationship, not a single sale. The RM sees the full picture on one screen."

---

## CLOSE — 1 minute

"Three companies. Three completely different risk profiles. Three different bundle recommendations with specific regulatory citations backing each one.

Razorpay: I-select Liability Insurance — because at 3,500 employees and Series D scale, the engine correctly adds Employment Practices on top of Cyber, D&O, and PI/Tech E&O. It moved past the early-stage bundle because the profile demanded it.

ideaForge: Industrial All Risk with Drone RPAS — because DGCA Rule 44 is a legal requirement and an uncovered drone incident is a claims problem that starts with a compliance gap we created.

boAt: Enterprise Secure — because Consumer Protection Act product liability at scale, a workforce of thousands, and a board under investor scrutiny are three separate exposure streams that one package solves.

Each recommendation is deterministic, auditable, and traceable to the exact config weight, sector multiplier, and regulatory citation that produced it.

What we're asking for today is a 60-day pilot: 50 RMs, two cities, three startup clusters. We measure recommendation acceptance, quote click-through, and conversion. We need one thing from you to get started: endorsement to define the pilot design.

The numbers in the tool are already there. We just need to put them in front of the right people."

---

## APPENDIX — CHEAT SHEET FOR PRESENTER

### Company Input Reference

| Field | Razorpay | ideaForge | boAt |
|---|---|---|---|
| Sector | Fintech | Deeptech / AI / Robotics | D2C / Consumer Brands |
| Stage | Series D+ / Growth | Series A | Series B+ |
| Team size | 3500 | 400 | 600 |
| Physical assets | Office only | Lab + Drones | Factory + Warehouse |
| Hardware split | — | 55% | 75% |
| Data handled | Payments + KYC | — | — |
| Regulatory | RBI licensed + DPDP | DGCA / drones | Consumer protection |
| Operations | Digital-only | Hardware / IoT | Hybrid |

### Bundle Outcomes to Confirm

| Company | Expected Bundle | Key Trigger | Mandatory Covers |
|---|---|---|---|
| Razorpay | I-select Liability Insurance (93% fit) | DPDP + RBI Digital Lending | PI/Tech E&O, D&O, Cyber, Crime/Fidelity, Employment Practices |
| ideaForge | Industrial All Risk (IAR) | DGCA Drone Rule 44 | Drone RPAS (mandatory add-on) |
| boAt | Enterprise Secure Package Policy | Consumer Protection Act 2019 | CGL I-Elite, Cyber, D&O, PI, Employers' Comp |

### Regulatory Citations (ready to say out loud)

| Regulation | Company | What it requires | Max exposure |
|---|---|---|---|
| DPDP Act 2023 | Razorpay | 72-hr breach notification to DPB | INR 250 Cr per incident |
| CERT-In Directions 2022 | Razorpay | Mandatory government incident reporting | Operational suspension risk |
| RBI Digital Lending Directions 2025 | Razorpay | Operational resilience for licensed PAs | Licence suspension |
| Employment Practices (why 5th cover fires) | Razorpay | 3,500 employees + layoff history = wrongful termination / discrimination exposure | Personal director liability + litigation costs |
| DGCA Drone Rules 2021, Rule 44 | ideaForge | Third-party liability insurance for RPAS operators | Liability voidance |
| Consumer Protection Act 2019 | boAt | Product liability at consumer scale | Class action exposure |
| Companies Act 2013 | boAt (D&O) | Board and director fiduciary obligations | Personal director liability |

### Estimated Quote Demo (Razorpay only — do this on Estimated Quote tab)

Enter these values, then click **Generate estimated quote**:

```
cyber_limit_cr:    15
dno_limit_cr:      10
pi_limit_cr:       7.5
crime_limit_cr:    5
```

What to say: *"The quote is indicative until underwriting inputs are provided. Once I enter the SI values, the engine produces a cover-level breakdown with GST, bundle discount, and any referral flags. The referral flag for Razorpay will show a note that Cyber above 85 requires a control questionnaire. The RM now has a number and a next step, not just a name."*

---

*Script for: SVP, ICICI Lombard Commercial Lines · May 2026 · App at http://localhost:5174*  
*Product config: research_config v2026.05 · All premium figures are indicative estimates subject to underwriting.*
