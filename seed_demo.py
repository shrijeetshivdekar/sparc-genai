"""Demo data seed for SPARC Commerce Layer SVP presentation.

Run:  python seed_demo.py
Re-running is safe — wipes commerce tables and reseeds fresh.
"""
from __future__ import annotations
import json, secrets, sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

import db

DB_PATH = db.DB_PATH

# ─── helpers ──────────────────────────────────────────────────
def _id(prefix): return f"{prefix}_" + secrets.token_hex(8)
def _ago(days): return (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
def _date(days_from_today): return (date.today() + timedelta(days=days_from_today)).isoformat()

# ─── wipe existing commerce data ──────────────────────────────
def wipe(conn):
    conn.execute("PRAGMA foreign_keys = OFF")
    for tbl in ("alerts", "gwp_estimates", "pipeline_events", "proposals",
                "analyses", "events", "accounts", "funding_leads", "rms"):
        conn.execute(f"DELETE FROM {tbl}")
    conn.execute("PRAGMA foreign_keys = ON")

# ─── RMs ──────────────────────────────────────────────────────
RMS = [
    {
        "rm_email": "shrijeet.s@icicilombard.com",
        "name": "Shrijeet Shivdekar",
        "phone": "9876543210",
        "office": "ICICI Lombard — Commercial Lines, Mumbai",
        "city": "Mumbai",
    },
    {
        "rm_email": "priya.nair@icicilombard.com",
        "name": "Priya Nair",
        "phone": "9820011223",
        "office": "ICICI Lombard — Commercial Lines, Bengaluru",
        "city": "Bengaluru",
    },
    {
        "rm_email": "arjun.mehta@icicilombard.com",
        "name": "Arjun Mehta",
        "phone": "9833445566",
        "office": "ICICI Lombard — Commercial Lines, Hyderabad",
        "city": "Hyderabad",
    },
]

# ─── Accounts ─────────────────────────────────────────────────
# stage, name, sector, funding_stage, city, rm_email,
# gwp_low_inr, gwp_high_inr, created_days_ago, renewal_due_days, last_engaged_days
ACCOUNTS = [
    # ── CONVERTED (5) ────────────────────────────────────────
    ("converted", "Zeta Payments",   "FinTech",    "Series B+", "Mumbai",    "shrijeet.s@icicilombard.com",  3_500_000, 10_200_000, 90, None, 5),
    ("converted", "Mednova Health",  "HealthTech", "Series A",  "Bengaluru", "priya.nair@icicilombard.com",  820_000,   2_950_000,  80, None, 8),
    ("converted", "Agristack",       "AgriTech",   "Seed",      "Pune",      "arjun.mehta@icicilombard.com", 150_000,   480_000,    70, None, 12),
    ("converted", "Cloudmatrix",     "SaaS",       "Series A",  "Hyderabad", "arjun.mehta@icicilombard.com", 950_000,   3_100_000,  65, None, 10),
    ("converted", "Finwise Capital", "FinTech",    "Series A",  "Mumbai",    "shrijeet.s@icicilombard.com",  700_000,   2_200_000,  55, None, 6),

    # ── PROPOSAL (4) ─────────────────────────────────────────
    ("proposal",  "Krana EdTech",    "EdTech",     "Series A",  "Delhi",     "priya.nair@icicilombard.com",  600_000,   1_900_000,  40, 45, 7),
    ("proposal",  "Orbit Logistics", "Logistics",  "Series B+", "Mumbai",    "shrijeet.s@icicilombard.com",  2_950_000, 9_700_000,  35, 50, 4),
    ("proposal",  "Swiftmed",        "HealthTech", "Seed",      "Chennai",   "arjun.mehta@icicilombard.com", 180_000,   560_000,    30, 55, 9),
    ("proposal",  "Buildpro SaaS",   "SaaS",       "Series A",  "Bengaluru", "priya.nair@icicilombard.com",  880_000,   2_800_000,  25, 60, 3),

    # ── QUOTED (4) ───────────────────────────────────────────
    ("quoted",    "Hyperlocal Now",  "Logistics",  "Seed",      "Bengaluru", "priya.nair@icicilombard.com",  120_000,   390_000,    22, None, 6),
    ("quoted",    "Neobank One",     "FinTech",    "Series A",  "Mumbai",    "shrijeet.s@icicilombard.com",  1_100_000, 3_600_000,  18, None, 5),
    ("quoted",    "Rista Robotics",  "DeepTech",   "Series A",  "Pune",      "arjun.mehta@icicilombard.com", 750_000,   2_400_000,  15, None, 11),
    ("quoted",    "PharmaTrace",     "HealthTech", "Series B+", "Hyderabad", "arjun.mehta@icicilombard.com", 2_200_000, 7_100_000,  12, None, 3),

    # ── ANALYSED (4) ─────────────────────────────────────────
    ("analysed",  "Ruraltech",       "AgriTech",   "Pre-seed",  "Nashik",    "shrijeet.s@icicilombard.com",  40_000,    120_000,    10, None, 2),
    ("analysed",  "Lendright",       "FinTech",    "Seed",      "Mumbai",    "shrijeet.s@icicilombard.com",  200_000,   640_000,    9,  None, 4),
    ("analysed",  "CargoFly",        "Logistics",  "Series A",  "Delhi",     "priya.nair@icicilombard.com",  820_000,   2_600_000,  8,  None, 1),
    ("analysed",  "EduVerse",        "EdTech",     "Seed",      "Bengaluru", "priya.nair@icicilombard.com",  160_000,   510_000,    7,  None, 3),

    # ── PROSPECT (5) ─────────────────────────────────────────
    ("prospect",  "GreenLogix",      "Logistics",  "Series B+", "Bengaluru", "priya.nair@icicilombard.com",  2_950_000, 9_700_000,  6,  None, None),
    ("prospect",  "Acme HealthTech", "HealthTech", "Series A",  "Bengaluru", "arjun.mehta@icicilombard.com", 820_000,   2_950_000,  5,  None, None),
    ("prospect",  "Northstar Pay",   "FinTech",    "Seed",      "Mumbai",    "shrijeet.s@icicilombard.com",  180_000,   570_000,    4,  None, None),
    ("prospect",  "Veda AI",         "SaaS",       "Pre-seed",  "Hyderabad", "arjun.mehta@icicilombard.com", 35_000,    110_000,    3,  None, None),
    ("prospect",  "Payhop",          "FinTech",    "Seed",      "Bengaluru", "priya.nair@icicilombard.com",  190_000,   590_000,    2,  None, None),
]

# ─── Funding leads (unclaimed) ────────────────────────────────
LEADS = [
    ("TrustLayer",    "FinTech",    "Series A",  "Mumbai",    550_000,  1_750_000),
    ("Medi-AI",       "HealthTech", "Seed",      "Bengaluru", 130_000,  420_000),
    ("FreightOS",     "Logistics",  "Series B+", "Delhi",     2_500_000, 8_200_000),
    ("SkillBridge",   "EdTech",     "Pre-seed",  "Pune",      30_000,   95_000),
    ("Cropwise",      "AgriTech",   "Seed",      "Nagpur",    90_000,   290_000),
    ("CyberShield",   "SaaS",       "Series A",  "Hyderabad", 740_000,  2_300_000),
    ("Instacredit",   "FinTech",    "Series B+", "Mumbai",    3_100_000, 9_900_000),
    ("BioSync",       "HealthTech", "Series A",  "Chennai",   680_000,  2_150_000),
]

DISCLAIMER = "Indicative only under IRDAI File-and-Use detariffed regime. Not a bindable quote."
STAGE_ORDER = ["prospect", "analysed", "quoted", "proposal", "converted"]

def seed():
    db.migrate(DB_PATH)
    conn = db.get_conn(DB_PATH)
    with conn:
        wipe(conn)

        # RMs
        for rm in RMS:
            conn.execute(
                "INSERT INTO rms (rm_email, name, phone, office, city) VALUES (?,?,?,?,?)",
                (rm["rm_email"], rm["name"], rm["phone"], rm["office"], rm["city"]),
            )

        # Accounts + GWP estimates + pipeline events + renewal data
        for (stage, name, sector, funding_stage, city, rm_email,
             gwp_low, gwp_high, created_ago, renewal_days, engaged_ago) in ACCOUNTS:

            acct_id = _id("acc")
            profile = json.dumps({"startup_name": name, "sector": sector,
                                   "funding_stage": funding_stage, "city": city})

            renewal_due = _date(renewal_days) if renewal_days else None
            last_engaged = _ago(engaged_ago) if engaged_ago else None

            conn.execute(
                """INSERT INTO accounts
                   (account_id, name, sector, funding_stage, city, profile_json,
                    stage, rm_email, source, renewal_due_on, last_engaged_on,
                    created_at, updated_at)
                   VALUES (?,?,?,?,?,?,?,?,'demo',?,?,?,?)""",
                (acct_id, name, sector, funding_stage, city, profile,
                 stage, rm_email, renewal_due, last_engaged,
                 _ago(created_ago), _ago(max(0, created_ago - 1))),
            )

            est_id = _id("gwp")
            conn.execute(
                """INSERT INTO gwp_estimates
                   (estimate_id, account_id, analysis_id,
                    gwp_low_inr, gwp_high_inr, basis, data_quality, disclaimer)
                   VALUES (?,?,NULL,?,?,'bucket',0.7,?)""",
                (est_id, acct_id, gwp_low, gwp_high, DISCLAIMER),
            )

            # Pipeline events — one per stage transition up to current stage
            cur_idx = STAGE_ORDER.index(stage) if stage in STAGE_ORDER else 0
            for i in range(cur_idx + 1):
                from_s = STAGE_ORDER[i - 1] if i > 0 else None
                to_s   = STAGE_ORDER[i]
                conn.execute(
                    """INSERT INTO pipeline_events
                       (event_id, account_id, from_stage, to_stage, rm_email,
                        gwp_low_inr, gwp_high_inr, created_at)
                       VALUES (?,?,?,?,?,?,?,?)""",
                    (_id("pe"), acct_id, from_s, to_s, rm_email,
                     gwp_low, gwp_high,
                     _ago(created_ago - i * 5)),
                )

        # Alerts — renewals + at_risk for proposal/quoted accounts nearing renewal
        alert_accounts = conn.execute(
            "SELECT account_id, name, renewal_due_on, last_engaged_on, rm_email, "
            "sector, funding_stage FROM accounts WHERE renewal_due_on IS NOT NULL"
        ).fetchall()

        for row in alert_accounts:
            acct_id = row["account_id"]
            gwp = conn.execute(
                "SELECT gwp_low_inr, gwp_high_inr FROM gwp_estimates WHERE account_id=? LIMIT 1",
                (acct_id,)
            ).fetchone()
            if not gwp: continue
            lo, hi = gwp["gwp_low_inr"], gwp["gwp_high_inr"]
            due   = row["renewal_due_on"]
            eng   = row["last_engaged_on"]
            days_to = (date.fromisoformat(due) - date.today()).days

            # renewal alert
            conn.execute(
                """INSERT INTO alerts
                   (alert_id, account_id, type, reason,
                    trigger_detail_json, delta_gwp_low_inr, delta_gwp_high_inr, status)
                   VALUES (?,?,'renewal',?,?,?,?,'open')""",
                (_id("al"), acct_id,
                 f"Renewal due in {days_to} days — protect existing GWP.",
                 json.dumps({"field":"renewal_due_on","days_to_renewal":days_to}),
                 lo, hi),
            )
            # at_risk if no engagement
            if not eng:
                conn.execute(
                    """INSERT INTO alerts
                       (alert_id, account_id, type, reason,
                        trigger_detail_json, delta_gwp_low_inr, delta_gwp_high_inr, status)
                       VALUES (?,?,'at_risk',?,?,?,?,'open')""",
                    (_id("al"), acct_id,
                     f"Renewal due in {days_to}d and no engagement recorded — GWP at risk.",
                     json.dumps({"field":"engagement","days_to_renewal":days_to}),
                     -hi, -lo),
                )

        # Upsell alert for one high-value prospect
        upsell_acct = conn.execute(
            "SELECT account_id FROM accounts WHERE funding_stage='Series A' "
            "AND stage='prospect' LIMIT 1"
        ).fetchone()
        if upsell_acct:
            conn.execute(
                """INSERT INTO alerts
                   (alert_id, account_id, type, reason,
                    trigger_detail_json, delta_gwp_low_inr, delta_gwp_high_inr, status)
                   VALUES (?,?,'upsell',?,?,?,?,'open')""",
                (_id("al"), upsell_acct["account_id"],
                 "Stage progression Series A → Series B+ unlocks higher indicative limits.",
                 json.dumps({"field":"funding_stage","old":"Series A","new":"Series B+"}),
                 200_000, 850_000),
            )

        # Funding leads (unclaimed)
        for (company, sector, stage, city, lo, hi) in LEADS:
            conn.execute(
                """INSERT INTO funding_leads
                   (lead_id, company, sector, stage, city,
                    est_gwp_low_inr, est_gwp_high_inr, status, source)
                   VALUES (?,?,?,?,?,?,?,'open','demo_seed')""",
                (_id("lead"), company, sector, stage, city, lo, hi),
            )

    conn.close()
    print("Seeded RMs:", len(RMS))
    print("Seeded Accounts:", len(ACCOUNTS))
    print("Seeded Funding Leads:", len(LEADS))

    # Summary
    conn2 = db.get_conn(DB_PATH)
    for row in conn2.execute(
        "SELECT stage, COUNT(*) n FROM accounts GROUP BY stage ORDER BY stage"
    ).fetchall():
        print(f"  accounts.{row['stage']}: {row['n']}")
    alerts_n = conn2.execute("SELECT COUNT(*) FROM alerts WHERE status='open'").fetchone()[0]
    print(f"  open alerts: {alerts_n}")
    conn2.close()

if __name__ == "__main__":
    seed()
