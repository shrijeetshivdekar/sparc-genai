"""
competitor_catalog_expanded.py — SPARC competitive intelligence layer (EXPANDED)
=================================================================================
Unlimited version of competitor_catalog.py.

Contains 50 insurance products offered by ICICI Lombard's competitors and
global specialty insurers — NOT currently in the ICICI Lombard product catalog
defined in risk_engine.PRODUCT_CATALOG.

Providers sourced:
  Indian: Digit, Tata AIG, Bajaj Allianz, New India Assurance, National Insurance,
          Oriental Insurance, HDFC Ergo, Reliance General, SBI General
  Global: Munich Re, AIG, Chubb, Zurich, AXA, Beazley, Swiss Re, Lloyd's syndicates,
          Vouch, Kita / Oka, Armilla, Corvus, Coalition, CFC Underwriting

All products scored against the same 13 risk categories used in risk_engine.py.
Score formula (identical to recommend_products in risk_engine):
    score = sum(risk_scores[cat] * w for cat, w in weights.items()) / sum(weights.values())

Public API
----------
- COMPETITOR_PRODUCT_CATALOG       : dict[key, product_metadata]
- COMPETITOR_PRODUCT_RISK_MAP      : dict[key, dict[risk_category, weight]]
- COMPETITOR_SECTOR_RELEVANCE      : dict[key, set[sector]]
- COMPETITOR_TRIGGERS              : dict[key, predicate(StartupInput) -> bool]
- recommend_competitor_products(scores, sector, team_size, funding_stage,
                                 inp, top_n=5, min_score=45.0) -> list

Author: SPARC project (competitive intelligence module — expanded edition)
"""
from __future__ import annotations

from typing import Callable, Optional

# =============================================================================
# CLEANUP NOTE
# Removed from all active recommender dictionaries because they were rechecked
# and found to be clearly offered by ICICI Lombard/public ICICI wordings:
# event_insurance, cattle_livestock, crop_weather_parametric,
# surety_performance_bond, group_hospital_cash, group_critical_illness,
# trade_credit_enhanced, carrier_legal_liability, crisis_solution_kr,
# clinical_trial_indemnity_extended, comprehensive_product_recall.
# =============================================================================

# =============================================================================
# HELPER
# =============================================================================
def _stage_at_or_above(stage: str, threshold_stages: tuple) -> bool:
    order = ("Pre-seed", "Seed", "Series A", "Series B+", "Series C", "Pre-IPO / Listed")
    try:
        return order.index(stage) >= order.index(threshold_stages[0])
    except (ValueError, IndexError):
        return False

def _profile_text(inp) -> str:
    """Return optional descriptive fields as lower-case text for niche gates."""
    fields = (
        "sub_sector",
        "product_description",
        "business_model",
        "customer_type",
        "data_handled",
        "regulatory",
        "physical_assets",
        "biggest_fear",
    )
    parts: list[str] = []
    for field in fields:
        value = getattr(inp, field, "")
        if isinstance(value, (list, tuple, set)):
            parts.extend(str(item) for item in value)
        elif value is not None:
            parts.append(str(value))
    return " ".join(parts).lower()

def _mentions_any(inp, keywords: tuple[str, ...]) -> bool:
    text = _profile_text(inp)
    return any(keyword.lower() in text for keyword in keywords)

# =============================================================================
# COMPETITOR PRODUCT CATALOG — 50 corrected whitespace products NOT in ICICI Lombard's PRODUCT_CATALOG
# =============================================================================
COMPETITOR_PRODUCT_CATALOG = {

    # ── 1. AI / EMERGING TECH (7 products) ─────────────────────────────────────
    "ai_performance_liability": {
        "name": "AI Performance & Liability Insurance",
        "providers": "Munich Re aiSure · Armilla AI Performance Warranty (Lloyd's) · Vouch AI Insurance",
        "india_status": "Lloyd's-placeable today; aiSure live in 30+ countries, IRDAI Sandbox file expected 2026",
        "what_it_covers": (
            "Pays out when an AI/ML model underperforms, hallucinates, drifts, or makes "
            "biased decisions. Covers third-party legal defence for class actions, "
            "regulatory investigations under EU AI Act / MeitY AI Advisory / SGI Rules 2026, "
            "and IP-infringement claims arising from model training data."
        ),
        "icici_equivalent": "Cyber Liability + Professional Indemnity (Tech)",
        "icici_gap": (
            "ICICI Lombard's Cyber and PI policies expressly EXCLUDE AI-specific failures — "
            "hallucinations, model drift, algorithmic bias, training-data IP claims. "
            "aiSure / Armilla provide AFFIRMATIVE coverage with parametric-style triggers "
            "(e.g., model accuracy below a contracted threshold)."
        ),
        "best_for": "Deeptech / AI / Robotics, SaaS with AI features, Healthtech AI diagnostics, Fintech AI underwriting.",
    },
    "embedded_cyber_via_compliance": {
        "name": "Embedded Cyber Insurance via SaaS Compliance",
        "providers": "Vouch + Vanta (US) · Sprinto / Scrut Automation partnerships emerging in India",
        "india_status": "Vouch+Vanta US-only currently; Indian SaaS-compliance platforms piloting 2025-26",
        "what_it_covers": (
            "Cyber liability bundled inside a SaaS compliance platform (SOC 2 / ISO 27001 / "
            "DPDPA-readiness). Coverage automatically scales as the company adds controls; "
            "the compliance posture itself drives the premium and underwriting decision."
        ),
        "icici_equivalent": "Commercial Cyber Liability (standalone, broker-placed)",
        "icici_gap": (
            "ICICI Lombard's cyber is a standalone, manually-underwritten product. "
            "Vouch's embedded model auto-binds at SOC 2 attestation and adjusts limits "
            "with security posture — no broker friction, instant compliance evidence "
            "for enterprise procurement (Vanta-backed)."
        ),
        "best_for": "B2B SaaS, fintech selling to enterprises, AI startups doing SOC 2.",
    },
    "satellite_in_orbit_liability": {
        "name": "Satellite In-Orbit Third-Party Liability",
        "providers": "Tata AIG (first in India, May 2024) · AIG Aerospace · Marsh / Lloyd's syndicates",
        "india_status": "Filed by Tata AIG (TATSat policy); reinsurance via Lloyd's",
        "what_it_covers": (
            "Third-party liability for damage caused by an in-orbit satellite — collisions "
            "with other satellites, debris generation, deorbit failures impacting ground "
            "or aviation. Mandatory under IN-SPACe authorisation framework and US/EU "
            "regulatory regimes for any commercial space asset."
        ),
        "icici_equivalent": "None — ICICI Lombard does not file an aerospace product",
        "icici_gap": (
            "India has 250+ active spacetech startups (IN-SPACe, 2025) and a growing satellite "
            "constellation pipeline. Tata AIG holds the first-mover monopoly here; ICICI "
            "Lombard's drone product does not extend to space-tier risk."
        ),
        "best_for": "Spacetech, satellite comms / earth observation startups (Pixxel, Dhruva Space, Skyroot).",
    },
    "satellite_launch_insurance": {
        "name": "Launch Vehicle & Pre-Launch Satellite Insurance",
        "providers": "AIG Aerospace · Chubb Space · Lloyd's (Atrium, Beazley Aerospace)",
        "india_status": "Lloyd's-placeable into India; IN-SPACe mandates it for licensed launches",
        "what_it_covers": (
            "Covers the satellite and launch vehicle from pre-launch (integration, transport) "
            "through ascent to injection into orbit. Payable on launch failure, "
            "partial deployment, incorrect orbit, or total loss of vehicle and payload."
        ),
        "icici_equivalent": "None — no aerospace/launch product filed",
        "icici_gap": (
            "ISRO's launch manifest is now open to commercial operators (PSLV-C60 onwards). "
            "Each private satellite launch requires separate launch insurance as a launch "
            "contract condition — ICICI Lombard is entirely absent from this ₹500cr+ market."
        ),
        "best_for": "Spacetech (Skyroot, Agnikul, Pixxel), payload operators requiring IN-SPACe licence.",
    },
    "quantum_computing_liability": {
        "name": "Quantum Computing & Cryptographic Liability",
        "providers": "Beazley Quantum (Lloyd's) · Coalition · CFC Cyber Quantum extension",
        "india_status": "Lloyd's-placeable; India NQM (National Quantum Mission ₹6,003 cr) creates demand",
        "what_it_covers": (
            "Liability arising from cryptographic failure in quantum-enabled systems — "
            "premature decryption of existing data (harvest-now-decrypt-later attack), "
            "quantum algorithm IP theft, error-correction failures causing third-party loss. "
            "Includes post-quantum migration cost reimbursement."
        ),
        "icici_equivalent": "Cyber Liability (traditional, excludes quantum-specific perils)",
        "icici_gap": (
            "Standard cyber policies exclude cryptographic failure or classify it as 'design defect'. "
            "India's NQM and global quantum computing deployments (banking, pharma) create "
            "unique liability exposure that only quantum-specific extensions cover."
        ),
        "best_for": "Deeptech.Quantum, fintech with quantum-safe migration obligations, pharma quantum computing.",
    },
    "robotics_liability": {
        "name": "Autonomous Systems & Robotics Liability",
        "providers": "AIG Robotics Liability · Chubb Industrial Robotics · Munich Re Autonomous Systems",
        "india_status": "Broker-placed via Lloyd's; IRDAI Sandbox dialogue ongoing",
        "what_it_covers": (
            "Third-party bodily injury and property damage caused by autonomous robots, "
            "drones beyond VLOS, warehouse AGVs, surgical robots, and co-bots. "
            "Covers sensor failure, algorithm error, and cyberhijack scenarios. "
            "Includes product recall triggered by autonomous-system defect."
        ),
        "icici_equivalent": "Product Liability (broad, not autonomous-specific)",
        "icici_gap": (
            "Standard PL policies exclude 'autonomous decision-making' as product defect. "
            "Warehouse automation (Addverb, Aesthete), surgical robotics (SS Innovations), "
            "and AGV deployments need affirmative coverage — ICICI Lombard has none."
        ),
        "best_for": "Deeptech / AI / Robotics, Healthtech.MedDevice, logistics warehouse automation.",
    },
    "blockchain_custody_liability": {
        "name": "Digital Asset Custody & Blockchain Liability",
        "providers": "Coincover (Lloyd's) · Marsh Digital Assets · Aon Digital Asset Insurance",
        "india_status": "Lloyd's-placeable; VDA-platform licensing under PMLA creates demand",
        "what_it_covers": (
            "Hot and cold wallet custody losses — private key compromise, insider theft, "
            "smart-contract exploit, oracle manipulation. Covers custodian liability to "
            "asset holders and exchange protocol failure. Extends to NFT platform liability."
        ),
        "icici_equivalent": "Crime / Fidelity (traditional financial instruments only)",
        "icici_gap": (
            "Crime/Fidelity policies exclude digital assets and smart-contract risk. "
            "FIU-India registered VDA platforms (100+ as of 2025) and IFSCA-licensed "
            "crypto custodians require bespoke digital-asset coverage — an entirely "
            "uncovered ICICI gap."
        ),
        "best_for": "Fintech.Crypto_VDA, Web3 protocols, NFT marketplaces, DeFi platforms.",
    },

    # ── 2. CYBER / DATA (4 products) ─────────────────────────────────────────
    "active_cyber_response": {
        "name": "Active Cyber Response & Incident Management",
        "providers": "Coalition Active Insurance · Corvus Cyber · Beazley Breach Response · CFC Cyber",
        "india_status": "Beazley and CFC broker-placed via Lloyd's; Coalition US-first, India pilot 2026",
        "what_it_covers": (
            "Goes beyond breach indemnity — 24/7 incident response retainer pre-baked, "
            "forensic investigation, PR crisis management, regulatory notification cost, "
            "customer monitoring program, PCI-DSS fines, DPDPA penalty defence. "
            "Coalition scans the policyholder's attack surface continuously."
        ),
        "icici_equivalent": "Cyber Liability (passive indemnity, no pre-bound incident response)",
        "icici_gap": (
            "ICICI Lombard's cyber indemnifies AFTER a breach but doesn't include a "
            "24/7 IR retainer or continuous attack-surface monitoring. Coalition's model "
            "actively reduces breach probability — the policy itself is a security tool, "
            "not just a financial backstop."
        ),
        "best_for": "SaaS / Enterprise Software, Fintech, Healthtech handling PII/PHI data.",
    },
    "iot_device_liability": {
        "name": "IoT Device Liability Insurance",
        "providers": "AIG IoT Liability · Zurich IoT · Beazley Technology Products",
        "india_status": "Lloyd's-placeable; India's IoT market $9.28B by 2025 (Statista)",
        "what_it_covers": (
            "Manufacturer's liability for IoT devices causing physical harm through "
            "firmware failure, remote exploit, rogue firmware update, or sensor defect. "
            "Covers bodily injury, property damage, and recall cost for connected devices "
            "(smart meters, medical monitors, industrial sensors, consumer electronics)."
        ),
        "icici_equivalent": "Product Liability (broad, not connected-device-specific)",
        "icici_gap": (
            "Standard PL excludes cyber-induced physical damage (the 'silent cyber' gap). "
            "An IoT thermostat that causes a fire via hacked firmware is excluded under "
            "ICICI's PL. IoT-specific policies provide affirmative coverage for "
            "cyber-physical causation chains."
        ),
        "best_for": "Deeptech IoT, smart home D2C, industrial IoT, medtech connected devices.",
    },
    "supply_chain_cyber": {
        "name": "Supply Chain Cyber / Third-Party IT Risk",
        "providers": "Aon Supply Chain Cyber · Munich Re SCCR · Resilience Insurance",
        "india_status": "Lloyd's-placeable; RBI/SEBI vendor-risk guidelines creating demand",
        "what_it_covers": (
            "Losses stemming from a cyber incident at a vendor, SaaS provider, cloud "
            "provider, or payment processor. Covers business interruption from cloud "
            "outage (AWS/Azure/GCP), third-party software exploit cascading into the "
            "policyholder, and SolarWinds-style supply-chain attacks."
        ),
        "icici_equivalent": "Cyber Liability (typically excludes upstream third-party failure)",
        "icici_gap": (
            "Standard cyber policies define 'loss' from attacks on the insured's OWN systems. "
            "SaaS startups on cloud-native architectures are more exposed to vendor outage "
            "than to direct breach — a gap that supply-chain cyber specifically addresses."
        ),
        "best_for": "SaaS / Enterprise Software, Fintech on cloud, Healthtech with third-party integrations.",
    },
    "dpdpa_regulatory_defence": {
        "name": "DPDPA Regulatory Defence & Fine Coverage",
        "providers": "Beazley DPDPA Extension · CFC Data Protection · Digit Cyber (add-on under development)",
        "india_status": "DPDPA 2023 rules effective 2025; Beazley Lloyd's-placeable; Digit piloting add-on",
        "what_it_covers": (
            "Legal defence costs and penalties arising under India's Digital Personal Data "
            "Protection Act 2023 — DPBI investigation costs, ₹250cr penalty defence, "
            "customer notification program, and civil liability to data principals. "
            "Includes GDPR and CCPA coverage for cross-border data flows."
        ),
        "icici_equivalent": "Cyber Liability (DPDPA penalties often sub-limited or excluded)",
        "icici_gap": (
            "DPDPA imposes penalties up to ₹250 crore per breach category. Most legacy "
            "Indian cyber policies cap regulatory fines at ₹1-2 crore with IRDA-mandated "
            "exclusions. A DPDPA-specific extension with full ₹250cr defence limit is "
            "only available via Lloyd's right now."
        ),
        "best_for": "All sectors handling personal data — SaaS, Fintech, Healthtech, Edtech, D2C.",
    },

    # ── 3. CLIMATE / ENVIRONMENT (5 products) ────────────────────────────────
    "carbon_credit_invalidation": {
        "name": "Carbon Credit Invalidation / Non-Delivery Insurance",
        "providers": "Kita (Lloyd's coverholder) · Oka Insurance · CFC CORSIA Guarantee",
        "india_status": "Lloyd's-placeable; capacity ~£22.5M for 2025; no Indian filed product yet",
        "what_it_covers": (
            "Protects buyers, sellers, lenders and developers of voluntary carbon credits "
            "against project under-delivery, abandonment, fraud, host-country political "
            "risk, methodology revision, or buffer-pool depletion. Claims payable in cash "
            "OR replacement credits."
        ),
        "icici_equivalent": "None — entirely uncovered under ICICI Lombard's catalog",
        "icici_gap": (
            "Carbon credits are a $1bn+ Indian asset class by 2030. India has zero filed "
            "carbon-insurance product. Kita is the only Lloyd's-placeable option and "
            "Gold Standard mandates this cover for CORSIA Phase-1 credits."
        ),
        "best_for": "Cleantech / Climatetech selling carbon credits, agritech with soil-carbon projects.",
    },
    "parametric_weather_climate": {
        "name": "Parametric Weather / AQI / Heat Insurance",
        "providers": "Digit (AQI for Delhi NCR migrants Feb-2025; Heat for Gujarat women 2024) · AXA Climate · Swiss Re Earth Cover",
        "india_status": "Filed and live (Digit IRDAN158RP0020V01202324); IRDAI Use-and-File since 2024",
        "what_it_covers": (
            "Auto-triggers payouts when an objective weather index breaches a threshold — "
            "rainfall mm, temperature °C, AQI > 400, wind speed, or hail. Settles in days "
            "without traditional loss assessment. Compensates gig and construction workers "
            "for wage loss during pollution / heat bans."
        ),
        "icici_equivalent": "Property Fire / Property All Risk (loss-assessment based)",
        "icici_gap": (
            "ICICI Lombard's property products require a physical-damage trigger and lengthy "
            "loss assessment. Parametric pays automatically — ideal for gig wage-protection, "
            "agritech weather risk, and logistics suspension during AQI bans."
        ),
        "best_for": "Agritech, Logistics with gig workforce, Foodtech, Cleantech, D2C with monsoon supply chain.",
    },
    "pollution_legal_liability": {
        "name": "Pollution Legal Liability (PLL)",
        "providers": "Tata AIG Pollution Legal Liability Select · AIG EnviroPro · Chubb",
        "india_status": "Tata AIG filed; available in Indian market via direct + broker channels",
        "what_it_covers": (
            "First-party clean-up costs and third-party bodily injury / property damage from "
            "pollution — including gradual seepage, spills, and historical contamination. "
            "Triggered by CPCB notices and NGT orders."
        ),
        "icici_equivalent": "Public Liability (Industrial Risk) — but pollution typically excluded",
        "icici_gap": (
            "Standard PL policies carve out gradual pollution. The CPCB issued 1,000+ "
            "show-cause notices in FY24 and NGT levies are uncapped. Battery Waste Management "
            "Rules 2022 + EPR liability extends to D2C and EV; ICICI Lombard has no affirmative PLL."
        ),
        "best_for": "Cleantech, EV manufacturing, D2C with chemical/battery, Foodtech (CPCB ETP norms).",
    },
    "solar_module_insurance": {
        "name": "Solar Module / Renewable Energy Asset Insurance",
        "providers": "Tata AIG Solar Module · AIG Renewable Energy · AXA Climate",
        "india_status": "Tata AIG filed; Indian market via brokers (Howden, Marsh)",
        "what_it_covers": (
            "All-risk cover for solar PV modules, inverters, BESS, and tracking systems "
            "against transit damage, hail, hot-spots, micro-cracks, performance degradation "
            "beyond OEM warranty, and induced-current failures. Includes BI."
        ),
        "icici_equivalent": "Property All Risk + Machinery Breakdown (generic, low solar-specificity)",
        "icici_gap": (
            "Generic ICICI products underwrite solar at metal-asset rates; specialist PV "
            "policies underwrite at module-degradation rates — a 30-40% premium reduction "
            "for genuine solar assets with hot-spot and induced-current sub-limits."
        ),
        "best_for": "Cleantech / solar developers, EPC startups, distributed-energy aggregators.",
    },
    "offshore_energy_liability": {
        "name": "Offshore / Floating Energy Platform Insurance",
        "providers": "AIG Offshore Energy · Zurich Marine & Energy · Lloyd's Energy syndicates",
        "india_status": "Lloyd's-placeable; ONGC / GAIL JV vendors and offshore wind developers",
        "what_it_covers": (
            "Property and liability cover for floating platforms, offshore wind turbines, "
            "sub-sea cables, and FLNG / FPSO assets. Covers well blowout, collision, "
            "environmental clean-up under MARPOL, and third-party platform damage. "
            "Mandatory for ONGC vendor contracts in Block 98/2 area."
        ),
        "icici_equivalent": "None — ICICI does not file offshore energy",
        "icici_gap": (
            "India's offshore wind ambitions (Adani/NTPC/Sterlite) and deep-water oil "
            "services startups (MTAR, SilverLine) require offshore-specific coverage. "
            "Standard property/marine products exclude platform risk by endorsement."
        ),
        "best_for": "Cleantech.Offshore_Wind, Deeptech energy services, ocean-tech startups.",
    },
    "biodiversity_natural_capital": {
        "name": "Biodiversity / Natural Capital Risk Insurance",
        "providers": "AXA TNFD Risk · Swiss Re Nature-Based Solutions · Howden NCS",
        "india_status": "Emerging global product; SEBI BRSR Core mandates biodiversity disclosure",
        "what_it_covers": (
            "Covers financial losses arising from biodiversity-related regulatory action, "
            "ecosystem service failure, or deforestation-linked supply-chain disruption. "
            "Includes EUDR (EU Deforestation Regulation) compliance insurance and "
            "TNFD-disclosure liability for material misstatement of nature risk."
        ),
        "icici_equivalent": "None",
        "icici_gap": (
            "SEBI BRSR Core requires biodiversity impact disclosure from FY2024. EU DR "
            "cuts off Indian agri/food exports lacking deforestation-free certification. "
            "No Indian insurer has filed a nature-capital product — global demand is high."
        ),
        "best_for": "Agritech, Foodtech with EU exports, Cleantech (forestry), D2C natural/organic brands.",
    },

    # ── 4. FINANCIAL LINES / M&A (6 products) ────────────────────────────────
    "warranty_indemnity": {
        "name": "Warranty & Indemnity (W&I / Reps & Warranties) Insurance",
        "providers": "Tata AIG Buyer's & Seller's W&I · AIG · Liberty GTS · Marsh-placed Lloyd's",
        "india_status": "Filed Tata AIG; predominantly broker-placed (Trilegal, Marsh, Howden)",
        "what_it_covers": (
            "Indemnifies the buyer (or seller) for losses arising from breach of warranties "
            "or indemnities in an M&A purchase agreement. Replaces seller escrow/holdback. "
            "Covers tax indemnities, IP warranties, employment, and material-contract reps."
        ),
        "icici_equivalent": "None — ICICI Lombard does not file W&I",
        "icici_gap": (
            "Indian PE/VC exits increasingly demand clean-exit structures. W&I lets founders "
            "avoid 5-10% escrow tie-ups for 2-3 years. Series B+ acquirers now treat W&I "
            "as the default — ICICI Lombard cannot service this demand."
        ),
        "best_for": "Series B+ exit-track startups, cross-border flips, PE-backed roll-ups.",
    },
    "side_a_dno_edge": {
        "name": "Side-A D&O Edge (Directors-only Excess)",
        "providers": "Tata AIG Side-A Edge · AIG ExecutiveEdge · Chubb Side-A",
        "india_status": "Tata AIG filed in commercial financial lines",
        "what_it_covers": (
            "Pure Side-A protection for individual directors / officers when entity "
            "indemnification is unavailable (insolvency, bankruptcy, or hostile board). "
            "Sits excess of primary D&O with broader coverage, no Insured-vs-Insured exclusion."
        ),
        "icici_equivalent": "Directors & Officers Liability (combined ABC structure)",
        "icici_gap": (
            "Standard Indian D&O policies share limits across entity (Side B/C) and "
            "individuals (Side A). Side-A Edge gives founders a dedicated, ring-fenced "
            "layer — increasingly required by independent directors post-Byju's/BharatPe."
        ),
        "best_for": "Series A+ with independent directors, founders facing investor litigation risk.",
    },
    "bankers_indemnity_blanket": {
        "name": "Bankers Blanket Bond / Financial Institution Crime",
        "providers": "Tata AIG Bankers Indemnity · Digit FI Crime · AIG Financial Institutions",
        "india_status": "Tata AIG and Digit filed",
        "what_it_covers": (
            "Employee dishonesty, forgery, counterfeit currency, computer fraud, and "
            "transit loss for licensed financial institutions — NBFCs, Payment Aggregators, "
            "PPIs, Account Aggregators, and digital lending platforms. RBI mandates for "
            "Category-I and II payment system operators."
        ),
        "icici_equivalent": "Crime / Fidelity (limited FI scope)",
        "icici_gap": (
            "ICICI's Crime/Fidelity product is designed for commercial firms, not licensed "
            "financial institutions. RBI requires FIs to carry a blanket bond with "
            "specific FI-crime triggers — a compliance mandate ICICI's product does not satisfy."
        ),
        "best_for": "Fintech.NBFC, Fintech.Payment_Aggregator, Fintech.Digital_Lending.",
    },
    "ip_infringement_defence": {
        "name": "Intellectual Property Infringement Defence Insurance",
        "providers": "AIG IP Risk · Chubb IP Liability · Lloyd's IP syndicates (Brit, Beazley)",
        "india_status": "Lloyd's-placeable; India IP disputes up 300% since 2020 (IPO data)",
        "what_it_covers": (
            "Legal defence costs when the insured is sued for patent, trademark, copyright, "
            "or trade-secret infringement (abatement cover). Optionally covers pursuit "
            "of infringers (enforcement cover). Includes standard-essential patent "
            "claim defence and open-source licence violation allegations."
        ),
        "icici_equivalent": "PI (Tech) partially covers copyright in professional services — very limited",
        "icici_gap": (
            "SaaS and deeptech startups routinely face NPE (patent troll) and SEP claims. "
            "ICICI's PI product covers professional mistakes, not IP infringement as a "
            "product characteristic. Dedicated IP insurance is standard practice in the US/EU — "
            "an enormous gap for Indian startups with global IP exposure."
        ),
        "best_for": "Deeptech, SaaS / Enterprise Software, AI startups, Healthtech MedDevice, Gaming / Media.",
    },
    "tax_liability_insurance": {
        "name": "Tax Liability / Uncertain Tax Position (UTP) Insurance",
        "providers": "AIG Tax Liability · Liberty Tax Risk · Marsh Tax Insurance Group",
        "india_status": "Lloyd's-placeable; increasingly required in cross-border M&A",
        "what_it_covers": (
            "Covers crystallised tax risk — GAAR challenges, transfer-pricing adjustments, "
            "treaty abuse determinations, and structuring risk on flip/redomicile transactions. "
            "Pays the tax, penalties, and interest if ITAT or High Court rules against the insured. "
            "Frequently used in PE/VC exit structuring."
        ),
        "icici_equivalent": "None — tax risk is entirely uninsured under ICICI's catalog",
        "icici_gap": (
            "India-to-Singapore flips, ESOP structuring, and Mauritius-route "
            "investment restructuring all carry unquantified tax risk. AIF Category I/II "
            "funds increasingly require tax insurance as a condition of exit — ICICI absent."
        ),
        "best_for": "Series B+ startups with GIFT City / Mauritius / Singapore holding structures.",
    },

    # ── 5. PRODUCT / RECALL / LIFE SCIENCES (4 products) ─────────────────────
    "contaminated_product_insurance": {
        "name": "Contaminated Product Insurance (CPI)",
        "providers": "Tata AIG Contaminated Product · AIG Food Defence · Chubb",
        "india_status": "Tata AIG filed",
        "what_it_covers": (
            "Specifically for food and beverage brands — pays for product recall, "
            "crisis PR, and BI triggered by FSSAI contamination notice, media allegation "
            "(including social media), or voluntary pre-emptive withdrawal. Includes "
            "brand rehabilitation and extortion payment cover."
        ),
        "icici_equivalent": "Product Liability (third-party only; FSSAI-recall cost excluded)",
        "icici_gap": (
            "An Instagram viral contamination post can trigger a de-facto recall before "
            "FSSAI acts. Contaminated Product Insurance pays from the ALLEGATION stage — "
            "standard PL waits for a proven claim. For D2C food brands, this is their "
            "most likely large loss and ICICI provides no affirmative cover."
        ),
        "best_for": "Foodtech / Cloud Kitchen, D2C food & beverage, supplements, organic brands.",
    },
    "life_sciences_liability": {
        "name": "Life Sciences Liability Insurance",
        "providers": "Digit Life Science Liability (IRDAN158CP0006V01202324) · AIG Life Science",
        "india_status": "Digit filed in commercial lines",
        "what_it_covers": (
            "Combined liability cover for biotech / pharma / medical device startups — "
            "products liability, clinical trials liability, professional services, "
            "and contractual indemnities to CROs, hospitals, and pharma partners. "
            "Covers human-tissue handling, gene therapy, and SaMD failure modes."
        ),
        "icici_equivalent": "Clinical Trials + Product Liability (separate, fragmented)",
        "icici_gap": (
            "Indian biotech needs INTEGRATED cover — CDSCO trial liability + post-launch "
            "product liability + CRO contractual indemnity in ONE policy. ICICI offers "
            "these as 3 separate policies with coverage seams."
        ),
        "best_for": "Healthtech.MedDevice_SaMD, biotech, pharma R&D, gene-therapy startups.",
    },
    "single_project_pi": {
        "name": "Single Project Professional Indemnity",
        "providers": "Tata AIG Single-Project PI · AIG · Liberty",
        "india_status": "Tata AIG filed",
        "what_it_covers": (
            "PI cover that attaches to a single, identified project — typically a "
            "high-value engagement (₹50cr+ enterprise SaaS implementation, infra "
            "engineering, construction-tech). Limit ring-fenced to that project, "
            "no aggregation with other engagements."
        ),
        "icici_equivalent": "Professional Indemnity (Tech) — annual, aggregate limits",
        "icici_gap": (
            "When a startup signs a ₹100cr enterprise contract demanding ₹50cr PI limit, "
            "burning the annual policy on one client leaves all others uncovered. "
            "Single-Project PI is dedicated, doesn't erode the master policy."
        ),
        "best_for": "Deeptech engineering services, B2B SaaS with anchor enterprise contracts, infra-tech.",
    },
    "media_production_insurance": {
        "name": "Media Production Insurance",
        "providers": "Tata AIG Media Production · AIG MediaPro · Chubb",
        "india_status": "Tata AIG filed",
        "what_it_covers": (
            "Cast / crew injury, equipment loss, errors & omissions on content (defamation, "
            "IP, privacy), production delay (weather, illness), and post-production "
            "negative-loss cover."
        ),
        "icici_equivalent": "None — ICICI does not file a media-specific product",
        "icici_gap": (
            "Indian streaming + creator economy is $7B+ (2025). Standard property/PI "
            "policies don't underwrite production-specific perils — cast illness, "
            "weather-day delay, post-production negative loss."
        ),
        "best_for": "OTT, creator economy, advertising production, gaming-content studios.",
    },
    "my_online_space_d2c": {
        "name": "Online Business Combo (Cyber + Brand + Content + IP)",
        "providers": "Digit My Online Space Policy (IRDAN158RP0013V01202223)",
        "india_status": "Digit filed; designed specifically for D2C e-commerce sellers",
        "what_it_covers": (
            "Bundled cover for online sellers: cyber liability + IP infringement defence + "
            "advertising / marketing liability + product-photo / counterfeit-listing defence "
            "+ e-comm platform takedown costs."
        ),
        "icici_equivalent": "Cyber Liability (separate) + needs IP + Ad-Liab add-ons",
        "icici_gap": (
            "ICICI sells these as 3 separate policies. D2C startups operating on Amazon / "
            "Flipkart / Shopify need them BUNDLED at SKU-economics premium. My Online "
            "Space is the only purpose-built D2C combo at affordable Seed/Series A price."
        ),
        "best_for": "D2C / Consumer Brands selling on marketplaces, creator-economy stores.",
    },
    "esports_gaming_liability": {
        "name": "Esports & Gaming Tournament Liability",
        "providers": "AIG Esports · Beazley Gaming · Aon Esports Practice",
        "india_status": "Lloyd's-placeable; India esports market $140M (2025, Nodwin Gaming data)",
        "what_it_covers": (
            "Tournament cancellation / postponement, spectator liability, prize indemnity "
            "(if a prize pot is won in a guaranteed-prize format), player accident / injury, "
            "broadcast equipment loss, and streaming-platform outage business interruption. "
            "Covers both live events and online tournaments."
        ),
        "icici_equivalent": "Event Insurance (generic, misses esports-specific perils)",
        "icici_gap": (
            "ICICI's PL and event insurance don't contemplate prize-indemnity or streaming-"
            "platform BI triggers. Esports is a category unto itself and India's fastest-"
            "growing entertainment segment — no ICICI product fits."
        ),
        "best_for": "Gaming / Media / Content (esports platforms, tournament organisers, gaming studios).",
    },
    "legaltech_regulatory_defence": {
        "name": "Legaltech & Regulatory Defence Insurance",
        "providers": "AIG LegalTech PI · Beazley Legaltech · Chubb Emerging Technology",
        "india_status": "Lloyd's-placeable; BCI (Bar Council) compliance and LegalTech PI intersecting",
        "what_it_covers": (
            "Professional indemnity tailored for legal technology platforms — contract "
            "review AI, legalform automation, online dispute resolution. Covers advice "
            "given by the platform's AI where a user relies on it, BCI regulatory defence, "
            "and data protection violations in legal databases."
        ),
        "icici_equivalent": "Professional Indemnity (Tech) — excludes AI advice specifically",
        "icici_gap": (
            "Legaltech platforms (SpotDraft, Leegality, NyaayTech) face dual exposure: "
            "PI for wrong advice AND BCI regulatory risk for practising law without licence. "
            "Standard ICICI PI covers the first but excludes the second — a coverage seam "
            "specific to the sector."
        ),
        "best_for": "Legaltech, contract automation SaaS, online arbitration platforms.",
    },

    # ── 7. PROJECT / CONSTRUCTION / SURETY (4 products) ─────────────────────
    "builders_risk": {
        "name": "Builder's Risk Insurance",
        "providers": "Tata AIG Builder's Risk · AIG · Zurich India",
        "india_status": "Tata AIG filed",
        "what_it_covers": (
            "Property cover for buildings UNDER CONSTRUCTION — different from CAR/EAR. "
            "Pays for damage to the structure from fire, theft, vandalism, weather during "
            "build phase, plus soft costs (financing, professional fees, lost rent)."
        ),
        "icici_equivalent": "Contractors All Risk (CAR) — different scope, contractor-side",
        "icici_gap": (
            "CAR insures the CONTRACTOR; Builder's Risk insures the OWNER (the startup). "
            "For a cleantech building its own factory or a logistics startup building a "
            "fulfilment centre, CAR alone leaves the owner exposed during construction."
        ),
        "best_for": "Cleantech (factory build), Logistics (FC build), D2C (own manufacturing build).",
    },
    "specie_insurance": {
        "name": "Specie Insurance (High-Value Goods)",
        "providers": "Tata AIG Specie · AIG Specie · Lloyd's specie market",
        "india_status": "Tata AIG filed in specialty lines",
        "what_it_covers": (
            "All-risk cover for high-value goods that don't fit standard marine/property — "
            "bullion, fine art, jewellery in vault and exhibition, rare collectibles, "
            "prototype hardware, lab samples in transit, sealed consumer-electronics shipments. "
            "Covers theft, mysterious disappearance, infidelity."
        ),
        "icici_equivalent": "Marine Transit + Money Insurance (gaps for vault & exhibition)",
        "icici_gap": (
            "Marine Transit excludes mysterious-disappearance and vault risks; Money "
            "Insurance caps at ₹50L typically. Specie has no per-piece sublimits and "
            "covers vault, exhibition, and prototype shipments."
        ),
        "best_for": "Jewellery D2C, art-tech, deeptech sample/prototype shipping, mobile-supply-chain.",
    },
    "nuclear_liability_extension": {
        "name": "Nuclear Liability Extension (Civil Liability for Nuclear Damage Act)",
        "providers": "New India Assurance (CLNDA pool member) · GIC Re-backed pool · Lloyd's Nuclear",
        "india_status": "CLNDA 2010 pool mandated; New India is pool manager",
        "what_it_covers": (
            "Operator liability up to ₹1,500 crore under CLNDA 2010 for nuclear vendors, "
            "EPC contractors, and component suppliers with right-of-recourse liability. "
            "Includes suppliers of equipment to NPCIL / NuPower / BHAVINI under "
            "Section 46 recourse provisions."
        ),
        "icici_equivalent": "None — ICICI Lombard is not a CLNDA pool member",
        "icici_gap": (
            "CLNDA's Section 17(b) right of recourse can expose any supplier of defective "
            "equipment to nuclear-incident liability — even a small component manufacturer. "
            "Only pool-member insurers (New India, GIC Re) can underwrite this risk; "
            "ICICI Lombard cannot."
        ),
        "best_for": "Deeptech energy, advanced materials, precision manufacturing (nuclear component vendors).",
    },

    # ── 8. AGRI / RURAL / NICHE (5 products) ─────────────────────────────────
    "aquaculture_insurance": {
        "name": "Aquaculture Insurance",
        "providers": "Tata AIG Aquaculture · ICAR-CIBA piloted (NIA, Agriculture Insurance Co)",
        "india_status": "Tata AIG filed; PMFBY does NOT cover aquaculture",
        "what_it_covers": (
            "Stock mortality for shrimp / prawn / fin-fish farms against disease outbreak, "
            "water-quality crash, oxygen depletion, and natural perils. "
            "Includes feed-cost reimbursement for partial mortality."
        ),
        "icici_equivalent": "None — ICICI does not file an aquaculture product",
        "icici_gap": (
            "India is world's #2 shrimp producer ($5B+ exports). Aquaculture-tech startups "
            "(Aqgromalin, FishGrowth) need stock-mortality cover; ICICI doesn't file. "
            "Tata AIG holds the only commercial product in market."
        ),
        "best_for": "Agritech.Aquaculture, fisheries-tech, blue-economy startups.",
    },
    "pet_insurance_b2c": {
        "name": "Pet Insurance (B2C / Embedded)",
        "providers": "Digit Pet Insurance (IRDAN158RP0006V01202223) · Bajaj · Future Generali",
        "india_status": "Filed Digit + others",
        "what_it_covers": (
            "Veterinary OPD + IPD, surgery, third-party liability of pet (bites, property "
            "damage), and theft / loss. Sold standalone or embedded by petcare startups."
        ),
        "icici_equivalent": "None",
        "icici_gap": (
            "Indian pet care is a $1B+ market growing 25% YoY. Petcare D2Cs (Supertails, "
            "Heads Up For Tails, Wiggles) want EMBEDDED pet insurance at checkout — Digit "
            "already does this. ICICI Lombard cannot service this distribution play."
        ),
        "best_for": "Petcare D2C (embedded), petcare marketplaces, vet-tech platforms.",
    },
    "microinsurance_sachet": {
        "name": "Sachet / Micro-Insurance Products (Embedded & PAYG)",
        "providers": "Digit Sachet · Bajaj Allianz m-Insurance · New India Suraksha Micro",
        "india_status": "IRDAI Micro-Insurance Regulations 2015 + sandboxed products 2024",
        "what_it_covers": (
            "Ticket-size ₹10-500 insurance covers: screen-break, travel, transit damage, "
            "hospital cash, micro-life. Designed for embedding at consumer checkout — "
            "e-comm order protection, ride-hail trip cover, BNPL repayment protection, "
            "gig-worker daily accident cover. Pay-as-you-go (PAYG) or per-transaction billing."
        ),
        "icici_equivalent": "None — ICICI Lombard does not file micro/sachet products",
        "icici_gap": (
            "Fintech / D2C / Logistics embedded insurance requires ₹10 premium points at "
            "checkout — ICICI's minimum premium thresholds make this impossible. Sachet "
            "products are the distribution layer for India's 500M uninsured digital users. "
            "ICICI entirely absent from embedded micro-insurance rails."
        ),
        "best_for": "Fintech (BNPL, UPI wallets), D2C, Logistics gig-platform, Edtech.",
    },

    # ── 9. EMPLOYEE BENEFIT EXTENSIONS (5 products) ──────────────────────────
    "wage_protection_gig_parametric": {
        "name": "Wage-Protection Cover for Gig Workers (Parametric)",
        "providers": "Digit AQI Parametric (Delhi NCR 2025) · Digit Heat (Gujarat 2024) · Tata AIG Sandbox",
        "india_status": "Filed Digit; aligned with CoSS 2020 §114(4)",
        "what_it_covers": (
            "Parametric payout when work is regulator-suspended — AQI > 400 (construction "
            "ban), heat-wave > 45°C, monsoon delivery suspension. Pays gig worker direct "
            "wage equivalent without loss assessment."
        ),
        "icici_equivalent": "None — group PA and group health do not trigger on wage-loss",
        "icici_gap": (
            "Karnataka, Rajasthan, Telangana gig Acts + CoSS §114(4) require platforms to "
            "provide social security. Parametric is the only cover that fits the regulatory "
            "definition; ICICI absent."
        ),
        "best_for": "Logistics.Last_Mile_Delivery, Foodtech / Cloud Kitchen, any gig-platform aggregator.",
    },
    "mental_health_wellness_benefit": {
        "name": "Group Mental Health & Employee Assistance Programme (EAP) Cover",
        "providers": "Digit Mental Health Rider · Medi Assist EAP · Tata AIG Group Health extension",
        "india_status": "Mental Healthcare Act 2017 §21 requires insurer parity; IRDAI circular 2022",
        "what_it_covers": (
            "In-patient and out-patient mental health treatment (psychiatry, psychology, "
            "rehab) at parity with physical conditions. Includes a 24/7 EAP helpline, "
            "teleconsultation with psychologist, 6+ sessions per employee, and "
            "burnout programme. IRDAI 2022 mandates MH parity in group health policies."
        ),
        "icici_equivalent": "Group Health (MH sub-limited to ₹50k-₹1L, rarely at parity)",
        "icici_gap": (
            "ICICI Group Health typically sub-limits mental health at ₹50k vs. "
            "₹5-15L physical illness limits. The IRDAI 2022 circular mandates parity "
            "but enforcement is soft — a structured MH benefit from Digit/Medi Assist "
            "is the compliant path. Critical for SaaS startup hiring post-COVID burnout era."
        ),
        "best_for": "SaaS / Enterprise Software, Deeptech (high-pressure startups), Fintech, Legaltech.",
    },
    "esop_key_person_extension": {
        "name": "ESOP Vesting & Key Person Disruption Cover",
        "providers": "Aon ESOP Risk · Beazley Key Person Extended · AIG Executive Life",
        "india_status": "Lloyd's-placeable; SEBI ESOP regulations create structured need",
        "what_it_covers": (
            "Pays the startup a lump sum if a key employee leaves before an ESOP vesting "
            "cliff (accelerated by disability, death, or involuntary departure), enabling "
            "re-hiring and IP transfer costs. Extends standard key-person life to include "
            "ESOP dilution events and post-departure IP litigation costs."
        ),
        "icici_equivalent": "Key Person Life Insurance (death/TPD only, no ESOP disruption)",
        "icici_gap": (
            "ICICI Key Person Insurance pays on death or TPD. It does NOT cover the "
            "departure scenario — a key technical founder leaving before Series B vesting "
            "who takes critical IP and whose ESOP accelerates. This is the more common "
            "loss event for startups and entirely uninsured."
        ),
        "best_for": "Series A+ deeptech/SaaS where 1-2 individuals hold critical IP.",
    },

    # ── 10. FINTECH-SPECIFIC (4 products) ────────────────────────────────────
    "bnpl_credit_default_embedded": {
        "name": "BNPL / Embedded Credit Default Insurance",
        "providers": "Digit BNPL Cover · AIG Trade Credit (digital) · Atradius Digital",
        "india_status": "RBI FLDG ban 2023 creates demand; Digit piloting structured BNPL cover",
        "what_it_covers": (
            "Credit default protection for BNPL platforms on their loan book — covers "
            "first-loss default risk up to a specified tranche, enabling lending partner "
            "bank / NBFC to deploy capital without direct FLDG. "
            "Structured as financial guarantee or trade-credit wrapper."
        ),
        "icici_equivalent": "Trade Credit Insurance (supplier invoices, not consumer credit)",
        "icici_gap": (
            "ICICI's trade credit covers B2B invoice default. RBI's FLDG ban means BNPL "
            "platforms can no longer provide direct first-loss guarantees to NBFCs. "
            "An insurance-wrapped credit-enhancement product is the compliant alternative — "
            "and ICICI has not filed one."
        ),
        "best_for": "Fintech.BNPL, Fintech.Digital_Lending, embedded credit platforms.",
    },
    "payment_systems_disruption": {
        "name": "Payment Systems Operational Disruption Insurance",
        "providers": "AIG Payment Systems · Chubb FinTech · Beazley Financial Lines",
        "india_status": "RBI DPSS oversight + SEBI MTSS rules create demand; Lloyd's-placeable",
        "what_it_covers": (
            "Business interruption and third-party settlement losses arising from "
            "payment system failure — UPI outage, RuPay network downtime, RTGS/NEFT "
            "batch failure, and payment-gateway vendor outage. Covers settlement shortfalls, "
            "refund costs, customer compensation, and regulatory fines."
        ),
        "icici_equivalent": "Cyber Liability + BI (typical exclusion for payment network outage)",
        "icici_gap": (
            "NPCI's UPI downtime in 2023 caused ₹40cr+ merchant losses in a single day. "
            "Standard cyber BI excludes third-party infrastructure failure (cloud carve-out "
            "applies to payment networks too). Payment-systems disruption is a named-peril "
            "policy that fills this gap."
        ),
        "best_for": "Fintech (payment aggregators, wallets, UPI apps), D2C with high UPI dependency.",
    },
    "insurance_embedded_rails": {
        "name": "Insurance-as-a-Service / Embedded Insurance Rail Liability",
        "providers": "Shift Technology · Vouch Insurance API · Turtlemint API partner",
        "india_status": "IRDAI Corporate Agent / Intermediary licensing creates liability",
        "what_it_covers": (
            "E&O and regulatory liability for insurtech platforms acting as embedded "
            "insurance distributors — policy mis-statement to end customer, licensing "
            "violation (CA/Web Aggregator rules), commission override errors, and "
            "API failure causing missed coverage for the underlying customer."
        ),
        "icici_equivalent": "Professional Indemnity (generic, not distribution-specific)",
        "icici_gap": (
            "IRDAI Corporate Agent regulations expose the embedding platform (not just "
            "the insurer) to customer redressal forum liability. A platform embedding "
            "health or life policies via API has a DIFFERENT PI exposure than a software "
            "company — ICICI's generic PI doesn't capture it."
        ),
        "best_for": "Fintech (insurtech API platforms), HRtech with embedded insurance benefits.",
    },
    "comprehensive_political_violence": {
        "name": "Comprehensive Political Violence Insurance",
        "providers": "Digit Comprehensive Political Violence (IRDAN158CP0177V01201920) · Lloyd's PVT",
        "india_status": "Digit filed in commercial",
        "what_it_covers": (
            "Broader than terrorism — covers riots, strikes, civil commotion, malicious "
            "damage, sabotage, insurrection, civil war, rebellion, and coup d'état. "
            "Includes property damage AND BI from political-violence events."
        ),
        "icici_equivalent": "Standard Fire & Special Perils (terrorism via TPI pool only)",
        "icici_gap": (
            "TPI pool covers terrorism strictly defined; CPV broadens to riots / strikes / "
            "civil commotion (Delhi 2020 riots, Manipur 2023, Haldwani 2024). "
            "ICICI has no broader political violence product."
        ),
        "best_for": "D2C / Logistics with stores or FCs in tier-2/3 cities, border-state ops.",
    },
    "political_risk_expropriation": {
        "name": "Political Risk & Expropriation Insurance",
        "providers": "AIG Political Risk · Chubb Global Political Risk · Lloyd's PRI syndicates",
        "india_status": "Lloyd's-placeable; MIGA (World Bank) cover also available for FDI",
        "what_it_covers": (
            "Covers foreign investments against expropriation / nationalisation, currency "
            "inconvertibility, contract frustration, political violence, and licence "
            "revocation by host government. Relevant for Indian startups with operations "
            "in South/Southeast Asia, Africa, or Gulf markets."
        ),
        "icici_equivalent": "None — ICICI does not offer political risk cover",
        "icici_gap": (
            "Indian startups expanding to markets like Bangladesh, Vietnam, Nigeria, or "
            "Egypt face serious sovereign-action risk. ICICI has no product to protect "
            "overseas investments or cross-border contracts. Lloyd's PRI is the standard "
            "solution for Series B+ international expansions."
        ),
        "best_for": "Fintech, Logistics, Cleantech, D2C with Africa/SE Asia/MENA market entry.",
    },
    "export_credit_guarantee": {
        "name": "Export Credit Guarantee (beyond ECGC standard scope)",
        "providers": "ECGC (Govt) · Euler Hermes export credit · Coface export credit",
        "india_status": "ECGC is govt-owned; private market via Euler Hermes / Coface",
        "what_it_covers": (
            "Insures the exporter against buyer default and political risk on export "
            "receivables. Private-market products cover higher-risk markets, larger "
            "single-buyer concentrations, and structured finance export deals beyond "
            "ECGC's standard ₹2cr per buyer limit."
        ),
        "icici_equivalent": "Trade Credit (domestic focus)",
        "icici_gap": (
            "ICICI's trade credit does not include sovereign/buyer-country risk for exports. "
            "ECGC's standard product caps per-buyer at ₹2cr — insufficient for SaaS ARR "
            "contracts or D2C export deals in the ₹10cr+ range."
        ),
        "best_for": "SaaS / Enterprise Software (US/EU ARR), D2C export brands, Logistics (international freight).",
    },

    # ── 12. EVENTS / REAL ESTATE / MISC (4 products) ─────────────────────────
    "coop_society_liability": {
        "name": "Co-operative Society Management Committee Liability",
        "providers": "Digit Co-operative Society Mgmt Liability (IRDAN158RP0015V01202223)",
        "india_status": "Digit filed",
        "what_it_covers": (
            "D&O-style cover for managing committees of housing societies, dairy / "
            "producer cooperatives, fisheries cooperatives. Covers wrongful-act claims, "
            "regulatory action, and employment disputes specific to cooperative governance."
        ),
        "icici_equivalent": "D&O Liability — but priced for corporate boards, not cooperatives",
        "icici_gap": (
            "Producer cooperatives (FPOs / dairy / fisheries) are common JV partners for "
            "agritech / foodtech startups. Standard D&O is mis-rated for cooperative "
            "governance; this is the cooperative-specific filed product."
        ),
        "best_for": "Agritech FPO partnerships, dairy-tech, housing-society-tech, fisheries-tech.",
    },
    "real_estate_techbroker_liability": {
        "name": "Real Estate PropTech / Broker E&O Insurance",
        "providers": "Digit PropTech PI · AIG Real Estate E&O · Chubb Real Estate PI",
        "india_status": "Digit filed; RERA Section 9 mandates agent registration creating E&O need",
        "what_it_covers": (
            "Professional indemnity for RERA-registered real estate agents, PropTech "
            "platforms, and digital property marketplaces — errors in property listing, "
            "incorrect valuation advice, undisclosed defects, title misrepresentation, "
            "and NRI investment advisory errors."
        ),
        "icici_equivalent": "Professional Indemnity (generic, not RERA-specific)",
        "icici_gap": (
            "RERA creates a dedicated consumer-redressal forum for real estate. A PI "
            "claim via RERA has different procedural requirements than a civil suit — "
            "generic ICICI PI covers the financial indemnity but not the RERA-specific "
            "defence costs and regulatory representation."
        ),
        "best_for": "PropTech platforms (NoBroker, Housing.com, Square Yards), RERA-registered agents.",
    },
    "fleet_telematics_ubi": {
        "name": "Usage-Based / Telematics Fleet Insurance",
        "providers": "Digit UBI Fleet · HDFC Ergo Telematics · Bajaj Allianz Pay-How-You-Drive",
        "india_status": "Digit and HDFC Ergo filed; IRDAI sandbox approved UBI 2021",
        "what_it_covers": (
            "Motor fleet insurance priced on ACTUAL usage data — telematics-scored driving "
            "behaviour, kilometres driven, time-of-day risk, load weight. Premium can be "
            "20-40% lower than standard fleet policy. Includes OBD device, live tracking "
            "dashboard, and per-trip micro-policy embedding."
        ),
        "icici_equivalent": "Motor Fleet Insurance (standard, mileage-agnostic pricing)",
        "icici_gap": (
            "ICICI Motor Fleet charges actuarial averages regardless of how safely the "
            "startup's drivers actually behave. A logistics startup with low-risk routes "
            "overpays massively. Telematics-based UBI products from Digit / HDFC Ergo "
            "offer transparent, usage-fair pricing with live dashboards."
        ),
        "best_for": "Logistics / Mobility (fleet operators, EV fleet, last-mile delivery).",
    },

    # ── 13. EDTECH / HRTECH / LEGALTECH SPECIFIC (3 products) ────────────────
    "edtech_learning_platform_liability": {
        "name": "EdTech Learning Platform Liability & Content E&O",
        "providers": "AIG EdTech PI · Chubb Learning Platform · Beazley Media & PI combo",
        "india_status": "Lloyd's-placeable; NEP 2020 + CBSE-affiliated edtech creates demand",
        "what_it_covers": (
            "Errors in course content causing student harm (wrong medical advice in "
            "healthcare course, wrong financial advice in a CFA prep course, negligent "
            "career guidance). Covers defamation in instructor-created content, copyright "
            "in educational materials, and student data DPDPA compliance defence. "
            "Includes exam-platform proctoring liability."
        ),
        "icici_equivalent": "Professional Indemnity (generic, content-error rarely covered)",
        "icici_gap": (
            "EdTech content liability is a MEDIA + PROFESSIONAL INDEMNITY + DATA PRIVACY "
            "hybrid that no single ICICI product addresses. A wrong answer in a NEET prep "
            "question that causes a student to fail could generate a ₹5cr+ class action — "
            "ICICI PI would argue this is 'product' not 'professional service'."
        ),
        "best_for": "Edtech (Unacademy, Vedantu, BYJU clones), online certification platforms.",
    },
    "hrtech_background_check_liability": {
        "name": "HRTech / Staffing Platform E&O & Negligent Hiring Liability",
        "providers": "AIG StaffPro PI · Chubb Staffing E&O · Beazley Employment Practices combo",
        "india_status": "Lloyd's-placeable; Shops & Establishments Act + IT Act background-check liability",
        "what_it_covers": (
            "Errors in background verification causing a bad hire (fake degree check, "
            "criminal-record miss), negligent referral by the platform, breach of candidate "
            "DPDPA rights during screening, and discrimination claims in AI-assisted hiring. "
            "Also covers temp-staffing platform liability for temp employee actions."
        ),
        "icici_equivalent": "Professional Indemnity (Tech) — staffing-specific risks excluded",
        "icici_gap": (
            "HRtech platforms (Springworks, Keka, Darwinbox) that do BGV and offer "
            "AI-hiring tools face: (1) DPDPA candidate-data liability, (2) negligent-hire "
            "E&O when a mis-verified employee causes harm, (3) AI-bias discrimination claims. "
            "ICICI PI covers none of these affirmatively."
        ),
        "best_for": "HRtech, staffing platforms, background-verification (IDfy, AuthBridge).",
    },
    "legal_defence_fund_cover": {
        "name": "Regulatory Defence Fund / Legal Expenses Insurance",
        "providers": "DAS Legal Expenses · AIG Before-the-Event (BTE) · Aon LEI India",
        "india_status": "DAS operating in India via bancassurance; AIG LEI available",
        "what_it_covers": (
            "Pre-funded legal defence for contract disputes, employment tribunals, SEBI / "
            "CCI / TDSAT / NCLT proceedings, tax appeals, and startup-investor disputes. "
            "Pays solicitor fees from day 1, regardless of claim outcome. "
            "Includes ₹25L-₹1cr annual limit covering most startup litigation."
        ),
        "icici_equivalent": "None — ICICI Lombard does not file Legal Expenses Insurance",
        "icici_gap": (
            "Startups face constant low-to-mid value disputes: ₹10-50L contract claims, "
            "labour tribunal orders, SEBI AIF compliance challenges. None of ICICI's "
            "liability products cover the INSURED'S OWN legal costs proactively. "
            "A ₹1L annual LEI premium can cover ₹25L+ in legal fees — enormous ROI for "
            "early-stage startups."
        ),
        "best_for": "All sectors — universal need, especially Fintech (SEBI/RBI), SaaS (contract disputes).",
    },
}

# =============================================================================
# COMPETITOR PRODUCT RISK MAP
# Weights are 0.0 – 1.0 multipliers applied to each risk dimension.
# Score formula (matches recommend_products in risk_engine):
#     raw = sum(risk_scores[cat] * w for cat, w in weights.items())
#     score = raw / sum(weights.values())   # → 0-100 normalised
# =============================================================================
COMPETITOR_PRODUCT_RISK_MAP = {
    # AI / Emerging tech
    "ai_performance_liability": {
        "Liability Risk": 0.7, "Cyber Technical Risk": 0.4,
        "IP Infringement Risk": 0.6, "Regulatory Compliance Risk": 0.7,
        "Policy Velocity Risk": 0.6,
    },
    "embedded_cyber_via_compliance": {
        "Cyber Technical Risk": 0.9, "Data Privacy Risk": 0.7,
        "Regulatory Compliance Risk": 0.4,
    },
    "satellite_in_orbit_liability": {
        "Liability Risk": 0.8, "Property Risk": 0.6,
        "Regulatory Compliance Risk": 0.5, "Geopolitical Risk": 0.3,
    },
    "satellite_launch_insurance": {
        "Property Risk": 0.9, "Liability Risk": 0.7,
        "Regulatory Compliance Risk": 0.4,
    },
    "quantum_computing_liability": {
        "Cyber Technical Risk": 0.7, "IP Infringement Risk": 0.5,
        "Regulatory Compliance Risk": 0.6, "Liability Risk": 0.5,
    },
    "robotics_liability": {
        "Liability Risk": 0.9, "Property Risk": 0.4,
        "Regulatory Compliance Risk": 0.4, "Cyber Technical Risk": 0.3,
    },
    "blockchain_custody_liability": {
        "Cyber Technical Risk": 0.7, "Governance & Fraud Risk": 0.8,
        "Regulatory Compliance Risk": 0.6, "Liability Risk": 0.4,
    },
    # Cyber / Data
    "active_cyber_response": {
        "Cyber Technical Risk": 1.0, "Data Privacy Risk": 0.8,
        "Regulatory Compliance Risk": 0.5, "Reputation Risk": 0.5,
    },
    "iot_device_liability": {
        "Liability Risk": 0.8, "Cyber Technical Risk": 0.6,
        "Property Risk": 0.4, "Regulatory Compliance Risk": 0.4,
    },
    "supply_chain_cyber": {
        "Cyber Technical Risk": 0.8, "Liability Risk": 0.5,
        "Regulatory Compliance Risk": 0.4,
    },
    "dpdpa_regulatory_defence": {
        "Data Privacy Risk": 1.0, "Regulatory Compliance Risk": 0.8,
        "Cyber Technical Risk": 0.4, "Reputation Risk": 0.4,
    },
    # Climate / Environment
    "carbon_credit_invalidation": {
        "ESG & Climate Risk": 1.0, "Regulatory Compliance Risk": 0.5,
        "Liability Risk": 0.3, "Geopolitical Risk": 0.4,
    },
    "parametric_weather_climate": {
        "ESG & Climate Risk": 1.0, "Property Risk": 0.4,
        "Gig & Labour Risk": 0.5, "Policy Velocity Risk": 0.3,
    },
    "pollution_legal_liability": {
        "ESG & Climate Risk": 0.8, "Liability Risk": 0.6,
        "Regulatory Compliance Risk": 0.6,
    },
    "solar_module_insurance": {
        "Property Risk": 0.9, "ESG & Climate Risk": 0.4,
    },
    "offshore_energy_liability": {
        "Property Risk": 0.8, "Liability Risk": 0.7,
        "ESG & Climate Risk": 0.5, "Regulatory Compliance Risk": 0.4,
    },
    "biodiversity_natural_capital": {
        "ESG & Climate Risk": 0.9, "Regulatory Compliance Risk": 0.6,
        "Reputation Risk": 0.5, "Geopolitical Risk": 0.3,
    },
    # Financial Lines / M&A
    "warranty_indemnity": {
        "Liability Risk": 0.7, "Governance & Fraud Risk": 0.5,
        "Tax_TP Risk": 0.4, "Regulatory Compliance Risk": 0.3,
    },
    "side_a_dno_edge": {
        "Liability Risk": 0.6, "Governance & Fraud Risk": 0.7,
        "Key Person Risk": 0.4, "Regulatory Compliance Risk": 0.4,
    },
    "bankers_indemnity_blanket": {
        "Cyber Technical Risk": 0.6, "Governance & Fraud Risk": 0.8,
        "Regulatory Compliance Risk": 0.5,
    },
    "ip_infringement_defence": {
        "IP Infringement Risk": 1.0, "Liability Risk": 0.6,
        "Regulatory Compliance Risk": 0.3,
    },
    "tax_liability_insurance": {
        "Tax_TP Risk": 1.0, "Regulatory Compliance Risk": 0.5,
        "Governance & Fraud Risk": 0.3,
    },
    # Product / Recall / Life Sciences
    "contaminated_product_insurance": {
        "Liability Risk": 0.7, "Reputation Risk": 0.8,
        "Regulatory Compliance Risk": 0.4,
    },
    "life_sciences_liability": {
        "Liability Risk": 0.9, "Regulatory Compliance Risk": 0.7,
        "IP Infringement Risk": 0.4,
    },
    "single_project_pi": {
        "Liability Risk": 0.9, "Key Person Risk": 0.2,
    },
    "media_production_insurance": {
        "Property Risk": 0.5, "Liability Risk": 0.5,
        "IP Infringement Risk": 0.6, "Reputation Risk": 0.4,
    },
    "my_online_space_d2c": {
        "Cyber Technical Risk": 0.6, "IP Infringement Risk": 0.6,
        "Liability Risk": 0.4, "Reputation Risk": 0.5,
    },
    "esports_gaming_liability": {
        "Liability Risk": 0.6, "Property Risk": 0.4,
        "Reputation Risk": 0.5, "IP Infringement Risk": 0.3,
    },
    "legaltech_regulatory_defence": {
        "Liability Risk": 0.8, "Regulatory Compliance Risk": 0.7,
        "Data Privacy Risk": 0.4,
    },
    # Project / construction / surety
    "builders_risk": {
        "Property Risk": 0.9, "Liability Risk": 0.3,
    },
    "specie_insurance": {
        "Property Risk": 0.7, "Governance & Fraud Risk": 0.4,
    },
    "nuclear_liability_extension": {
        "Liability Risk": 0.9, "Regulatory Compliance Risk": 0.8,
        "Geopolitical Risk": 0.3,
    },
    # Agri / rural
    "aquaculture_insurance": {
        "Property Risk": 0.7, "ESG & Climate Risk": 0.5,
    },
    "pet_insurance_b2c": {
        "Liability Risk": 0.4, "Property Risk": 0.3,
        "Reputation Risk": 0.3,
    },
    "microinsurance_sachet": {
        "Liability Risk": 0.3, "Gig & Labour Risk": 0.4,
        "Regulatory Compliance Risk": 0.4,
    },
    # Employee benefit
    "wage_protection_gig_parametric": {
        "Gig & Labour Risk": 1.0, "Regulatory Compliance Risk": 0.5,
        "ESG & Climate Risk": 0.3, "Reputation Risk": 0.3,
    },
    "mental_health_wellness_benefit": {
        "Key Person Risk": 0.5, "Gig & Labour Risk": 0.4,
        "Regulatory Compliance Risk": 0.3, "Reputation Risk": 0.3,
    },
    "esop_key_person_extension": {
        "Key Person Risk": 0.9, "IP Infringement Risk": 0.4,
        "Governance & Fraud Risk": 0.3,
    },
    # Fintech-specific
    "bnpl_credit_default_embedded": {
        "Liability Risk": 0.5, "Regulatory Compliance Risk": 0.7,
        "Governance & Fraud Risk": 0.5,
    },
    "payment_systems_disruption": {
        "Cyber Technical Risk": 0.7, "Liability Risk": 0.5,
        "Regulatory Compliance Risk": 0.6, "Reputation Risk": 0.4,
    },
    "insurance_embedded_rails": {
        "Liability Risk": 0.6, "Regulatory Compliance Risk": 0.8,
        "Data Privacy Risk": 0.4,
    },
    "comprehensive_political_violence": {
        "Property Risk": 0.6, "Geopolitical Risk": 0.7,
        "Liability Risk": 0.3,
    },
    "political_risk_expropriation": {
        "Geopolitical Risk": 1.0, "Property Risk": 0.5,
        "Regulatory Compliance Risk": 0.4,
    },
    "export_credit_guarantee": {
        "Geopolitical Risk": 0.7, "Liability Risk": 0.4,
        "Regulatory Compliance Risk": 0.3,
    },
    # Events / real estate / misc
    "coop_society_liability": {
        "Liability Risk": 0.6, "Governance & Fraud Risk": 0.5,
        "Regulatory Compliance Risk": 0.4,
    },
    "real_estate_techbroker_liability": {
        "Liability Risk": 0.7, "Regulatory Compliance Risk": 0.6,
        "Data Privacy Risk": 0.3,
    },
    "fleet_telematics_ubi": {
        "Property Risk": 0.7, "Liability Risk": 0.4,
        "Gig & Labour Risk": 0.3, "ESG & Climate Risk": 0.2,
    },
    # EdTech / HRtech / Legaltech
    "edtech_learning_platform_liability": {
        "Liability Risk": 0.7, "IP Infringement Risk": 0.5,
        "Data Privacy Risk": 0.5, "Reputation Risk": 0.4,
    },
    "hrtech_background_check_liability": {
        "Liability Risk": 0.7, "Data Privacy Risk": 0.6,
        "Regulatory Compliance Risk": 0.5, "Reputation Risk": 0.3,
    },
    "legal_defence_fund_cover": {
        "Liability Risk": 0.5, "Regulatory Compliance Risk": 0.7,
        "Governance & Fraud Risk": 0.3,
    },
}

# =============================================================================
# SECTOR RELEVANCE
# =============================================================================
COMPETITOR_SECTOR_RELEVANCE = {
    "ai_performance_liability": {
        "Deeptech / AI / Robotics", "SaaS / Enterprise Software",
        "Healthtech", "Fintech", "HRtech", "Legaltech", "Edtech",
    },
    "embedded_cyber_via_compliance": {
        "SaaS / Enterprise Software", "Fintech", "Healthtech",
        "HRtech", "Edtech", "Legaltech",
    },
    "satellite_in_orbit_liability": {
        "Deeptech / AI / Robotics",
    },
    "satellite_launch_insurance": {
        "Deeptech / AI / Robotics",
    },
    "quantum_computing_liability": {
        "Deeptech / AI / Robotics", "Fintech", "Healthtech",
        "SaaS / Enterprise Software",
    },
    "robotics_liability": {
        "Deeptech / AI / Robotics", "Healthtech", "Logistics / Mobility",
        "D2C / Consumer Brands",
    },
    "blockchain_custody_liability": {
        "Fintech",
    },
    "active_cyber_response": {
        "SaaS / Enterprise Software", "Fintech", "Healthtech",
        "HRtech", "Edtech", "Legaltech", "D2C / Consumer Brands",
    },
    "iot_device_liability": {
        "Deeptech / AI / Robotics", "D2C / Consumer Brands",
        "Healthtech", "Cleantech / Climatetech",
    },
    "supply_chain_cyber": {
        "SaaS / Enterprise Software", "Fintech", "Healthtech",
        "Logistics / Mobility",
    },
    "dpdpa_regulatory_defence": {
        "SaaS / Enterprise Software", "Fintech", "Healthtech",
        "Edtech", "D2C / Consumer Brands", "HRtech", "Legaltech",
    },
    "carbon_credit_invalidation": {
        "Cleantech / Climatetech", "Agritech",
    },
    "parametric_weather_climate": {
        "Agritech", "Logistics / Mobility", "Foodtech / Cloud Kitchen",
        "Cleantech / Climatetech", "D2C / Consumer Brands",
    },
    "pollution_legal_liability": {
        "Cleantech / Climatetech", "D2C / Consumer Brands",
        "Foodtech / Cloud Kitchen", "Logistics / Mobility",
    },
    "solar_module_insurance": {
        "Cleantech / Climatetech",
    },
    "offshore_energy_liability": {
        "Cleantech / Climatetech", "Deeptech / AI / Robotics",
    },
    "biodiversity_natural_capital": {
        "Agritech", "Foodtech / Cloud Kitchen", "Cleantech / Climatetech",
        "D2C / Consumer Brands",
    },
    "warranty_indemnity": {
        "SaaS / Enterprise Software", "Fintech", "Healthtech",
        "D2C / Consumer Brands", "Deeptech / AI / Robotics", "Edtech",
        "Cleantech / Climatetech", "Logistics / Mobility",
        "Foodtech / Cloud Kitchen", "Gaming / Media / Content",
        "HRtech", "Legaltech", "Agritech",
    },
    "side_a_dno_edge": {
        "SaaS / Enterprise Software", "Fintech", "Healthtech",
        "D2C / Consumer Brands", "Deeptech / AI / Robotics", "Edtech",
        "Cleantech / Climatetech", "Logistics / Mobility",
        "Foodtech / Cloud Kitchen", "Gaming / Media / Content",
    },
    "bankers_indemnity_blanket": {
        "Fintech",
    },
    "ip_infringement_defence": {
        "Deeptech / AI / Robotics", "SaaS / Enterprise Software",
        "Healthtech", "Gaming / Media / Content", "Fintech", "Legaltech",
    },
    "tax_liability_insurance": {
        "SaaS / Enterprise Software", "Fintech", "Healthtech",
        "D2C / Consumer Brands", "Deeptech / AI / Robotics",
        "Cleantech / Climatetech",
    },
    "contaminated_product_insurance": {
        "Foodtech / Cloud Kitchen", "D2C / Consumer Brands",
    },
    "life_sciences_liability": {
        "Healthtech",
    },
    "single_project_pi": {
        "SaaS / Enterprise Software", "Deeptech / AI / Robotics",
        "Cleantech / Climatetech", "Legaltech",
    },
    "media_production_insurance": {
        "Gaming / Media / Content",
    },
    "my_online_space_d2c": {
        "D2C / Consumer Brands", "Foodtech / Cloud Kitchen",
        "Gaming / Media / Content",
    },
    "esports_gaming_liability": {
        "Gaming / Media / Content",
    },
    "legaltech_regulatory_defence": {
        "Legaltech", "SaaS / Enterprise Software",
    },
    "builders_risk": {
        "Cleantech / Climatetech", "Logistics / Mobility",
        "D2C / Consumer Brands", "Foodtech / Cloud Kitchen",
    },
    "specie_insurance": {
        "D2C / Consumer Brands", "Deeptech / AI / Robotics",
    },
    "nuclear_liability_extension": {
        "Deeptech / AI / Robotics", "Cleantech / Climatetech",
    },
    "aquaculture_insurance": {
        "Agritech",
    },
    "pet_insurance_b2c": {
        "D2C / Consumer Brands", "Healthtech",
    },
    "microinsurance_sachet": {
        "Fintech", "D2C / Consumer Brands", "Logistics / Mobility",
        "Edtech",
    },
    "wage_protection_gig_parametric": {
        "Logistics / Mobility", "Foodtech / Cloud Kitchen",
    },
    "mental_health_wellness_benefit": {
        "SaaS / Enterprise Software", "Fintech", "Deeptech / AI / Robotics",
        "Legaltech", "Healthtech", "HRtech",
    },
    "esop_key_person_extension": {
        "SaaS / Enterprise Software", "Deeptech / AI / Robotics",
        "Fintech", "Healthtech",
    },
    "bnpl_credit_default_embedded": {
        "Fintech",
    },
    "payment_systems_disruption": {
        "Fintech", "D2C / Consumer Brands", "Logistics / Mobility",
    },
    "insurance_embedded_rails": {
        "Fintech", "HRtech",
    },
    "comprehensive_political_violence": {
        "D2C / Consumer Brands", "Logistics / Mobility",
        "Foodtech / Cloud Kitchen", "Cleantech / Climatetech",
    },
    "political_risk_expropriation": {
        "Fintech", "Logistics / Mobility", "Cleantech / Climatetech",
        "D2C / Consumer Brands", "SaaS / Enterprise Software",
    },
    "export_credit_guarantee": {
        "SaaS / Enterprise Software", "Logistics / Mobility",
        "D2C / Consumer Brands",
    },
    "coop_society_liability": {
        "Agritech", "Foodtech / Cloud Kitchen",
    },
    "real_estate_techbroker_liability": {
        "SaaS / Enterprise Software",  # PropTech sits here
    },
    "fleet_telematics_ubi": {
        "Logistics / Mobility",
    },
    "edtech_learning_platform_liability": {
        "Edtech",
    },
    "hrtech_background_check_liability": {
        "HRtech",
    },
    "legal_defence_fund_cover": {
        "SaaS / Enterprise Software", "Fintech", "Healthtech",
        "Legaltech", "HRtech", "Edtech",
        "Deeptech / AI / Robotics", "D2C / Consumer Brands",
    },
}

# =============================================================================
# TRIGGERS — input-field predicates that gate product visibility
# =============================================================================
COMPETITOR_TRIGGERS: dict[str, Callable] = {
    "ai_performance_liability":
        lambda inp: bool(getattr(inp, "ai_in_product", False)),
    "embedded_cyber_via_compliance":
        lambda inp: inp.sector in {"SaaS / Enterprise Software", "Fintech", "Healthtech"}
                    and inp.team_size >= 10,
    "satellite_in_orbit_liability":
        lambda inp: "Space" in (getattr(inp, "sub_sector", "") or "")
                    or (getattr(inp, "hardware_software_split", 0.0) >= 0.50
                        and inp.sector == "Deeptech / AI / Robotics"),
    "satellite_launch_insurance":
        lambda inp: "Space" in (getattr(inp, "sub_sector", "") or ""),
    "quantum_computing_liability":
        lambda inp: "Quantum" in (getattr(inp, "sub_sector", "") or "")
                    or _mentions_any(inp, ("quantum", "cryptographic", "post-quantum")),
    "robotics_liability":
        lambda inp: "Robot" in (getattr(inp, "sub_sector", "") or "")
                    or (
                        getattr(inp, "hardware_software_split", 0.0) >= 0.30
                        and _mentions_any(inp, (
                            "robot", "robotics", "autonomous", "drone",
                            "industrial automation", "machine vision",
                        ))
                    ),
    "blockchain_custody_liability":
        lambda inp: getattr(inp, "rbi_registration", None) in {"PA", "PPI"}
                    or "Crypto" in (getattr(inp, "sub_sector", "") or "")
                    or "Web3" in (getattr(inp, "sub_sector", "") or ""),
    "active_cyber_response":
        lambda inp: inp.team_size >= 10
                    or _stage_at_or_above(inp.funding_stage, ("Series A",)),
    "iot_device_liability":
        lambda inp: "IoT" in (getattr(inp, "sub_sector", "") or "")
                    or (
                        getattr(inp, "hardware_software_split", 0.0) >= 0.30
                        and _mentions_any(inp, (
                            "iot", "connected device", "sensor", "telematics",
                            "wearable", "smart device", "electronics",
                        ))
                    ),
    "supply_chain_cyber":
        lambda inp: _stage_at_or_above(inp.funding_stage, ("Series A",))
                    and inp.team_size >= 20,
    "dpdpa_regulatory_defence":
        lambda inp: _stage_at_or_above(inp.funding_stage, ("Seed",))
                    and (
                        getattr(inp, "data_sensitivity", "") in {"Medium", "High"}
                        or _mentions_any(inp, (
                            "personal data", "customer data", "health", "medical",
                            "payments", "financial", "employee", "children",
                            "minors", "location", "biometric", "dpdpa",
                        ))
                    ),
    "carbon_credit_invalidation":
        lambda inp: getattr(inp, "sub_sector", "") in {
            "Cleantech.Carbon_Markets", "Agritech.Carbon_Soil",
        } or (inp.sector == "Cleantech / Climatetech"
              and getattr(inp, "export_eu_pct", 0.0) > 0.05),
    "parametric_weather_climate":
        lambda inp: True,   # universal within relevant sectors
    "pollution_legal_liability":
        lambda inp: getattr(inp, "hardware_software_split", 0.0) >= 0.30
                    or inp.sector in {"Cleantech / Climatetech", "Foodtech / Cloud Kitchen"},
    "solar_module_insurance":
        lambda inp: "Solar" in (getattr(inp, "sub_sector", "") or "")
                    or (inp.sector == "Cleantech / Climatetech"
                        and getattr(inp, "hardware_software_split", 0.0) >= 0.40),
    "offshore_energy_liability":
        lambda inp: "Offshore" in (getattr(inp, "sub_sector", "") or "")
                    or "Wind" in (getattr(inp, "sub_sector", "") or ""),
    "biodiversity_natural_capital":
        lambda inp: getattr(inp, "export_eu_pct", 0.0) > 0.10
                    or inp.sector in {"Agritech", "Foodtech / Cloud Kitchen"},
    "warranty_indemnity":
        lambda inp: _stage_at_or_above(inp.funding_stage, ("Series B+",))
                    and _mentions_any(inp, (
                        "m&a", "merger", "acquisition", "acquire", "buyer",
                        "seller", "exit", "roll-up", "rollup", "due diligence",
                        "warranty", "reps", "representations",
                    )),
    "side_a_dno_edge":
        lambda inp: _stage_at_or_above(inp.funding_stage, ("Series A",))
                    and bool(getattr(inp, "institutional_investors_on_board", False)),
    "bankers_indemnity_blanket":
        lambda inp: getattr(inp, "rbi_registration", None) in {"NBFC", "PA", "PPI", "AA"},
    "ip_infringement_defence":
        lambda inp: bool(getattr(inp, "ai_in_product", False))
                    or getattr(inp, "b2b_pct", 0.0) >= 0.60
                    or getattr(inp, "ip_portfolio_filed", False),
    "tax_liability_insurance":
        lambda inp: _stage_at_or_above(inp.funding_stage, ("Series B+",))
                    and (
                        getattr(inp, "holdco_domicile", "India") != "India"
                        or getattr(inp, "export_eu_pct", 0.0) > 0.10
                        or _mentions_any(inp, (
                            "tax", "transfer pricing", "gaar", "gift city",
                            "mauritius", "singapore", "cross-border",
                            "holding company", "exit", "restructuring",
                        ))
                    ),
    "contaminated_product_insurance":
        lambda inp: inp.sector in {"Foodtech / Cloud Kitchen", "D2C / Consumer Brands"},
    "life_sciences_liability":
        lambda inp: inp.sector == "Healthtech"
                    or _mentions_any(inp, (
                        "biotech", "pharma", "clinical trial", "medical device",
                        "gene therapy", "samd", "cdsco", "life science",
                        "diagnostics", "cro",
                    )),
    "single_project_pi":
        lambda inp: getattr(inp, "b2b_pct", 0.5) >= 0.70
                    and _stage_at_or_above(inp.funding_stage, ("Series A",)),
    "media_production_insurance":
        lambda inp: getattr(inp, "sub_sector", "") in {
            "Gaming.OTT", "Gaming.Creator_Economy",
        } or inp.sector == "Gaming / Media / Content",
    "my_online_space_d2c":
        lambda inp: inp.sector in {"D2C / Consumer Brands", "Foodtech / Cloud Kitchen"},
    "esports_gaming_liability":
        lambda inp: "Esports" in (getattr(inp, "sub_sector", "") or "")
                    or inp.sector == "Gaming / Media / Content",
    "legaltech_regulatory_defence":
        lambda inp: inp.sector == "Legaltech",
    "builders_risk":
        lambda inp: (
            inp.sector in {"Cleantech / Climatetech", "Logistics / Mobility"}
            and (
                getattr(inp, "hardware_software_split", 0.0) >= 0.50
                or _mentions_any(inp, ("epc", "construction", "project", "infra", "solar", "warehouse"))
            )
        ),
    "specie_insurance":
        lambda inp: getattr(inp, "sub_sector", "") in {
            "D2C.Apparel_Footwear", "D2C.Hardware_Electronics",
        } or "Jewell" in (getattr(inp, "sub_sector", "") or ""),
    "nuclear_liability_extension":
        lambda inp: "Nuclear" in (getattr(inp, "sub_sector", "") or "")
                    or "Energy" in (getattr(inp, "sub_sector", "") or ""),
    "aquaculture_insurance":
        lambda inp: "Aqua" in (getattr(inp, "sub_sector", "") or ""),
    "pet_insurance_b2c":
        lambda inp: _mentions_any(inp, ("pet", "veterinary", "vet-tech", "veterinarian", "animal companion")),
    "microinsurance_sachet":
        lambda inp: inp.sector == "Fintech"
                    or _mentions_any(inp, (
                        "microinsurance", "sachet", "embedded insurance",
                        "payg", "pay-as-you-go", "low-income", "gig worker",
                    )),
    "wage_protection_gig_parametric":
        lambda inp: getattr(inp, "gig_headcount_pct", 0.0) > 0.20,
    "mental_health_wellness_benefit":
        lambda inp: inp.team_size >= 10,
    "esop_key_person_extension":
        lambda inp: _stage_at_or_above(inp.funding_stage, ("Series A",))
                    and inp.team_size <= 50,
    "bnpl_credit_default_embedded":
        lambda inp: getattr(inp, "rbi_registration", None) in {"NBFC", "PA"}
                    or "BNPL" in (getattr(inp, "sub_sector", "") or ""),
    "payment_systems_disruption":
        lambda inp: getattr(inp, "rbi_registration", None) in {"PA", "PPI"}
                    or inp.sector == "Fintech",
    "insurance_embedded_rails":
        lambda inp: inp.sector == "Fintech"
                    and getattr(inp, "rbi_registration", None) in {"CA", "PA"},
    "comprehensive_political_violence":
        lambda inp: bool(getattr(inp, "state_footprint", []))
                    and len(getattr(inp, "state_footprint", []) or []) >= 3,
    "political_risk_expropriation":
        lambda inp: getattr(inp, "export_eu_pct", 0.0) > 0.05
                    or _stage_at_or_above(inp.funding_stage, ("Series B+",)),
    "export_credit_guarantee":
        lambda inp: getattr(inp, "export_eu_pct", 0.0) > 0.10,
    "coop_society_liability":
        lambda inp: _mentions_any(inp, ("cooperative", "co-op", "coop", "fpo", "farmer producer")),
    "real_estate_techbroker_liability":
        lambda inp: "PropTech" in (getattr(inp, "sub_sector", "") or ""),
    "fleet_telematics_ubi":
        lambda inp: inp.sector == "Logistics / Mobility"
                    and inp.team_size >= 10,
    "edtech_learning_platform_liability":
        lambda inp: inp.sector == "Edtech",
    "hrtech_background_check_liability":
        lambda inp: inp.sector == "HRtech",
    "legal_defence_fund_cover":
        lambda inp: bool(getattr(inp, "regulatory", []))
                    or inp.sector in {"Fintech", "Healthtech", "Legaltech"}
                    or (
                        inp.sector in {"SaaS / Enterprise Software", "HRtech", "Edtech", "Deeptech / AI / Robotics"}
                        and (
                            getattr(inp, "data_sensitivity", "") == "High"
                            or bool(getattr(inp, "ai_in_product", False))
                            or _mentions_any(inp, ("dpdpa", "regulatory", "compliance", "children", "health", "employee"))
                        )
                    ),
}

AI_CYBER_DATA_PRODUCTS = {
    "ai_performance_liability", "embedded_cyber_via_compliance",
    "quantum_computing_liability", "active_cyber_response",
    "iot_device_liability", "supply_chain_cyber",
    "dpdpa_regulatory_defence", "ip_infringement_defence",
}

PRODUCT_RECALL_PRODUCTS = {
    "robotics_liability", "contaminated_product_insurance",
    "life_sciences_liability", "specie_insurance",
}

INFRA_ENERGY_PRODUCTS = {
    "satellite_in_orbit_liability", "satellite_launch_insurance",
    "carbon_credit_invalidation", "parametric_weather_climate",
    "pollution_legal_liability", "solar_module_insurance",
    "offshore_energy_liability", "biodiversity_natural_capital",
    "builders_risk", "nuclear_liability_extension", "fleet_telematics_ubi",
    "comprehensive_political_violence", "political_risk_expropriation",
    "export_credit_guarantee",
}

FINTECH_PAYMENT_CREDIT_PRODUCTS = {
    "blockchain_custody_liability", "bankers_indemnity_blanket",
    "bnpl_credit_default_embedded", "payment_systems_disruption",
    "insurance_embedded_rails",
}

EMPLOYEE_BENEFIT_PRODUCTS = {
    "wage_protection_gig_parametric", "mental_health_wellness_benefit",
    "esop_key_person_extension",
}

LEGAL_REGULATORY_PRODUCTS = {
    "warranty_indemnity", "side_a_dno_edge", "tax_liability_insurance",
    "single_project_pi", "legaltech_regulatory_defence", "legal_defence_fund_cover",
    "real_estate_techbroker_liability", "edtech_learning_platform_liability",
    "hrtech_background_check_liability",
}

NICHE_VERTICAL_PRODUCTS = {
    "media_production_insurance", "my_online_space_d2c", "esports_gaming_liability",
    "aquaculture_insurance", "pet_insurance_b2c", "microinsurance_sachet",
    "coop_society_liability",
}


def _add_signal(signals: list[str], label: str, score: float, cap: float = 100.0) -> float:
    if label not in signals:
        signals.append(label)
    return min(cap, score)

def _context_relevance(key: str, sector: str, team_size: int, funding_stage: str, inp) -> tuple[float, list[str]]:
    """Return independent contextual fit score and explainable match signals."""
    signals: list[str] = []
    score = 0.0

    if sector:
        signals.append(f"sector={sector}")
        score += 10

    sub_sector = getattr(inp, "sub_sector", None)
    if sub_sector:
        signals.append(f"sub_sector={sub_sector}")
        score += 5

    family_signal_count = 0

    def mark(label: str, points: float) -> None:
        nonlocal score, family_signal_count
        score = _add_signal(signals, label, score + points)
        family_signal_count += 1

    if key in AI_CYBER_DATA_PRODUCTS:
        if bool(getattr(inp, "ai_in_product", False)):
            mark("AI in product", 45)
        if getattr(inp, "data_sensitivity", "") in {"Medium", "High"}:
            mark(f"data_sensitivity={getattr(inp, 'data_sensitivity', '')}", 30)
        if getattr(inp, "data_handled", None):
            mark("data-handling context", 20)
        if team_size >= 10:
            mark("team_size>=10 cyber operating scale", 15)
        if getattr(inp, "b2b_pct", 0.0) >= 0.70:
            mark("B2B/enterprise exposure", 10)
        if _mentions_any(inp, ("cyber", "security", "soc 2", "iso 27001", "dpdpa", "iot", "sensor", "connected device", "quantum")):
            mark("cyber/data/product keyword match", 35)

    elif key in PRODUCT_RECALL_PRODUCTS:
        if sector in {"D2C / Consumer Brands", "Foodtech / Cloud Kitchen", "Healthtech"}:
            mark("physical/product sector", 25)
        if getattr(inp, "hardware_software_split", 0.0) >= 0.30:
            mark("hardware/product revenue mix", 25)
        if _mentions_any(inp, ("food", "beverage", "fssai", "supplement", "device", "medical device", "cdsco", "bis", "electronics", "manufacturing", "robot", "autonomous")):
            mark("product/recall keyword match", 45)
        if getattr(inp, "regulatory", None):
            mark("regulated product context", 15)

    elif key in INFRA_ENERGY_PRODUCTS:
        if sector in {"Cleantech / Climatetech", "Logistics / Mobility", "Agritech"}:
            mark("infra/energy/logistics sector", 25)
        if getattr(inp, "hardware_software_split", 0.0) >= 0.40:
            mark("material physical-asset exposure", 20)
        if getattr(inp, "export_eu_pct", 0.0) > 0.05:
            mark("cross-border/EU exposure", 20)
        if len(getattr(inp, "state_footprint", []) or []) >= 3:
            mark("multi-state physical footprint", 15)
        if _mentions_any(inp, ("solar", "wind", "offshore", "carbon", "climate", "epc", "construction", "warehouse", "fleet", "telematics", "nuclear", "satellite", "space")):
            mark("infra/energy keyword match", 45)
        if key == "carbon_credit_invalidation" and (
            getattr(inp, "export_eu_pct", 0.0) > 0.05
            or _mentions_any(inp, ("carbon credit", "carbon-credit", "ccts", "cbam", "voluntary carbon"))
        ):
            mark("carbon-credit/EU reporting context", 25)
        if key == "builders_risk" and (
            "Solar_EPC" in (getattr(inp, "sub_sector", "") or "")
            or _mentions_any(inp, ("epc", "construction", "project delay", "site work", "installation"))
        ):
            mark("EPC/construction project context", 25)
        if key == "parametric_weather_climate" and (
            getattr(inp, "facility_climate_risk_zone", "") == "High"
            or len(getattr(inp, "state_footprint", []) or []) >= 3
            or _mentions_any(inp, ("weather", "heat", "flood", "climate", "monsoon", "site delay"))
        ):
            mark("weather/climate delay context", 20)

    elif key in FINTECH_PAYMENT_CREDIT_PRODUCTS:
        if sector == "Fintech":
            mark("sector=Fintech", 40)
        if getattr(inp, "rbi_registration", None):
            mark(f"rbi_registration={getattr(inp, 'rbi_registration', None)}", 40)
        if getattr(inp, "b2b_pct", 0.0) >= 0.70:
            mark("B2B receivables/enterprise exposure", 15)
        if getattr(inp, "export_eu_pct", 0.0) > 0.10:
            mark("export receivables exposure", 20)
        if _mentions_any(inp, ("payment", "payments", "credit", "bnpl", "loan", "lending", "wallet", "bank", "blockchain", "crypto", "receivable", "invoice")):
            mark("fintech/payment keyword match", 40)

    elif key in EMPLOYEE_BENEFIT_PRODUCTS:
        if team_size >= 15:
            mark("team_size>=15 employee-benefit scale", 45)
        if getattr(inp, "gig_headcount_pct", 0.0) > 0.20:
            mark("gig workforce exposure", 40)
        if _stage_at_or_above(funding_stage, ("Series A",)):
            mark("Series A+ talent retention context", 10)
        if _mentions_any(inp, ("employee", "workforce", "gig", "benefit", "esop", "mental health", "critical illness")):
            mark("employee-benefit keyword match", 25)

    elif key in LEGAL_REGULATORY_PRODUCTS:
        is_transactional_cover = key in {"warranty_indemnity", "tax_liability_insurance"}
        if bool(getattr(inp, "regulatory", [])):
            mark("explicit regulatory exposure", 45)
        if sector in {"Fintech", "Healthtech", "Legaltech", "HRtech", "Edtech"}:
            mark("regulated/professional-services sector", 25)
        if bool(getattr(inp, "ai_in_product", False)):
            mark("AI regulatory/IP exposure", 20)
        if getattr(inp, "data_sensitivity", "") == "High":
            mark("high-sensitivity data", 15)
        if getattr(inp, "b2b_pct", 0.0) >= 0.70:
            mark("contractual liability exposure", 15)
        if _stage_at_or_above(funding_stage, ("Series A",)):
            mark("Series A+ governance/procurement context", 10)
        if _mentions_any(inp, ("regulatory", "compliance", "lawsuit", "contract", "tax", "legal", "proptech", "background check", "children")):
            mark("legal/regulatory keyword match", 35)
        if key == "warranty_indemnity" and _mentions_any(inp, (
            "m&a", "merger", "acquisition", "acquire", "exit", "roll-up", "rollup", "due diligence"
        )):
            mark("M&A/exit transaction context", 45)
        if key == "tax_liability_insurance" and (
            getattr(inp, "holdco_domicile", "India") != "India"
            or _mentions_any(inp, ("tax", "transfer pricing", "gaar", "gift city", "mauritius", "singapore", "restructuring"))
        ):
            mark("explicit tax-structuring context", 45)
        if is_transactional_cover and not _mentions_any(inp, (
            "m&a", "merger", "acquisition", "acquire", "exit", "roll-up",
            "rollup", "due diligence", "tax", "transfer pricing", "gaar",
            "gift city", "mauritius", "singapore", "restructuring",
        )):
            score = min(score, 70.0)

    elif key in NICHE_VERTICAL_PRODUCTS:
        if key == "media_production_insurance" and sector == "Gaming / Media / Content":
            mark("media/content sector", 55)
        elif key == "my_online_space_d2c" and sector in {"D2C / Consumer Brands", "Foodtech / Cloud Kitchen", "Gaming / Media / Content"}:
            mark("online consumer brand context", 45)
        elif key == "esports_gaming_liability" and sector == "Gaming / Media / Content":
            mark("gaming/esports context", 55)
        elif key == "aquaculture_insurance" and _mentions_any(inp, ("aqua", "aquaculture", "fish", "shrimp")):
            mark("aquaculture keyword match", 70)
        elif key == "pet_insurance_b2c" and _mentions_any(inp, ("pet", "veterinary", "vet-tech", "veterinarian", "animal companion")):
            mark("petcare keyword match", 70)
        elif key == "microinsurance_sachet" and (
            sector == "Fintech" or getattr(inp, "gig_headcount_pct", 0.0) > 0.20
            or _mentions_any(inp, ("microinsurance", "sachet", "embedded insurance", "payg", "low-income"))
        ):
            mark("microinsurance distribution context", 60)
        elif key == "coop_society_liability" and _mentions_any(inp, ("cooperative", "co-op", "coop", "fpo", "farmer producer")):
            mark("co-op/FPO keyword match", 70)

    if family_signal_count == 0:
        return 0.0, []

    # Broad cyber/data products should remain visible, but not crowd out
    # highly specific AI or embedded-compliance covers merely because every
    # digital startup has elevated cyber and privacy risk.
    broad_product_context_caps = {
        "active_cyber_response": 75.0,
        "supply_chain_cyber": 72.0,
        "dpdpa_regulatory_defence": 78.0,
    }
    if key in broad_product_context_caps:
        score = min(score, broad_product_context_caps[key])

    return round(min(score, 100.0), 1), signals[:8]

def _ranking_bonus(key: str, inp) -> float:
    """Small tie-breaker bonus used only for sorting, not displayed scores."""
    bonus = 0.0
    sub_sector = getattr(inp, "sub_sector", "") or ""
    is_solar_epc = "Solar_EPC" in sub_sector or _mentions_any(inp, ("solar epc", "solar project"))
    has_carbon_context = getattr(inp, "export_eu_pct", 0.0) > 0.05 or _mentions_any(
        inp, ("carbon credit", "carbon-credit", "ccts", "cbam", "carbon reporting")
    )

    if is_solar_epc:
        if key == "carbon_credit_invalidation" and has_carbon_context:
            bonus += 6.0
        elif key == "solar_module_insurance":
            bonus += 5.0
        elif key == "builders_risk":
            bonus += 4.0
        elif key == "pollution_legal_liability":
            bonus += 4.0
        elif key == "parametric_weather_climate":
            bonus += 3.5

    return bonus

# =============================================================================
# RECOMMENDER
# =============================================================================
def recommend_competitor_products(
    risk_scores: dict,
    sector: str,
    team_size: int,
    funding_stage: str,
    inp,
    top_n: int = 5,
    min_score: float = 45.0,
) -> list:
    """
    Return up to top_n competitor products that:
      • Are sector-relevant (per COMPETITOR_SECTOR_RELEVANCE)
      • Pass any input trigger (per COMPETITOR_TRIGGERS)
      • Score >= min_score against the user's 13-category risk vector

    Each result dict contains:
      key, name, providers, india_status, what_it_covers,
      icici_equivalent, icici_gap, best_for, score, priority
    """
    scored: list[tuple[str, float, float, float, float, list[str]]] = []

    for key, weights in COMPETITOR_PRODUCT_RISK_MAP.items():
        # Sector gate
        relevant_sectors = COMPETITOR_SECTOR_RELEVANCE.get(key)
        if relevant_sectors and sector not in relevant_sectors:
            continue

        # Trigger gate
        trigger = COMPETITOR_TRIGGERS.get(key)
        if trigger is not None:
            try:
                if not trigger(inp):
                    continue
            except Exception:
                continue

        # Risk fit: weighted mean against the user's 13-category risk vector.
        usable = {cat: w for cat, w in weights.items() if cat in risk_scores}
        if not usable:
            continue
        raw = sum(risk_scores[cat] * w for cat, w in usable.items())
        risk_fit = raw / sum(usable.values())

        # Context relevance: guardrail so niche products do not win purely
        # because broad liability/property/compliance scores are high.
        context_relevance, matched_signals = _context_relevance(
            key, sector, team_size, funding_stage, inp
        )
        if context_relevance <= 0:
            continue

        score = (risk_fit * 0.70) + (context_relevance * 0.30)
        rank_score = score + _ranking_bonus(key, inp)

        if score >= min_score:
            scored.append((key, rank_score, score, risk_fit, context_relevance, matched_signals))

    scored.sort(key=lambda x: x[1], reverse=True)
    scored = scored[:top_n]

    out = []
    for key, _rank_score, score, risk_fit, context_relevance, matched_signals in scored:
        meta = COMPETITOR_PRODUCT_CATALOG[key].copy()
        meta["key"] = key
        meta["score"] = round(score, 1)
        meta["risk_fit"] = round(risk_fit, 1)
        meta["context_relevance"] = round(context_relevance, 1)
        meta["matched_signals"] = matched_signals
        meta["priority"] = _priority_label(score)
        out.append(meta)
    return out

def _priority_label(score: float) -> str:
    if score >= 70:
        return "Critical Gap"
    if score >= 55:
        return "Strategic Gap"
    return "Tactical Gap"

# =============================================================================
# SELF-VALIDATION
# =============================================================================
def _validate_catalog() -> None:
    cat_keys = set(COMPETITOR_PRODUCT_CATALOG.keys())
    map_keys = set(COMPETITOR_PRODUCT_RISK_MAP.keys())
    missing_in_map = cat_keys - map_keys
    missing_in_cat = map_keys - cat_keys
    if missing_in_map or missing_in_cat:
        raise ValueError(
            "competitor_catalog_expanded config error: "
            f"in catalog but no risk map: {missing_in_map}; "
            f"in risk map but no catalog: {missing_in_cat}"
        )
    for key, meta in COMPETITOR_PRODUCT_CATALOG.items():
        for required in ("name", "providers", "india_status", "what_it_covers",
                         "icici_equivalent", "icici_gap", "best_for"):
            if required not in meta:
                raise ValueError(f"competitor product '{key}' missing field '{required}'")

_validate_catalog()


# =============================================================================
# COMPATIBILITY SHIM — drop-in replacement for global_products.get_top5_global()
# =============================================================================
def _label_from_india_status(india_status: str) -> str:
    """Derive a label consistent with global_products._label() from india_status text."""
    s = india_status.lower()
    if any(kw in s for kw in ("tata aig", "bajaj", "hdfc", "new india", "digit", "sbi general",
                               "indian competitor", "partner-led", "irdai sandbox",
                               "available now", "available in india")):
        return "india_competitor"
    return "not_in_india"


def get_top5_global(
    scores: dict,
    sector: str,
    size_bucket: str,
    team_size: int = 10,
    funding_stage: str = "Seed",
    inp=None,
    top_n: int = 5,
) -> list[dict]:
    """
    Drop-in replacement for global_products.get_top5_global().
    Delegates to recommend_competitor_products() and normalises the output
    to the shape server.py expects:
      key, name, providers, what_it_covers, icici_equivalent, icici_gap,
      best_for, relevance_score, label, match_basis, premium_range,
      score, risk_fit, context_relevance, matched_signals, priority
    """
    results = recommend_competitor_products(
        risk_scores=scores,
        sector=sector,
        team_size=team_size,
        funding_stage=funding_stage,
        inp=inp,
        top_n=top_n,
        min_score=40.0,
    )
    out = []
    for r in results:
        r = r.copy()
        r.setdefault("relevance_score", r.get("score", 0.0))
        r.setdefault("premium_range", None)
        r.setdefault("label", _label_from_india_status(r.get("india_status", "")))
        r.setdefault("match_basis", "competitor_scored")
        out.append(r)
    return out
