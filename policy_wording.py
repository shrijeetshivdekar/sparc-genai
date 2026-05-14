"""Policy wording comparison helpers for SPARC.

The reference data is distilled from SPARC_Policy_Wording_Comparison.docx.
It is intentionally deterministic: GenAI may summarize the result, but these
checks provide the auditable baseline.
"""

from __future__ import annotations

import re
from typing import Any


def _entry(
    name: str,
    covers: list[str] | None = None,
    exclusions: list[str] | None = None,
    gaps: list[str] | None = None,
    fit: str = "",
) -> dict[str, Any]:
    return {
        "name": name,
        "covers": covers or [],
        "exclusions": exclusions or [],
        "gaps": gaps or [],
        "fit": fit,
    }


POLICY_REFERENCE: dict[str, dict[str, Any]] = {
    "msme_suraksha_kavach": _entry(
        "MSME Suraksha Kavach",
        ["Fire and allied perils", "Burglary", "Business interruption", "Cyber add-on", "Product liability add-on", "Money insurance add-on", "Public liability add-on", "Employees compensation add-on"],
        ["Kutcha construction not covered", "Terrorism deductible applies", "Deliberate or intentional acts", "War, nuclear, and radioactive perils", "Cyber loss excluded from property section unless cyber module is added", "Goods in transit not covered unless marine add-on is purchased", "Flood endorsement should be checked for specific geographies"],
        ["No D&O liability", "No professional indemnity or E&O", "No employment practices liability", "No key person insurance", "No group health", "INR 50 Cr SI cap", "No trade credit or marine transit by default"],
        "Early-stage startups with physical premises, inventory, or field operations.",
    ),
    "corporate_cover_ii": _entry(
        "Corporate Cover II",
        ["Property", "Business interruption", "Public liability", "Employees compensation", "Cyber recommended", "D&O recommended", "Professional indemnity add-on", "Crime/fidelity add-on", "Marine transit add-on", "Trade credit add-on"],
        ["Pre-existing conditions or known events", "War, nuclear, and radioactive perils", "Deliberate or intentional acts", "Consequential loss beyond BI section", "Employee fraud excluded from property section unless crime/fidelity is added", "Cyber events excluded from property section unless cyber add-on is purchased", "Short-period policy loading", "Market value basis may not guarantee replacement cost"],
        ["No EPL in base form", "No key person insurance", "No IP or copyright cover", "No clinical trials liability", "No drone/RPAS cover", "Group health placed separately", "D&O optional unless selected"],
        "Growth-stage startups with offices, multi-team operations, and enterprise contracts.",
    ),
    "business_shield_sme": _entry(
        "Business Shield SME",
        ["Cyber liability", "D&O liability", "Professional indemnity/E&O", "Group health recommended", "Group personal accident recommended", "EPL add-on", "Key person add-on", "Crime/fidelity add-on"],
        ["Prior acts before retroactive date", "Insured-vs-insured D&O exclusion", "Bodily injury and physical property damage not covered under PI", "Deliberate fraud excluded until adjudicated", "Intentional regulatory violations", "Criminal fines where uninsurable", "State-sponsored cyber attack ambiguity"],
        ["No fire or property cover", "No business interruption", "No marine transit or motor fleet", "No trade credit", "CERT-In 6-hour reporting risk may not be fully covered", "D&O Side C may need endorsement"],
        "Digital-first, asset-light funded startups.",
    ),
    "bharat_sookshma_udyam_suraksha": _entry(
        "Bharat Sookshma Udyam Suraksha",
        ["Fire and allied perils", "Burglary", "Business interruption", "Money add-on", "Public liability add-on", "Employees compensation add-on"],
        ["INR 5 Cr hard SI ceiling", "Terrorism deductible applies", "War, nuclear, and radioactive perils", "Deliberate or intentional acts", "Kutcha construction not covered", "Cyber loss excluded from property section", "Claims must be lodged within 12 months"],
        ["INR 5 Cr SI ceiling", "No cyber liability", "No D&O or PI financial lines", "No group health", "No trade credit or marine", "Bharat Laghu is the next step after asset growth"],
        "Very early-stage startups with minimal assets.",
    ),
    "bharat_laghu_udyam_suraksha": _entry(
        "Bharat Laghu Udyam Suraksha",
        ["Fire and allied perils", "Burglary recommended", "Business interruption recommended", "Machinery breakdown add-on", "Employees compensation add-on", "Public liability add-on", "Money insurance add-on", "Electronic equipment add-on"],
        ["War, nuclear, and radioactive perils", "Deliberate or intentional acts", "Gradual deterioration, wear and tear", "Cyber loss excluded from property section", "Terrorism deductible applies"],
        ["No cyber liability", "No D&O or PI", "No group health", "No trade credit or marine", "Limited financial-lines coverage"],
        "Physical-asset startups with INR 5-50 Cr asset values.",
    ),
    "enterprise_secure_package_policy": _entry(
        "Enterprise Secure Package Policy",
        ["Property", "Business interruption", "Public liability", "Employees compensation", "Cyber liability", "D&O liability", "Professional indemnity add-on", "Crime/fidelity add-on", "Marine transit add-on", "Trade credit add-on", "Product liability add-on"],
        ["Physical presence required", "Minimum 10 employees required", "War, nuclear, and radioactive perils", "Deliberate acts", "State-sponsored cyber attack ambiguity", "D&O insured-vs-insured exclusion", "Criminal fines where uninsurable"],
        ["No EPL in base form", "No key person insurance", "No drone/RPAS cover", "Group health placed separately", "No clinical trials liability", "Unsuitable for fully remote companies"],
        "Series B+ startups with multi-site operations, enterprise contracts, and regulatory exposure.",
    ),
    "i_select_liability_insurance": _entry(
        "I-select Liability Insurance",
        ["Professional indemnity/E&O anchor", "D&O recommended", "Cyber recommended", "Crime/fidelity add-on", "EPL add-on", "Comprehensive general liability add-on", "Public liability add-on"],
        ["Prior acts before retroactive date", "Insured-vs-insured D&O exclusion", "Bodily injury/property damage under PI", "Deliberate fraud", "Criminal penalties where uninsurable", "State-sponsored cyber attack ambiguity"],
        ["No property or fire cover", "No business interruption", "No marine, motor, or trade credit", "No group health or group PA", "Gaps depend on selected add-ons"],
        "Liability-heavy startups needing modular financial lines.",
    ),
    "entertainment_production_package": _entry(
        "Entertainment Production Package",
        ["Event production", "Public liability", "Comprehensive general liability recommended", "Employees compensation add-on", "Electronic equipment add-on", "Fire add-on", "Burglary add-on"],
        ["Gaming/media/content sector restriction", "War and nuclear perils", "Deliberate acts", "Wear and tear on equipment", "Pre-existing damage"],
        ["No cyber liability for content/IP breaches", "No D&O or PI", "No group health", "No BI beyond production abandonment", "Not suitable outside media/production"],
    ),
    "merchants_cover_iii": _entry(
        "Merchants Cover III",
        ["Fire and allied perils", "Burglary", "Public liability", "Money insurance recommended", "Employees compensation recommended", "Business interruption add-on", "Product liability add-on", "Electronic equipment add-on"],
        ["War and nuclear perils", "Deliberate acts", "Cyber loss excluded from property section", "Terrorism deductible", "Wear and tear"],
        ["No cyber liability", "No D&O or PI", "No group health", "Retail-focused and not suited for pure digital or B2B startups"],
    ),
    "cyber_liability": _entry(
        "Cyber Liability Insurance",
        ["Data breach response costs", "Cyber extortion/ransomware", "Network security liability", "Cyber business interruption", "Regulatory defence costs", "Reputational harm expenses"],
        ["Prior known breaches", "Bodily injury or physical property damage", "War/state-sponsored cyber operations ambiguity", "Failure to maintain basic security standards", "Criminal fines where uninsurable", "Contractual penalties beyond insured liability"],
        ["CERT-In 6-hour notification costs may not be fully covered", "State-sponsored attack attribution must be checked", "Employee internal fraud needs crime/fidelity", "Physical hardware damage may need electronic equipment insurance", "DPDP penalty coverage stance must be verified"],
    ),
    "dno_liability": _entry(
        "Directors & Officers (D&O) Liability",
        ["Side A personal liability", "Side B company reimbursement", "Side C entity securities claims if included", "Regulatory investigation defence", "Employment wrongful acts if EPL rider added"],
        ["Insured-vs-insured claims", "Fraud/dishonesty until final adjudication", "Bodily injury/property damage", "Prior acts before retroactive date", "Wilful regulatory violations", "Criminal fines where uninsurable"],
        ["Side C may need endorsement", "Regulatory investigation cover must be confirmed", "Insured-vs-insured can affect shareholder derivative actions", "Run-off cover after exit or wind-down is not automatic"],
    ),
    "professional_indemnity": _entry(
        "Professional Indemnity / E&O Insurance",
        ["Errors and omissions", "Negligent advice or misrepresentation", "Civil defence costs", "SaaS/software contract performance failure", "IP infringement if wording includes it"],
        ["Bodily injury or physical property damage", "Prior acts before retroactive date", "Deliberate breach of contract", "Criminal/fraudulent acts", "Pollution liability", "Cyber data breach liability usually excluded"],
        ["AI/algorithmic errors may fall outside standard PI", "DPDP data fiduciary obligations need cyber", "SaaS uptime SLA penalties may exceed sub-limits", "Copyright/patent coverage varies"],
    ),
    "employees_comp": _entry(
        "Workmen's / Employees' Compensation",
        ["Workplace death or disability", "Temporary disability compensation", "Medical expenses from workplace injury", "EC Act and Fatal Accidents Act liability", "Legal costs of EC disputes"],
        ["Employees not listed in schedule", "Injuries outside course of employment", "Pre-existing conditions", "Wilful acts of employee", "War and nuclear perils", "Contractor/gig workers not classified as employees"],
        ["Gig/platform workers may not be covered", "Group health is separate", "ESIC applicability must be checked", "Occupational disease may need endorsement"],
    ),
    "employee_health": _entry(
        "Group Health Insurance",
        ["Hospitalisation", "Pre/post hospitalisation", "Daycare procedures", "Maternity if opted", "OPD if opted", "Cashless network"],
        ["Pre-existing disease waiting period if not waived", "Cosmetic treatment", "Experimental procedures", "Self-inflicted injuries", "War/civil unrest", "Dental unless rider"],
        ["Does not replace employees compensation", "Mental health parity must be verified", "OPD often excluded from base", "Employees added late may face inception gaps"],
    ),
    "property_fire": _entry(
        "Fire & Allied Perils / Property Insurance",
        ["Fire, lightning, explosion", "Riot/strike/malicious damage", "Storm/cyclone/flood/inundation", "Earthquake if opted", "Impact damage", "Sprinkler leakage"],
        ["Kutcha construction", "War and nuclear perils", "Deliberate acts", "Electrical/mechanical breakdown", "Cyber loss to property", "Gradual deterioration/wear and tear", "Consequential loss beyond BI", "Terrorism deductible/separate coverage"],
        ["Average clause underinsurance risk", "Flood locations may need endorsement", "Cyber physical damage may need cyber/equipment cover", "Business interruption is not automatic"],
    ),
    "public_liability": _entry(
        "Public Liability Insurance",
        ["Third-party bodily injury at premises", "Third-party property damage", "Legal defence costs", "Medical expenses of injured third parties"],
        ["Employee injuries", "Contractual liability beyond legal liability", "War and nuclear perils", "Deliberate acts", "Product liability", "Gradual pollution"],
        ["Does not replace employees compensation", "CGL may be needed for enterprise contracts", "Pollution liability may need specialist cover"],
    ),
    "product_liability": _entry(
        "Product Liability Insurance",
        ["Third-party bodily injury caused by product", "Third-party property damage caused by product", "Legal defence costs", "Recall costs if endorsed"],
        ["Contractual liability beyond statutory", "Deliberate product defects", "Gradual pollution", "War and nuclear", "Digital products/software defects"],
        ["Software products usually need PI", "Medical/pharma recalls need specialist cover", "Exports may need US/EU jurisdiction endorsement"],
    ),
    "marine_transit": _entry(
        "Marine Transit / Inland Transit Insurance",
        ["Loss or damage to goods in transit", "Sea/air/inland transit", "Theft/piracy/jettison", "Collision/fire/sinking", "Warehouse-to-warehouse if opted"],
        ["Inherent vice", "Delay unless endorsed", "War and strikes unless endorsed", "Faulty packing", "Ordinary leakage/wear and tear"],
        ["Last-mile mode coverage must be checked", "High-value equipment may have sub-limits", "Perishables may need cold-chain endorsement"],
    ),
    "key_person": _entry(
        "Key Person Insurance",
        ["Death of founder/CTO/CEO", "Total permanent disability", "Lump sum or income replacement to business", "Loan repayment cover if opted"],
        ["Suicide within waiting period", "Pre-existing conditions", "War and hazardous activities", "Fraudulent claims"],
        ["Usually life insurer, not general insurance bundle", "Critical illness may need rider", "Founder buyout agreements need shareholder protection"],
    ),
    "crime_fidelity": _entry(
        "Crime / Fidelity Insurance",
        ["Employee theft/dishonesty", "Computer fraud and funds transfer fraud", "Forgery and alteration", "Third-party crime", "Social engineering if opted"],
        ["Known dishonest employees", "Inventory shortage/unexplained losses", "War and nuclear", "Wilful acts of senior management", "Cyber extortion"],
        ["Social engineering needs endorsement", "Vendor/supply-chain fraud extension must be checked", "Crypto losses often excluded"],
    ),
    "employment_practices": _entry(
        "Employment Practices Liability (EPL)",
        ["Wrongful termination", "Sexual harassment/POSH", "Discrimination", "Retaliation", "Workplace bullying if endorsed"],
        ["Prior acts before retroactive date", "Criminal acts", "Deliberate legal violations", "Wage and hour claims", "ESOP disputes"],
        ["POSH Internal Committee still required", "Constructive dismissal wording must be checked", "Class/collective claims may be limited"],
    ),
    "business_interruption": _entry(
        "Business Interruption Insurance",
        ["Revenue loss after insured property damage", "Continuing fixed costs", "Increased cost of working", "Payroll during shutdown"],
        ["Must be triggered by insured property loss", "Cyber BI requires cyber extension", "Supply chain failure without property damage", "War and nuclear", "Government closure without property damage"],
        ["Pandemic/public health BI often excluded", "Cyber downtime not covered by property BI", "Indemnity period may be too short", "Waiting period/deductible must be checked"],
    ),
    "drone_insurance": _entry(
        "Remotely Piloted Aircraft (Drone) Insurance",
        ["Drone hull/own damage", "Third-party liability", "Pilot personal accident", "Payload if opted", "Ground equipment"],
        ["Operations outside permitted DGCA zones", "Non-licensed/non-certified operators", "Intentional or illegal operations", "Wear and tear", "War and nuclear"],
        ["DGCA/Digital Sky compliance required", "BVLOS needs endorsement", "Drone imaging data liability needs cyber"],
    ),
    "clinical_trials": _entry(
        "Clinical Trials Liability",
        ["Trial participant injury", "Trial participant death", "Regulatory investigation defence", "Protocol deviations", "Sponsor liability"],
        ["Known protocol violations", "Pre-existing conditions causing event", "War and nuclear", "Non-ICMR-approved trials", "Trials outside India without endorsement"],
        ["CDSCO/ICMR compliance still mandatory", "Post-trial follow-up liabilities may extend beyond policy", "International trials need jurisdiction endorsements"],
    ),
}


ALIASES: dict[str, str] = {
    "business shield sme": "business_shield_sme",
    "business guard plus": "business_shield_sme",
    "corporate cover ii": "corporate_cover_ii",
    "msme suraksha kavach": "msme_suraksha_kavach",
    "bharat sookshma udyam suraksha": "bharat_sookshma_udyam_suraksha",
    "bharat laghu udyam suraksha": "bharat_laghu_udyam_suraksha",
    "enterprise secure package policy": "enterprise_secure_package_policy",
    "enterprise secure": "enterprise_secure_package_policy",
    "i-select liability insurance": "i_select_liability_insurance",
    "iselect liability insurance": "i_select_liability_insurance",
    "entertainment production package": "entertainment_production_package",
    "merchants cover iii": "merchants_cover_iii",
    "cyber liability": "cyber_liability",
    "cyber liability insurance": "cyber_liability",
    "directors officers d o liability": "dno_liability",
    "d&o liability": "dno_liability",
    "dno liability": "dno_liability",
    "professional indemnity": "professional_indemnity",
    "professional indemnity e o insurance": "professional_indemnity",
    "professional indemnity / e&o insurance": "professional_indemnity",
    "tech e o": "professional_indemnity",
    "workmen s compensation employee s compensation": "employees_comp",
    "employees compensation": "employees_comp",
    "group health insurance": "employee_health",
    "fire allied perils property insurance": "property_fire",
    "public liability insurance": "public_liability",
    "product liability insurance": "product_liability",
    "marine transit inland transit insurance": "marine_transit",
    "key person insurance": "key_person",
    "crime fidelity insurance": "crime_fidelity",
    "employment practices liability epl": "employment_practices",
    "business interruption insurance": "business_interruption",
    "drone insurance": "drone_insurance",
    "remotely piloted aircraft drone insurance": "drone_insurance",
    "clinical trials liability": "clinical_trials",
}


UNIVERSAL_EXCLUSIONS = [
    "War and nuclear",
    "Deliberate or wilful acts",
    "Criminal fines and penalties where uninsurable",
    "Gradual deterioration and wear and tear",
    "Consequential loss unless BI applies",
    "Contractual liability beyond legal liability",
    "Pre-existing or known events",
    "Gradual pollution",
    "Sanctions",
]


COVER_TERMS = {
    "cyber_liability": ["cyber", "data breach", "ransomware", "network security", "privacy"],
    "dno_liability": ["d&o", "directors", "officers", "side a", "side b"],
    "professional_indemnity": ["professional indemnity", "errors and omissions", "e&o", "negligent advice"],
    "employees_comp": ["employees compensation", "workmen", "workplace injury", "ec act"],
    "employee_health": ["group health", "hospitalisation", "cashless", "maternity", "opd"],
    "property_fire": ["fire", "allied perils", "property", "storm", "flood", "earthquake"],
    "business_interruption": ["business interruption", "gross profit", "increased cost of working", "indemnity period"],
    "public_liability": ["public liability", "third-party bodily injury", "third party bodily injury"],
    "product_liability": ["product liability", "product defect", "recall"],
    "marine_transit": ["marine", "transit", "warehouse-to-warehouse", "inland"],
    "key_person": ["key person", "founder", "permanent disability", "life"],
    "crime_fidelity": ["crime", "fidelity", "employee theft", "computer fraud", "social engineering"],
    "employment_practices": ["employment practices", "wrongful termination", "sexual harassment", "posh", "discrimination"],
    "drone_insurance": ["drone", "rpas", "uas", "dgca", "digital sky"],
    "clinical_trials": ["clinical trial", "participant injury", "protocol"],
}


def _normalise(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()


def canonical_policy_key(name: str | None) -> str | None:
    if not name:
        return None
    raw = str(name).strip()
    if raw in POLICY_REFERENCE:
        return raw
    norm = _normalise(raw)
    if norm in ALIASES:
        return ALIASES[norm]
    for alias, key in ALIASES.items():
        if alias and (alias in norm or norm in alias):
            return key
    return None


def _contains_any(text: str, phrases: list[str]) -> bool:
    haystack = _normalise(text)
    return any(_normalise(phrase) in haystack for phrase in phrases if phrase)


def _item_status(text: str, item: str) -> str:
    words = [w for w in re.split(r"[^a-zA-Z0-9]+", item.lower()) if len(w) > 3]
    if not words:
        return "not_detected"
    hits = sum(1 for word in words if word in text)
    return "detected" if hits >= max(1, min(3, len(words) // 2)) else "not_detected"


def _recommended_cover_keys(recommendations: list[dict[str, Any]] | None, bundle: dict[str, Any] | None) -> list[str]:
    keys: list[str] = []
    for cover in (bundle or {}).get("mandatory_covers", []) + (bundle or {}).get("optional_covers", []):
        if cover not in keys:
            keys.append(cover)
    for item in recommendations or []:
        key = item.get("key")
        if key and key not in keys:
            keys.append(key)
    return keys


def compare_policy_wording(payload: dict[str, Any]) -> dict[str, Any]:
    policy_text = str(payload.get("policy_text") or "").strip()
    product_name = payload.get("product_name") or payload.get("product_key")
    profile = payload.get("profile") or {}
    recommendations = payload.get("recommendations") or []
    bundle = payload.get("bundle_match") or {}
    selected_key = canonical_policy_key(product_name) or canonical_policy_key((bundle or {}).get("name"))
    reference = POLICY_REFERENCE.get(selected_key or "") if selected_key else None
    normalized_text = _normalise(policy_text)

    if len(policy_text) < 80:
        return {
            "ok": False,
            "error": "Paste at least 80 characters of policy wording or a policy excerpt.",
            "source": "deterministic",
        }

    expected_exclusions = []
    expected_gaps = []
    if reference:
        expected_exclusions = [
            {"text": item, "status": _item_status(normalized_text, item)}
            for item in reference["exclusions"]
        ]
        expected_gaps = [{"text": item, "status": "reference_gap"} for item in reference["gaps"]]

    universal_detected = [
        item for item in UNIVERSAL_EXCLUSIONS
        if _item_status(normalized_text, item) == "detected"
    ]

    recommended_keys = _recommended_cover_keys(recommendations, bundle)
    missing_recommended_covers = []
    for key in recommended_keys:
        terms = COVER_TERMS.get(key)
        if terms and not _contains_any(policy_text, terms):
            missing_recommended_covers.append({
                "key": key,
                "status": "not_found_in_pasted_wording",
                "why_it_matters": "This cover appears in the SPARC recommendation but was not detected in the pasted wording.",
            })

    profile_flags = []
    data = set(profile.get("data_handled") or [])
    regs = set(profile.get("regulatory") or [])
    if (data & {"Payments / financial transactions", "Personal identity data (KYC / Aadhaar)", "Sensitive personal data (DPDP Act)"}) and not _contains_any(policy_text, COVER_TERMS["cyber_liability"]):
        profile_flags.append("Sensitive/payment data exposure is present, but cyber/privacy wording was not detected.")
    if (profile.get("rbi_registration") or "RBI / SEBI / IRDAI licensed" in regs or profile.get("has_investors") == "Yes") and not _contains_any(policy_text, COVER_TERMS["dno_liability"]):
        profile_flags.append("Investor/regulatory exposure is present, but D&O wording was not detected.")
    if profile.get("team_size", 0) and int(profile.get("team_size", 0)) >= 10 and not _contains_any(policy_text, COVER_TERMS["employment_practices"]):
        profile_flags.append("Team size suggests EPL/POSH exposure; EPL wording was not detected.")

    not_detected_exclusions = [x["text"] for x in expected_exclusions if x["status"] == "not_detected"]
    summary_parts = []
    if reference:
        summary_parts.append(f"Compared pasted wording against {reference['name']} reference.")
    else:
        summary_parts.append("No exact reference product was selected; comparison used universal exclusions and SPARC recommended covers.")
    if not_detected_exclusions:
        summary_parts.append(f"{len(not_detected_exclusions)} expected exclusion(s) were not detected in the pasted wording and should be checked manually.")
    if missing_recommended_covers:
        summary_parts.append(f"{len(missing_recommended_covers)} SPARC recommended cover(s) were not detected in the pasted wording.")

    return {
        "ok": True,
        "source": "deterministic",
        "matched_reference": reference["name"] if reference else None,
        "matched_reference_key": selected_key,
        "reference_fit": reference.get("fit") if reference else "",
        "summary": " ".join(summary_parts),
        "expected_covers": reference["covers"] if reference else [],
        "expected_exclusions": expected_exclusions,
        "coverage_gaps": expected_gaps,
        "universal_exclusions_detected": universal_detected,
        "missing_recommended_covers": missing_recommended_covers,
        "profile_gap_flags": profile_flags,
        "manual_review_required": bool(not_detected_exclusions or missing_recommended_covers or profile_flags),
        "audit": {
            "reference_doc": "SPARC_Policy_Wording_Comparison.docx",
            "policy_text_chars": len(policy_text),
            "recommended_cover_count": len(recommended_keys),
            "deterministic_only": True,
        },
    }

