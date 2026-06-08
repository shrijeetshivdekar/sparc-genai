import os, sys, io, contextlib
from pathlib import Path

for line in Path('.env').read_text().splitlines():
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        k, _, v = line.partition('=')
        os.environ.setdefault(k.strip(), v.strip())

# Disable Gemini unless explicitly opted in — this test validates deterministic logic.
if not os.environ.get("GEMINI_ENABLED"):
    os.environ["GEMINI_API_KEY"] = ""

sys.path.insert(0, 'startup_shield_web')
import server

profiles = [
    ("BharatPe (Fintech, Series B+, payment, RBI+DPDP)", {
        "startup_name": "BharatPe", "sector": "Fintech", "funding_stage": "Series B+",
        "team_size": 900, "revenue_cr": 1400, "business_model": "B2B", "operations": "Digital-only",
        "physical_assets": "none", "data_handled": ["PII", "payment_data"],
        "regulatory": ["RBI", "DPDP", "MCA"], "data_records_lakhs": 50,
        "data_sensitivity": "High", "customer_type": ["SME"],
        "payment_or_card_program": True, "ai_in_product": False,
        "healthcare_operations": False, "b2b_pct": 90, "export_eu_pct": 0,
    }),
    ("PayAI (Seed fintech, AI payments, 15 people)", {
        "startup_name": "PayAI", "sector": "Fintech", "funding_stage": "Seed",
        "team_size": 15, "revenue_cr": 0, "business_model": "B2B", "operations": "Digital-only",
        "physical_assets": "none", "data_handled": ["PII", "payment_data"],
        "regulatory": ["RBI", "DPDP"], "data_records_lakhs": 2,
        "data_sensitivity": "High", "customer_type": ["SME", "enterprise"],
        "payment_or_card_program": True, "ai_in_product": True,
        "healthcare_operations": False, "b2b_pct": 100, "export_eu_pct": 0,
    }),
    ("Zepto (Quick Commerce, Series B+, warehouse, FSSAI)", {
        "startup_name": "Zepto", "sector": "Quick Commerce", "funding_stage": "Series B+",
        "team_size": 20000, "revenue_cr": 4454, "business_model": "B2C", "operations": "Hybrid",
        "physical_assets": "warehouse", "data_handled": ["PII", "payment_data"],
        "regulatory": ["DPDP", "FSSAI", "GST"], "data_records_lakhs": 500,
        "data_sensitivity": "High", "customer_type": ["consumer"],
        "payment_or_card_program": True, "ai_in_product": False,
        "healthcare_operations": False, "b2b_pct": 0, "export_eu_pct": 0,
    }),
    ("CareOS (Healthtech Series A, AI, EU exports)", {
        "startup_name": "CareOS", "sector": "Healthtech", "funding_stage": "Series A",
        "team_size": 80, "revenue_cr": 12, "business_model": "B2B", "operations": "Digital-only",
        "physical_assets": "none", "data_handled": ["PII", "health_data"],
        "regulatory": ["DPDP", "IRDAI"], "data_records_lakhs": 8,
        "data_sensitivity": "High", "customer_type": ["enterprise"],
        "payment_or_card_program": False, "ai_in_product": True,
        "healthcare_operations": True, "b2b_pct": 100, "export_eu_pct": 30,
    }),
    ("NovaBrew (Pre-seed D2C, no data, no revenue)", {
        "startup_name": "NovaBrew", "sector": "Consumer Brands", "funding_stage": "Pre-seed",
        "team_size": 8, "revenue_cr": 0, "business_model": "B2C", "operations": "Hybrid",
        "physical_assets": "inventory", "data_handled": [],
        "regulatory": ["FSSAI"], "data_records_lakhs": 0,
        "data_sensitivity": "Low", "customer_type": ["consumer"],
        "payment_or_card_program": False, "ai_in_product": False,
        "healthcare_operations": False, "b2b_pct": 0, "export_eu_pct": 0,
    }),
]

for label, prof in profiles:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        result = server.score(prof)
    bm = result.get("bundle_match") or {}
    sc = result.get("scores") or {}
    bullets = server.build_pitch_bullets(prof, bm, sc, None)
    print(f"\n{'='*65}")
    print(f">>> {label}")
    print(f"    Bundle: {bm.get('name','?')}")
    print(f"    Mandatory: {bm.get('mandatory_covers',[])[:4]}")
    for i, b in enumerate(bullets, 1):
        print(f"\n  {i}. {b}")
