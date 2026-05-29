# Backend Schema — SPARC Commerce Layer (v1)

**Engine:** SQLite (pilot), path from `SPARC_DB_PATH`; portable to Postgres for production (`SPARC_DB_URL`).
**Migrations:** idempotent, run on boot via `db.migrate()`. All timestamps UTC ISO-8601 TEXT. All money in **paise-free INR integers** (rupees) to avoid float drift; ranges stored as `_low` / `_high` pairs.

---

## 1. Entity overview

```
accounts ──1:N── analyses ──1:1── gwp_estimates
   │                                  
   ├──1:N── pipeline_events            
   ├──1:N── alerts                     
   ├──1:N── proposals                  
   └──N:1── rms                        

funding_leads ──(on claim)──► accounts
events  (append-only activity log, FK to rms + accounts)
```

---

## 2. Tables

### `rms`
Relationship managers. Seeded from `contacts.json`.
```sql
CREATE TABLE IF NOT EXISTS rms (
  rm_email    TEXT PRIMARY KEY,
  name        TEXT NOT NULL,
  phone       TEXT,
  office      TEXT,
  city        TEXT,
  created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
```

### `accounts`
A startup tracked in the pipeline.
```sql
CREATE TABLE IF NOT EXISTS accounts (
  account_id     TEXT PRIMARY KEY,            -- 'acc_' + ulid
  name           TEXT NOT NULL,
  sector         TEXT,
  sub_sector     TEXT,
  funding_stage  TEXT,                        -- Pre-seed | Seed | Series A | Series B+ | Growth
  team_size      INTEGER,
  city           TEXT,
  annual_revenue_cr           REAL,           -- mirrors profile model
  total_insurable_asset_value_cr REAL,
  profile_json   TEXT,                         -- full DEFAULT_PROFILE-shaped JSON
  stage          TEXT NOT NULL DEFAULT 'prospect',  -- prospect|analysed|quoted|converted|lost
  rm_email       TEXT REFERENCES rms(rm_email),
  source         TEXT,                          -- 'funding_feed' | 'manual' | 'signal'
  renewal_due_on TEXT,                          -- nullable; for F4
  last_engaged_on TEXT,                         -- nullable; for F4 at-risk
  created_at     TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at     TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_accounts_scope ON accounts(city, sector, stage);
CREATE INDEX IF NOT EXISTS idx_accounts_rm    ON accounts(rm_email);
```

### `analyses`
A stored SPARC analysis result for an account (snapshot of the engine output).
```sql
CREATE TABLE IF NOT EXISTS analyses (
  analysis_id   TEXT PRIMARY KEY,             -- 'an_' + ulid
  account_id    TEXT NOT NULL REFERENCES accounts(account_id),
  recommended_bundle TEXT,
  bundle_fit_pct REAL,
  risk_scores_json TEXT,                       -- {Cyber:82, DataPrivacy:85, ...}
  mandatory_covers_json TEXT,                  -- ["Cyber","D&O",...]
  triggers_json TEXT,                          -- [{reg, requirement, max_exposure}]
  result_json   TEXT NOT NULL,                 -- full engine result (window.__result shape)
  created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_analyses_account ON analyses(account_id);
```

### `gwp_estimates`
Indicative GWP range for an analysis. **Always a range.**
```sql
CREATE TABLE IF NOT EXISTS gwp_estimates (
  estimate_id   TEXT PRIMARY KEY,             -- 'gwp_' + ulid
  account_id    TEXT NOT NULL REFERENCES accounts(account_id),
  analysis_id   TEXT REFERENCES analyses(analysis_id),
  gwp_low_inr   INTEGER NOT NULL,
  gwp_high_inr  INTEGER NOT NULL,
  basis         TEXT,                          -- 'pricing.model.quote' | 'premium_estimator bands'
  data_quality  REAL,                          -- 0..1
  disclaimer    TEXT NOT NULL,
  per_cover_json TEXT,                          -- [{cover, low, high}]
  created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_gwp_account ON gwp_estimates(account_id);
```

### `pipeline_events`
Stage transitions (audit of the funnel).
```sql
CREATE TABLE IF NOT EXISTS pipeline_events (
  event_id    TEXT PRIMARY KEY,               -- 'pe_' + ulid
  account_id  TEXT NOT NULL REFERENCES accounts(account_id),
  from_stage  TEXT,
  to_stage    TEXT NOT NULL,
  rm_email    TEXT REFERENCES rms(rm_email),
  gwp_low_inr INTEGER,                          -- snapshot at transition
  gwp_high_inr INTEGER,
  created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_pe_account ON pipeline_events(account_id);
CREATE INDEX IF NOT EXISTS idx_pe_time ON pipeline_events(created_at);
```

### `alerts`  (F4)
Renewal / upsell / at-risk / coverage-gap alerts.
```sql
CREATE TABLE IF NOT EXISTS alerts (
  alert_id    TEXT PRIMARY KEY,               -- 'al_' + ulid
  account_id  TEXT NOT NULL REFERENCES accounts(account_id),
  type        TEXT NOT NULL,                   -- renewal|upsell|at_risk|coverage_gap
  reason      TEXT NOT NULL,                   -- typed, human-readable
  trigger_detail_json TEXT,                    -- {field, old, new, threshold}
  delta_gwp_low_inr  INTEGER,
  delta_gwp_high_inr INTEGER,
  status      TEXT NOT NULL DEFAULT 'open',    -- open|dismissed|actioned
  created_at  TEXT NOT NULL DEFAULT (datetime('now')),
  resolved_at TEXT,
  resolved_by TEXT REFERENCES rms(rm_email)
);
CREATE INDEX IF NOT EXISTS idx_alerts_account ON alerts(account_id);
CREATE INDEX IF NOT EXISTS idx_alerts_status  ON alerts(status, type);
```

### `proposals`  (F3)
Generated proposal PDFs.
```sql
CREATE TABLE IF NOT EXISTS proposals (
  proposal_id TEXT PRIMARY KEY,               -- 'prop_' + ulid
  account_id  TEXT NOT NULL REFERENCES accounts(account_id),
  analysis_id TEXT REFERENCES analyses(analysis_id),
  pdf_path    TEXT NOT NULL,                   -- served path
  bundle      TEXT,
  gwp_low_inr INTEGER,
  gwp_high_inr INTEGER,
  valid_until TEXT,                             -- generated_at + 30d
  rm_email    TEXT REFERENCES rms(rm_email),
  created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_proposals_account ON proposals(account_id);
```

### `funding_leads`  (F5)
Ingested funding events, valued and claimable.
```sql
CREATE TABLE IF NOT EXISTS funding_leads (
  lead_id     TEXT PRIMARY KEY,               -- 'lead_' + ulid
  company     TEXT NOT NULL,
  city        TEXT,
  sector      TEXT,
  stage       TEXT,
  amount_inr  INTEGER,                          -- round size
  round       TEXT,                             -- 'Series A' etc.
  source      TEXT,                             -- 'csv:filename' | 'tracxn'
  announced_on TEXT,
  est_bundle  TEXT,                             -- from auto-analyse
  est_gwp_low_inr  INTEGER,
  est_gwp_high_inr INTEGER,
  status      TEXT NOT NULL DEFAULT 'open',     -- open|claimed|dismissed
  claimed_by  TEXT REFERENCES rms(rm_email),
  account_id  TEXT REFERENCES accounts(account_id),  -- set on claim
  created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_leads_scope  ON funding_leads(city, sector, status);
CREATE INDEX IF NOT EXISTS idx_leads_status ON funding_leads(status);
```

### `events`  (F2 — append-only activity log)
```sql
CREATE TABLE IF NOT EXISTS events (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  kind        TEXT NOT NULL,                   -- analysed|quoted|proposal_generated|lead_claimed|converted
  rm_email    TEXT REFERENCES rms(rm_email),
  account_id  TEXT REFERENCES accounts(account_id),
  gwp_low_inr INTEGER,
  gwp_high_inr INTEGER,
  meta_json   TEXT,
  created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_events_rm   ON events(rm_email, kind);
CREATE INDEX IF NOT EXISTS idx_events_time ON events(created_at);
```

---

## 3. Derived views (queries, not tables)

**Funnel (F1):**
```sql
SELECT stage,
       COUNT(*) AS count,
       COALESCE(SUM(g.gwp_low_inr),0)  AS gwp_low,
       COALESCE(SUM(g.gwp_high_inr),0) AS gwp_high
FROM accounts a
LEFT JOIN gwp_estimates g ON g.account_id = a.account_id
WHERE (:city  IS NULL OR a.city = :city)
  AND (:sector IS NULL OR a.sector = :sector)
GROUP BY stage;
```

**RM leaderboard (F2):**
```sql
SELECT r.rm_email, r.name,
       SUM(e.kind='analysed')            AS analysed,
       SUM(e.kind='quoted')              AS quoted,
       SUM(e.kind='proposal_generated')  AS proposals,
       SUM(e.kind='converted')           AS converted,
       COALESCE(SUM(CASE WHEN e.kind IN('quoted','converted') THEN e.gwp_high_inr END),0) AS pipeline_gwp_high
FROM rms r
LEFT JOIN events e ON e.rm_email = r.rm_email
WHERE (:since IS NULL OR e.created_at >= :since)
GROUP BY r.rm_email;
```

**Conversion by sector (F2):**
```sql
SELECT a.sector,
       SUM(e.kind='quoted')    AS quoted,
       SUM(e.kind='converted') AS converted,
       CAST(SUM(e.kind='converted') AS REAL) / NULLIF(SUM(e.kind='quoted'),0) AS conv_rate
FROM accounts a JOIN events e ON e.account_id = a.account_id
GROUP BY a.sector;
```

---

## 4. ID & money conventions
- IDs: typed prefix + ULID (`acc_`, `an_`, `gwp_`, `al_`, `prop_`, `lead_`, `pe_`).
- Money: INR integer rupees. UI formats to ₹L / ₹Cr at render only.
- Ranges: every monetary fact stored and returned as `_low`/`_high`. **No single-point premium is ever persisted or surfaced.**

## 5. Seed / migration order
1. `rms` (from `contacts.json`)
2. `accounts` ← `funding_leads` claims or manual
3. `analyses` + `gwp_estimates` (per analyse)
4. `events` (append on every action)
5. `alerts` (alert_engine sweep)
6. `proposals` (on generate)
