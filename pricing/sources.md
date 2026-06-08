# SPARC Pricing — Indian Public Sources Bibliography

Every parameter in `parameters.yaml` cites one of the sources below.
Indian-domain sources only. No US benchmarks. No FX-converted USD rates.
Last verified: **2026-05-25**.

---

## A. Regulator (IRDAI)

### A1. IRDAI Annual Report 2023–24
- **URL:** https://irdai.gov.in/annual-reports
- **Type:** Regulator publication
- **Informs:** Industry Ultimate Loss Ratios (ULRs) by LOB (`industry_ulr.*`), management expense ratio (`expense_components.management_expense_ratio`), implied profit margin from solvency framework (`expense_components.profit_margin`), Fire segment data (`base_rate_per_crore.Property` above-MSME band).
- **Confidence:** high (it is the regulator's own publication).

### A2. IRDAI Health Insurance Annual Report FY23–24
- **URL:** https://irdai.gov.in/annual-reports
- **Type:** Regulator publication
- **Informs:** Group Health ICR (`industry_ulr.GH = 0.92`), per-employee GH baseline rates (`base_rate_per_crore.GH.*`).
- **Confidence:** high.

### A3. IRDAI Public Disclosures (L-series quarterly forms)
- **URL:** each insurer's investor-relations page; aggregator at https://irdai.gov.in/public-disclosures
- **Type:** Quarterly regulatory disclosure (every insurer publishes)
- **Informs:** State-wise premium concentration (`state_factor.*`), per-LOB premium-claims-ULR per insurer (median used for `base_rate_per_crore.*`).
- **Carriers tracked:** Tata AIG, ICICI Lombard, HDFC ERGO, Bajaj Allianz, Go Digit, SBI General, New India Assurance, Acko.
- **Confidence:** medium (extraction involves median across carriers).

### A4. IRDAI (Payment of Commission) Regulations 2023
- **URL:** https://irdai.gov.in/document-detail?documentId=3404538
- **Type:** Regulation (Use-and-File regime)
- **Informs:** Commission cap (`expense_components.commission = 0.125`); 30% absolute cap for non-life under §6, with typical commercial liability commission of 12-15%.
- **Confidence:** high.

### A5. IRDAI Bharat Sookshma Udyam Suraksha (BSU) Standard Policy Wording
- **URL:** https://irdai.gov.in/document-detail?documentId=394018
- **Type:** Regulator-mandated standard wording
- **Informs:** **REGULATED RATE** for MSME property up to ₹5 crore SI. Used as the floor for `base_rate_per_crore.Property` MSME bands. Model test #1 reconciles ±5% against this rate.
- **Confidence:** high. This is the only line with a regulator-mandated rate post-detariffing.

### A6. IRDAI File-and-Use Procedure
- **URL:** https://irdai.gov.in/document-detail
- **Type:** Procedure
- **Informs:** Architectural disclaimer — all rates are filed (not browsable), hence the *indicative-not-bindable* framing throughout.
- **Confidence:** high.

---

## B. Industry Information Bureau (IIB)

### B1. IIB Annual Reports / Segment Reports
- **URL:** https://iib.gov.in/IIB/IIB_AnnualReports.html
- **Type:** Industry data hub
- **Informs:** NIC hazard factors (`nic_hazard_factor.*`) for divisions where IIB publishes (Manufacturing 26-27, IT 62-63, Financial 64-66, Healthcare 86, Transport 49-52, Professional services 74).
- **Confidence:** medium. NIC-division-level loss ratios are coarse — many divisions are PLACEHOLDER.

### B2. IIB Liability Segment Report FY23 (where publicly accessible)
- **URL:** https://iib.gov.in/IIB/Reports.html
- **Type:** Segment report
- **Informs:** Liability ULR bands by industry segment. Where the report is members-only, the parameter is marked PLACEHOLDER.
- **Confidence:** medium.

---

## C. General Insurance Council

### C1. GI Council Segment Statistics
- **URL:** https://www.gicouncil.in
- **Type:** Industry aggregate
- **Informs:** Cross-check on segment premium totals used in median calculations.
- **Confidence:** medium.

---

## D. Reinsurance

### D1. GIC Re Obligatory Cession FY25 Notification
- **URL:** https://www.gicre.in
- **Type:** Regulator (IRDAI) notification
- **Informs:** Obligatory cession % (`expense_components.reinsurance_cession_cost = 0.04`). FY25 cession is 4% (was 5% earlier).
- **Confidence:** high.

---

## E. Cyber / Data Protection

### E1. CERT-In Annual Report 2023
- **URL:** https://www.cert-in.org.in/PDF/CERT-In_Annual_Report_2023.pdf
- **Type:** Statutory body annual report
- **Informs:** Cyber incident frequency anchor (`dpdp_severity.cert_in_fy24_incidents = 13,91,457`). Used in Cyber pricing notes and decline/refer rules.
- **Confidence:** high.

### E2. CERT-In Directions, 28 April 2022 (Sec 70B IT Act)
- **URL:** https://www.cert-in.org.in/PDF/CERT-In_Directions_70B_28.04.2022.pdf
- **Type:** Statutory direction
- **Informs:** Discount for `cert_in_poc_designated` — companies that have notified CERT-In PoC reduce breach response time.
- **Confidence:** medium.

### E3. Digital Personal Data Protection Act 2023
- **URL:** https://www.meity.gov.in/static/uploads/2024/06/2bf1f0e9f04e6fb4f8fef35e82c42aa5.pdf
- **Type:** Statute
- **Informs:** **Severity anchor** — `dpdp_severity.max_penalty_inr = ₹250 crore` per violation (Schedule); Sec 10 (Significant Data Fiduciary obligations); Sec 8(4) (DPIA); Sec 33 (penalties).
- **Confidence:** high.

---

## F. Companies & Securities Law

### F1. Companies Act 2013
- **URL:** https://www.mca.gov.in
- **Type:** Statute
- **Informs:** D&O exposure framing (director duties, related-party transactions, fraud reporting).
- **Confidence:** high.

### F2. SEBI LODR Regulations 2015 (last amended 2024)
- **URL:** https://www.sebi.gov.in/legal/regulations/jul-2024/securities-and-exchange-board-of-india-listing-obligations-and-disclosure-requirements-regulations-2015-last-amended-on-july-10-2024-_85291.html
- **Type:** Regulation
- **Informs:** Pre-IPO and listed-company D&O loading (`stage_factor.pre_ipo`, auto-refer rule for listed companies).
- **Confidence:** high.

### F3. SEBI ICDR Regulations 2018
- **URL:** https://www.sebi.gov.in
- **Type:** Regulation
- **Informs:** S1/DRHP disclosure liability — drives pre-IPO D&O / PI severity uplift.
- **Confidence:** high.

### F4. MCA21 Master Data Portal
- **URL:** https://www.mca.gov.in/mcafoportal/login.do
- **Type:** Public corporate registry
- **Informs:** CIN-driven director count, paid-up capital, director-disqualification status (used by `founder_prior_fraud_event` loading and refer rules).
- **Confidence:** high.

---

## G. Labour & Employment

### G1. Employees' Compensation Act 1923 (and amendments)
- **URL:** https://labour.gov.in/sites/default/files/the_employees_compensation_act1923.pdf
- **Type:** Statute
- **Informs:** Statutory minimum compensation schedule (`base_rate_per_crore.EC.*` calibrated to Schedule IV).
- **Confidence:** high.

### G2. Labour Bureau wage data (Indian Labour Statistics)
- **URL:** https://labourbureau.gov.in
- **Type:** Government statistics
- **Informs:** State-wise wage band for EC exposure scaling.
- **Confidence:** high.

---

## H. Tax & Stamp Duty

### H1. GST Act 2017 / Notification 11/2017-Central Tax (Rate)
- **URL:** https://gstcouncil.gov.in/sites/default/files/Notifications/Notification%20no.%2011%202017%20(CT)Rate.pdf
- **Type:** Statute
- **Informs:** `taxes.gst_rate = 0.18` for insurance services (SAC 9971).
- **Confidence:** high.

### H2. State Stamp Acts
- Maharashtra Stamp Act 1958 — https://igrmaharashtra.gov.in
- Karnataka Stamp Act 1957 — https://stamps.karnataka.gov.in
- Indian Stamp Act 1899 (Delhi/TN/Telangana) — https://legislative.gov.in
- Gujarat Stamp Act 1958 — https://garvi.gujarat.gov.in
- **Informs:** State-specific stamp duty on insurance policies (`taxes.stamp_duty.*`). Typical ₹200 per policy nationwide post-2020 amendments.
- **Confidence:** high.

---

## I. NIC Codes & Economic Classification

### I1. MoSPI NIC 2008 Code List
- **URL:** https://mospi.gov.in/sites/default/files/main_menu/national_industrial_classification/nic_2008_17apr09.pdf
- **Type:** Government statistical classification
- **Informs:** NIC division → hazard factor mapping (`nic_hazard_factor.*`).
- **Confidence:** high.

---

## J. Crime Statistics

### J1. NCRB Crime in India 2023
- **URL:** https://ncrb.gov.in
- **Type:** Government statistics
- **Informs:** State-wise economic offences density — feeds `state_factor` and Crime LOB severity anchor.
- **Confidence:** high.

---

## K. Carrier Brochures (Public PDFs)

All Indian carrier brochures cited inline; URLs below for reference.

| Carrier | Product | URL |
|---|---|---|
| Tata AIG | D&O Liability | https://www.tataaig.com/business-insurance/directors-officers-liability-insurance |
| Tata AIG | Cyber (CyberEdge) | https://www.tataaig.com/business-insurance/cyber-insurance |
| Tata AIG | Professional Indemnity | https://www.tataaig.com/business-insurance/professional-indemnity-insurance |
| Tata AIG | CGL | https://www.tataaig.com/business-insurance/commercial-general-liability |
| ICICI Lombard | D&O | https://www.icicilombard.com/business-insurance/liability-insurance/directors-and-officers-liability-insurance |
| ICICI Lombard | Cyber | https://www.icicilombard.com/business-insurance/cyber-insurance |
| ICICI Lombard | PI / E&O | https://www.icicilombard.com/business-insurance/liability-insurance/professional-indemnity-insurance |
| ICICI Lombard | CGL | https://www.icicilombard.com/business-insurance/liability-insurance/commercial-general-liability |
| ICICI Lombard | Group Personal Accident | https://www.icicilombard.com/group-health-insurance/group-personal-accident-insurance |
| HDFC ERGO | D&O | https://www.hdfcergo.com/commercial-insurance/liability-insurance/directors-officers-liability-insurance |
| HDFC ERGO | Cyber | https://www.hdfcergo.com/commercial-insurance/cyber-insurance |
| HDFC ERGO | Commercial Crime | https://www.hdfcergo.com/commercial-insurance/liability-insurance/commercial-crime-insurance |
| Bajaj Allianz | Cyber Safe | https://www.bajajallianz.com/business-insurance/cyber-safe-insurance.html |

**Confidence:** medium. Public brochures give indicative rates; specific filed rates per insurer are not publicly browsable (no SERFF equivalent in India).

---

## L. Broker Commentary (low-confidence supporting refs only)

### L1. Marsh India D&O Market Outlook (annual)
- **URL:** https://www.marsh.com/in/insights.html
- **Type:** Broker market commentary
- **Informs:** Governance-discount benchmarks, market hardening commentary. Used for loadings/discounts only, never base rates.
- **Confidence:** low.

### L2. WTW India Insurance Marketplace Realities (annual)
- **URL:** https://www.wtwco.com/en-in
- **Type:** Broker market commentary
- **Informs:** Same as Marsh India — discount and loading directional support.
- **Confidence:** low.

---

## M. DPIIT / Startup India

### M1. DPIIT Startup India Recognition Registry
- **URL:** https://www.startupindia.gov.in/content/sih/en/recoginition.html
- **Type:** Government registry
- **Informs:** `dpiit_recognised` discount (carrier goodwill towards recognised startups).
- **Confidence:** medium.

---

## N. Sources I CANNOT fetch in this environment

| Source | Why blocked | What you can drop into `pricing/sources/raw/` |
|---|---|---|
| IIB members-only reports | Login wall | Any IIB report you have member access to (D&O Specific, Cyber, etc.) |
| Insurer-internal rate filings | India has no SERFF equivalent — File-and-Use does not require public posting | N/A — structural reason most factors will carry "medium" or "low" confidence |
| Reinsurance treaty terms | Proprietary | Your treaty summary, if any (raises `reinsurance_cession_cost` confidence) |
| NIC-division-level loss ratios | IIB publishes by broad segment, not by NIC division | Any internal NIC-level loss data your team has |

---

## How to add a new source

1. Drop the PDF in `pricing/sources/raw/<source_name>.pdf` (or just record the URL).
2. Add a numbered entry under the relevant letter section in this file.
3. Update the relevant `source.citation` + `source.url` + `source.accessed` fields in `pricing/parameters.yaml`.
4. Run `python -m pricing.params validate` to confirm the schema is intact.
5. Run `python -m pricing.params edit <path> <new_value> --reason "calibrated to <source>"` to bump confidence if appropriate.

---

## Audit trail

Every edit to `parameters.yaml` via the CLI appends to `pricing/audit_log.csv`:
`timestamp, user, parameter_path, old_value, new_value, reason`.

This file is committed to git on each edit so the MD/CEO can trace exactly when a rate moved, who moved it, and what source justified the move.
