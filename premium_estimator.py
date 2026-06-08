STARTUP_SIZE_BUCKETS = {
    "micro": {"stages": ["Pre-seed", "Seed"], "team_max": 25},
    "small": {"stages": ["Series A"], "team_max": 100},
    "growth": {"stages": ["Series B+"], "team_max": 500},
}

# All ranges = rate × typical_SI ± 20%.
# Typical SIs: micro ₹2Cr liability/₹3Cr property/15 emp,
#              small ₹5Cr liability/₹10Cr property/75 emp (ICICI Lombard Jun 2026 anchors),
#              growth ₹25Cr liability/₹40Cr property/200 emp.
PREMIUM_RANGES = {
    # ── ICICI Lombard verified rates (Jun 2026) — ±20% ────────────────────────────
    "cyber_liability": {           # 0.46 L/Cr — ICICI Lombard verified
        "micro":  {"min_lakh": 0.74, "max_lakh": 1.10, "basis": "₹2Cr SI × 0.46 L/Cr ±20% — ICICI Lombard verified"},
        "small":  {"min_lakh": 1.84, "max_lakh": 2.76, "basis": "₹5Cr SI × 0.46 L/Cr ±20% — ICICI Lombard verified"},
        "growth": {"min_lakh": 9.20, "max_lakh": 13.80, "basis": "₹25Cr SI × 0.46 L/Cr ±20% — ICICI Lombard verified"},
    },
    "dno_liability": {             # 0.15 L/Cr — ICICI Lombard verified
        "micro":  {"min_lakh": 0.24, "max_lakh": 0.36, "basis": "₹2Cr SI × 0.15 L/Cr ±20% — ICICI Lombard verified"},
        "small":  {"min_lakh": 0.60, "max_lakh": 0.90, "basis": "₹5Cr SI × 0.15 L/Cr ±20% — ICICI Lombard verified"},
        "growth": {"min_lakh": 3.00, "max_lakh": 4.50, "basis": "₹25Cr SI × 0.15 L/Cr ±20% — ICICI Lombard verified"},
    },
    "professional_indemnity": {    # 0.46 L/Cr — ICICI Lombard verified
        "micro":  {"min_lakh": 0.74, "max_lakh": 1.10, "basis": "₹2Cr SI × 0.46 L/Cr ±20% — ICICI Lombard verified"},
        "small":  {"min_lakh": 1.84, "max_lakh": 2.76, "basis": "₹5Cr SI × 0.46 L/Cr ±20% — ICICI Lombard verified"},
        "growth": {"min_lakh": 9.20, "max_lakh": 13.80, "basis": "₹25Cr SI × 0.46 L/Cr ±20% — ICICI Lombard verified"},
    },
    "comprehensive_general_liability": {  # 0.14 L/Cr — ICICI Lombard verified
        "micro":  {"min_lakh": 0.22, "max_lakh": 0.34, "basis": "₹2Cr limit × 0.14 L/Cr ±20% — ICICI Lombard verified"},
        "small":  {"min_lakh": 0.56, "max_lakh": 0.84, "basis": "₹5Cr limit × 0.14 L/Cr ±20% — ICICI Lombard verified"},
        "growth": {"min_lakh": 2.24, "max_lakh": 3.36, "basis": "₹20Cr limit × 0.14 L/Cr ±20% — ICICI Lombard verified"},
    },
    "public_liability": {          # 0.40 L/Cr — ICICI Lombard verified
        "micro":  {"min_lakh": 0.32, "max_lakh": 0.48, "basis": "₹1Cr limit × 0.40 L/Cr ±20% — ICICI Lombard verified"},
        "small":  {"min_lakh": 0.64, "max_lakh": 0.96, "basis": "₹2Cr limit × 0.40 L/Cr ±20% — ICICI Lombard verified"},
        "growth": {"min_lakh": 4.80, "max_lakh": 7.20, "basis": "₹15Cr limit × 0.40 L/Cr ±20% — ICICI Lombard verified"},
    },
    "employment_practices": {      # 0.70 L/Cr — ICICI Lombard verified
        "micro":  {"min_lakh": 0.56, "max_lakh": 0.84, "basis": "₹1Cr limit × 0.70 L/Cr ±20% — ICICI Lombard verified"},
        "small":  {"min_lakh": 1.12, "max_lakh": 1.68, "basis": "₹2Cr limit × 0.70 L/Cr ±20% — ICICI Lombard verified"},
        "growth": {"min_lakh": 5.60, "max_lakh": 8.40, "basis": "₹10Cr limit × 0.70 L/Cr ±20% — ICICI Lombard verified"},
    },
    "product_liability": {         # 0.35 L/Cr — ICICI Lombard verified
        "micro":  {"min_lakh": 0.28, "max_lakh": 0.42, "basis": "₹1Cr limit × 0.35 L/Cr ±20% — ICICI Lombard verified"},
        "small":  {"min_lakh": 0.56, "max_lakh": 0.84, "basis": "₹2Cr limit × 0.35 L/Cr ±20% — ICICI Lombard verified"},
        "growth": {"min_lakh": 4.20, "max_lakh": 6.30, "basis": "₹15Cr limit × 0.35 L/Cr ±20% — ICICI Lombard verified"},
    },
    "property_fire": {             # 0.50 L/Cr — ICICI Lombard verified
        "micro":  {"min_lakh": 1.20, "max_lakh": 1.80, "basis": "₹3Cr SI × 0.50 L/Cr ±20% — ICICI Lombard verified"},
        "small":  {"min_lakh": 4.00, "max_lakh": 6.00, "basis": "₹10Cr SI × 0.50 L/Cr ±20% — ICICI Lombard verified"},
        "growth": {"min_lakh": 16.00, "max_lakh": 24.00, "basis": "₹40Cr SI × 0.50 L/Cr ±20% — ICICI Lombard verified"},
    },
    "property_all_risk": {         # 0.50 L/Cr — ICICI Lombard verified
        "micro":  {"min_lakh": 1.20, "max_lakh": 1.80, "basis": "₹3Cr SI × 0.50 L/Cr ±20% — ICICI Lombard verified"},
        "small":  {"min_lakh": 4.00, "max_lakh": 6.00, "basis": "₹10Cr SI × 0.50 L/Cr ±20% — ICICI Lombard verified"},
        "growth": {"min_lakh": 16.00, "max_lakh": 24.00, "basis": "₹40Cr SI × 0.50 L/Cr ±20% — ICICI Lombard verified"},
    },
    "engineering": {               # 0.40 L/Cr — ICICI Lombard verified
        "micro":  {"min_lakh": 0.64, "max_lakh": 0.96, "basis": "₹2Cr project × 0.40 L/Cr ±20% — ICICI Lombard verified"},
        "small":  {"min_lakh": 2.56, "max_lakh": 3.84, "basis": "₹8Cr project × 0.40 L/Cr ±20% — ICICI Lombard verified"},
        "growth": {"min_lakh": 8.00, "max_lakh": 12.00, "basis": "₹25Cr project × 0.40 L/Cr ±20% — ICICI Lombard verified"},
    },
    "machinery_breakdown": {       # 0.25 L/Cr — ICICI Lombard verified
        "micro":  {"min_lakh": 0.20, "max_lakh": 0.30, "basis": "₹1Cr machinery SI × 0.25 L/Cr ±20% — ICICI Lombard verified"},
        "small":  {"min_lakh": 1.00, "max_lakh": 1.50, "basis": "₹5Cr machinery SI × 0.25 L/Cr ±20% — ICICI Lombard verified"},
        "growth": {"min_lakh": 3.00, "max_lakh": 4.50, "basis": "₹15Cr machinery SI × 0.25 L/Cr ±20% — ICICI Lombard verified"},
    },
    "electronic_equipment": {      # 0.25 L/Cr — ICICI Lombard verified
        "micro":  {"min_lakh": 0.20, "max_lakh": 0.30, "basis": "₹1Cr EEI SI × 0.25 L/Cr ±20% — ICICI Lombard verified"},
        "small":  {"min_lakh": 1.00, "max_lakh": 1.50, "basis": "₹5Cr EEI SI × 0.25 L/Cr ±20% — ICICI Lombard verified"},
        "growth": {"min_lakh": 3.00, "max_lakh": 4.50, "basis": "₹15Cr EEI SI × 0.25 L/Cr ±20% — ICICI Lombard verified"},
    },
    "contractors_all_risk": {      # 1.00 L/Cr — ICICI Lombard verified
        "micro":  {"min_lakh": 1.60, "max_lakh": 2.40, "basis": "₹2Cr project × 1.00 L/Cr ±20% — ICICI Lombard verified"},
        "small":  {"min_lakh": 5.60, "max_lakh": 8.40, "basis": "₹7Cr project × 1.00 L/Cr ±20% — ICICI Lombard verified"},
        "growth": {"min_lakh": 24.00, "max_lakh": 36.00, "basis": "₹30Cr project × 1.00 L/Cr ±20% — ICICI Lombard verified"},
    },
    "enterprise_secure": {         # 0.000445729294/₹ flat — ICICI Lombard verified
        "micro":  {"min_lakh": 1.78, "max_lakh": 2.68, "basis": "₹25Cr total SI × 0.044573‰ ±20% — ICICI Lombard verified"},
        "small":  {"min_lakh": 1.78, "max_lakh": 2.68, "basis": "₹25Cr total SI × 0.044573‰ ±20% — ICICI Lombard verified"},
        "growth": {"min_lakh": 5.35, "max_lakh": 8.02, "basis": "₹75Cr total SI × 0.044573‰ ±20% — ICICI Lombard verified"},
    },
    # ── Market estimates (named sources) — ±35% ───────────────────────────────────
    "business_interruption": {     # 0.22 L/Cr; market estimate (Trust Risk Control / general BI pricing)
        "micro":  {"min_lakh": 0.14, "max_lakh": 0.30, "basis": "₹1Cr BI SI × 0.22 L/Cr ±35% — market estimate"},
        "small":  {"min_lakh": 0.72, "max_lakh": 1.49, "basis": "₹5Cr BI SI × 0.22 L/Cr ±35% — market estimate"},
        "growth": {"min_lakh": 2.15, "max_lakh": 4.46, "basis": "₹15Cr BI SI × 0.22 L/Cr ±35% — market estimate"},
    },
    "employees_comp": {            # 0.40 L/Cr payroll; market estimate (IRDAI WC office-class rate)
        "micro":  {"min_lakh": 0.26, "max_lakh": 0.54, "basis": "₹1Cr payroll × 0.40 L/Cr ±35% — market estimate (IRDAI WC)"},
        "small":  {"min_lakh": 1.30, "max_lakh": 2.70, "basis": "₹5Cr payroll × 0.40 L/Cr ±35% — market estimate (IRDAI WC)"},
        "growth": {"min_lakh": 5.20, "max_lakh": 10.80, "basis": "₹20Cr payroll × 0.40 L/Cr ±35% — market estimate (IRDAI WC)"},
    },
    "employee_health": {           # 0.13 L/emp; market estimate (NivaaBupa / Pazcare group health data)
        "micro":  {"min_lakh": 1.27, "max_lakh": 2.63, "basis": "15 emp × ₹13K/emp ±35% — market estimate (NivaaBupa/Pazcare)"},
        "small":  {"min_lakh": 6.34, "max_lakh": 13.16, "basis": "75 emp × ₹13K/emp ±35% — market estimate (NivaaBupa/Pazcare)"},
        "growth": {"min_lakh": 16.90, "max_lakh": 35.10, "basis": "200 emp × ₹13K/emp ±35% — market estimate (NivaaBupa/Pazcare)"},
    },
    "group_pa": {                  # 0.09 L/emp; market estimate (Bajaj Finserv group PA market)
        "micro":  {"min_lakh": 0.88, "max_lakh": 1.82, "basis": "15 emp × ₹9K/emp ±35% — market estimate (Bajaj Finserv)"},
        "small":  {"min_lakh": 4.39, "max_lakh": 9.11, "basis": "75 emp × ₹9K/emp ±35% — market estimate (Bajaj Finserv)"},
        "growth": {"min_lakh": 11.70, "max_lakh": 24.30, "basis": "200 emp × ₹9K/emp ±35% — market estimate (Bajaj Finserv)"},
    },
    "marine_transit": {            # 0.40 L/Cr; market estimate (Pazago domestic marine cargo rate)
        "micro":  {"min_lakh": 0.52, "max_lakh": 1.08, "basis": "₹2Cr turnover × 0.40 L/Cr ±35% — market estimate (Pazago)"},
        "small":  {"min_lakh": 2.08, "max_lakh": 4.32, "basis": "₹8Cr turnover × 0.40 L/Cr ±35% — market estimate (Pazago)"},
        "growth": {"min_lakh": 7.80, "max_lakh": 16.20, "basis": "₹30Cr turnover × 0.40 L/Cr ±35% — market estimate (Pazago)"},
    },
    "trade_credit": {              # 0.40 L/Cr; market estimate (Allianz Trade receivables rate)
        "micro":  {"min_lakh": 0.52, "max_lakh": 1.08, "basis": "₹2Cr receivables × 0.40 L/Cr ±35% — market estimate (Allianz Trade)"},
        "small":  {"min_lakh": 2.08, "max_lakh": 4.32, "basis": "₹8Cr receivables × 0.40 L/Cr ±35% — market estimate (Allianz Trade)"},
        "growth": {"min_lakh": 7.80, "max_lakh": 16.20, "basis": "₹30Cr receivables × 0.40 L/Cr ±35% — market estimate (Allianz Trade)"},
    },
    "surety": {                    # 0.45 L/Cr; market estimate (IRDAI Surety Guidelines 2022)
        "micro":  {"min_lakh": 0.59, "max_lakh": 1.22, "basis": "₹2Cr bond × 0.45 L/Cr ±35% — market estimate (IRDAI Surety Guidelines)"},
        "small":  {"min_lakh": 2.93, "max_lakh": 6.08, "basis": "₹10Cr bond × 0.45 L/Cr ±35% — market estimate (IRDAI Surety Guidelines)"},
        "growth": {"min_lakh": 8.78, "max_lakh": 18.23, "basis": "₹30Cr bond × 0.45 L/Cr ±35% — market estimate (IRDAI Surety Guidelines)"},
    },
    "crime_fidelity": {            # 0.35 L/Cr; market estimate
        "micro":  {"min_lakh": 0.11, "max_lakh": 0.24, "basis": "₹50L limit × 0.35 L/Cr ±35% — market estimate"},
        "small":  {"min_lakh": 0.46, "max_lakh": 0.95, "basis": "₹2Cr limit × 0.35 L/Cr ±35% — market estimate"},
        "growth": {"min_lakh": 2.28, "max_lakh": 4.73, "basis": "₹10Cr limit × 0.35 L/Cr ±35% — market estimate"},
    },
    "money_insurance": {           # 0.35 L/Cr; market estimate
        "micro":  {"min_lakh": 0.05, "max_lakh": 0.09, "basis": "₹20L cash × 0.35 L/Cr ±35% — market estimate"},
        "small":  {"min_lakh": 0.23, "max_lakh": 0.47, "basis": "₹1Cr cash × 0.35 L/Cr ±35% — market estimate"},
        "growth": {"min_lakh": 1.14, "max_lakh": 2.36, "basis": "₹5Cr cash × 0.35 L/Cr ±35% — market estimate"},
    },
    "motor_fleet": {               # 0.18 L/vehicle; market estimate (commercial motor fleet rate)
        "micro":  {"min_lakh": 0.59, "max_lakh": 1.22, "basis": "5 vehicles × ₹18K/vehicle ±35% — market estimate"},
        "small":  {"min_lakh": 2.34, "max_lakh": 4.86, "basis": "20 vehicles × ₹18K/vehicle ±35% — market estimate"},
        "growth": {"min_lakh": 11.70, "max_lakh": 24.30, "basis": "100 vehicles × ₹18K/vehicle ±35% — market estimate"},
    },
    "drone_insurance": {           # 0.42 L/Cr; market estimate (limited market data)
        "micro":  {"min_lakh": 0.14, "max_lakh": 0.28, "basis": "₹50L hull × 0.42 L/Cr ±35% — market estimate (limited data)"},
        "small":  {"min_lakh": 0.55, "max_lakh": 1.13, "basis": "₹2Cr hull × 0.42 L/Cr ±35% — market estimate (limited data)"},
        "growth": {"min_lakh": 2.73, "max_lakh": 5.67, "basis": "₹10Cr hull × 0.42 L/Cr ±35% — market estimate (limited data)"},
    },
    "group_criti_shield": {        # 0.05 L/emp; market estimate (critical illness rider market India)
        "micro":  {"min_lakh": 0.49, "max_lakh": 1.01, "basis": "15 emp × ₹5K/emp ±35% — market estimate (India CI rider)"},
        "small":  {"min_lakh": 2.44, "max_lakh": 5.06, "basis": "75 emp × ₹5K/emp ±35% — market estimate (India CI rider)"},
        "growth": {"min_lakh": 6.50, "max_lakh": 13.50, "basis": "200 emp × ₹5K/emp ±35% — market estimate (India CI rider)"},
    },
    "group_hospishield": {         # 0.06 L/emp; market estimate (hospital daily cash market India)
        "micro":  {"min_lakh": 0.59, "max_lakh": 1.22, "basis": "15 emp × ₹6K/emp ±35% — market estimate (India hosp cash)"},
        "small":  {"min_lakh": 2.93, "max_lakh": 6.08, "basis": "75 emp × ₹6K/emp ±35% — market estimate (India hosp cash)"},
        "growth": {"min_lakh": 7.80, "max_lakh": 16.20, "basis": "200 emp × ₹6K/emp ±35% — market estimate (India hosp cash)"},
    },
    # ── Heuristic estimates — ±35% ────────────────────────────────────────────────
    "healthcare_pi": {             # 0.95 L/Cr; heuristic estimate
        "micro":  {"min_lakh": 1.24, "max_lakh": 2.57, "basis": "₹2Cr limit × 0.95 L/Cr ±35% — heuristic estimate"},
        "small":  {"min_lakh": 3.09, "max_lakh": 6.41, "basis": "₹5Cr limit × 0.95 L/Cr ±35% — heuristic estimate"},
        "growth": {"min_lakh": 12.35, "max_lakh": 25.65, "basis": "₹20Cr limit × 0.95 L/Cr ±35% — heuristic estimate"},
    },
    "financial_services_pi": {     # 1.05 L/Cr; heuristic estimate
        "micro":  {"min_lakh": 1.37, "max_lakh": 2.84, "basis": "₹2Cr limit × 1.05 L/Cr ±35% — heuristic estimate"},
        "small":  {"min_lakh": 3.41, "max_lakh": 7.09, "basis": "₹5Cr limit × 1.05 L/Cr ±35% — heuristic estimate"},
        "growth": {"min_lakh": 13.65, "max_lakh": 28.35, "basis": "₹20Cr limit × 1.05 L/Cr ±35% — heuristic estimate"},
    },
    "payment_protection": {        # 0.65 L/Cr; heuristic estimate
        "micro":  {"min_lakh": 0.85, "max_lakh": 1.76, "basis": "₹2Cr limit × 0.65 L/Cr ±35% — heuristic estimate"},
        "small":  {"min_lakh": 2.11, "max_lakh": 4.39, "basis": "₹5Cr limit × 0.65 L/Cr ±35% — heuristic estimate"},
        "growth": {"min_lakh": 8.45, "max_lakh": 17.55, "basis": "₹20Cr limit × 0.65 L/Cr ±35% — heuristic estimate"},
    },
    "product_recall": {            # 0.85 L/Cr; heuristic estimate
        "micro":  {"min_lakh": 0.55, "max_lakh": 1.15, "basis": "₹1Cr limit × 0.85 L/Cr ±35% — heuristic estimate"},
        "small":  {"min_lakh": 2.76, "max_lakh": 5.74, "basis": "₹5Cr limit × 0.85 L/Cr ±35% — heuristic estimate"},
        "growth": {"min_lakh": 11.05, "max_lakh": 22.95, "basis": "₹20Cr limit × 0.85 L/Cr ±35% — heuristic estimate"},
    },
    "event_production": {          # 0.60 L/Cr; heuristic estimate
        "micro":  {"min_lakh": 0.39, "max_lakh": 0.81, "basis": "₹1Cr budget × 0.60 L/Cr ±35% — heuristic estimate"},
        "small":  {"min_lakh": 1.95, "max_lakh": 4.05, "basis": "₹5Cr budget × 0.60 L/Cr ±35% — heuristic estimate"},
        "growth": {"min_lakh": 7.80, "max_lakh": 16.20, "basis": "₹20Cr budget × 0.60 L/Cr ±35% — heuristic estimate"},
    },
    "key_person": {                # ~1.0 L/Cr; heuristic estimate
        "micro":  {"min_lakh": 1.30, "max_lakh": 2.70, "basis": "₹2Cr cover × ~1.0 L/Cr ±35% — heuristic estimate"},
        "small":  {"min_lakh": 3.25, "max_lakh": 6.75, "basis": "₹5Cr cover × ~1.0 L/Cr ±35% — heuristic estimate"},
        "growth": {"min_lakh": 9.75, "max_lakh": 20.25, "basis": "₹15Cr cover × ~1.0 L/Cr ±35% — heuristic estimate"},
    },
    "msme_suraksha": {             # 0.50 L/Cr; heuristic estimate
        "micro":  {"min_lakh": 0.16, "max_lakh": 0.34, "basis": "₹50L SI × 0.50 L/Cr ±35% — heuristic estimate"},
        "small":  {"min_lakh": 0.65, "max_lakh": 1.35, "basis": "₹2Cr SI × 0.50 L/Cr ±35% — heuristic estimate"},
        "growth": {"min_lakh": 3.25, "max_lakh": 6.75, "basis": "₹10Cr SI × 0.50 L/Cr ±35% — heuristic estimate"},
    },
    "gadget_equipment": {          # ~1.5 L/Cr; heuristic estimate
        "micro":  {"min_lakh": 0.20, "max_lakh": 0.41, "basis": "₹20L equipment × 1.5 L/Cr ±35% — heuristic estimate"},
        "small":  {"min_lakh": 0.98, "max_lakh": 2.03, "basis": "₹1Cr equipment × 1.5 L/Cr ±35% — heuristic estimate"},
        "growth": {"min_lakh": 4.88, "max_lakh": 10.13, "basis": "₹5Cr equipment × 1.5 L/Cr ±35% — heuristic estimate"},
    },
    "clinical_trials": {           # specialist product; heuristic estimate
        "micro":  {"min_lakh": 1.63, "max_lakh": 3.38, "basis": "Phase 1 specialist rate ±35% — heuristic estimate"},
        "small":  {"min_lakh": 5.20, "max_lakh": 10.80, "basis": "Phase 2 specialist rate ±35% — heuristic estimate"},
        "growth": {"min_lakh": 16.90, "max_lakh": 35.10, "basis": "Phase 3 specialist rate ±35% — heuristic estimate"},
    },
    "business_edge": {             # package ~0.50 L/Cr; heuristic estimate
        "micro":  {"min_lakh": 0.98, "max_lakh": 2.03, "basis": "₹3Cr SI package × 0.50 L/Cr ±35% — heuristic estimate"},
        "small":  {"min_lakh": 3.25, "max_lakh": 6.75, "basis": "₹10Cr SI package × 0.50 L/Cr ±35% — heuristic estimate"},
        "growth": {"min_lakh": 9.75, "max_lakh": 20.25, "basis": "₹30Cr SI package × 0.50 L/Cr ±35% — heuristic estimate"},
    },
}

BENCHMARK_STANDARD_ASSUMPTIONS = {
    "cyber_liability": "Standard startup cyber limit, India-first operations, basic controls, no confirmed prior claims.",
    "dno_liability": "Unlisted Indian startup, institutional investor exposure where applicable, no IPO/M&A/restatement facts supplied.",
    "professional_indemnity": "B2B software/services or professional work with standard contract wording and no known claims.",
    "employee_health": "Employee-only group health benchmark without dependent, maternity, PED, age-band, or claims-census calibration.",
    "property_fire": "One-location property benchmark on reinstatement-style asset values with ordinary protections.",
    "property_all_risk": "Asset-heavy startup benchmark with ordinary occupancy, protection, and catastrophe assumptions.",
    "marine_transit": "Annual domestic transit turnover benchmark with standard packed non-hazardous goods and ordinary routes.",
    "trade_credit": "Indicative receivables/turnover benchmark without debtor-book concentration or payment-tenor data.",
}

BENCHMARK_SOURCE_TYPES = {
    "cyber_liability": "market_observation",
    "dno_liability": "market_observation",
    "professional_indemnity": "heuristic",
    "employee_health": "market_observation",
    "property_fire": "public_source",
    "property_all_risk": "public_source",
    "marine_transit": "heuristic",
    "trade_credit": "heuristic",
}

BENCHMARK_CATALOG = {
    product_key: {
        bucket: {
            **values,
            "product_key": product_key,
            "startup_segment": bucket,
            "sector_cluster": "general_startup",
            "standard_assumptions": BENCHMARK_STANDARD_ASSUMPTIONS.get(
                product_key,
                "Directional startup benchmark under ordinary controls, no confirmed prior claims, and standard Indian operations.",
            ),
            "base_exposure_or_plan": values.get("basis", ""),
            "source_type": BENCHMARK_SOURCE_TYPES.get(product_key, "heuristic"),
            "last_calibration": "2026-05",
            "comparability_status": "assumption_led",
        }
        for bucket, values in buckets.items()
    }
    for product_key, buckets in PREMIUM_RANGES.items()
}

PREMIUM_FOOTNOTE = (
    "Directional benchmark only. Ranges are assumption-led and are not bindable "
    "quotes, insurer-approved tariffs, or final underwriting rates. Actual premium "
    "depends on selected limits, census/asset schedules, claims history, controls, "
    "policy wording, deductibles, exclusions, taxes, and underwriter appetite. "
    "Public and market references support product structure and order-of-magnitude "
    "context; exact rate curves remain heuristic until calibrated against real "
    "quote and placement data."
)


def get_size_bucket(funding_stage: str, team_size: int) -> str:
    if funding_stage in STARTUP_SIZE_BUCKETS["micro"]["stages"] and team_size <= 25:
        return "micro"
    if funding_stage in STARTUP_SIZE_BUCKETS["growth"]["stages"]:
        return "growth"
    return "small"


def estimate_premium(product_key: str, size_bucket: str) -> dict | None:
    return BENCHMARK_CATALOG.get(product_key, {}).get(size_bucket)


def format_premium(min_lakh: float, max_lakh: float) -> str:
    return f"INR {min_lakh:.1f} - {max_lakh:.1f} lakhs"
