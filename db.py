"""SQLite persistence layer for the SPARC Commerce Layer.

M0 foundation: connection helper, idempotent migrations covering the nine
tables defined in 03_BACKEND_SCHEMA.md, and an idempotent seed of the
``rms`` table from ``contacts.json``.

Path strategy mirrors ``startup_shield_web/server.py`` exactly: honour
``SPARC_DB_PATH`` if set, else ``/tmp/sparc_data.db`` on Vercel, else
``<project_root>/sparc_data.db`` locally.
"""

from __future__ import annotations

import json
import os
import sqlite3
import tempfile
from pathlib import Path
from typing import Iterable

PROJECT_ROOT = Path(__file__).resolve().parent

DB_PATH = Path(os.environ.get(
    "SPARC_DB_PATH",
    str(Path(tempfile.gettempdir()) / "sparc_data.db")
    if os.environ.get("VERCEL")
    else str(PROJECT_ROOT / "sparc_data.db"),
))

_SCHEMA_STATEMENTS: tuple[str, ...] = (
    """
    CREATE TABLE IF NOT EXISTS rms (
      rm_email    TEXT PRIMARY KEY,
      name        TEXT NOT NULL,
      phone       TEXT,
      office      TEXT,
      city        TEXT,
      created_at  TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS accounts (
      account_id     TEXT PRIMARY KEY,
      name           TEXT NOT NULL,
      sector         TEXT,
      sub_sector     TEXT,
      funding_stage  TEXT,
      team_size      INTEGER,
      city           TEXT,
      annual_revenue_cr               REAL,
      total_insurable_asset_value_cr  REAL,
      profile_json   TEXT,
      stage          TEXT NOT NULL DEFAULT 'prospect',
      rm_email       TEXT REFERENCES rms(rm_email),
      source         TEXT,
      renewal_due_on  TEXT,
      last_engaged_on TEXT,
      created_at     TEXT NOT NULL DEFAULT (datetime('now')),
      updated_at     TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_accounts_scope ON accounts(city, sector, stage)",
    "CREATE INDEX IF NOT EXISTS idx_accounts_rm    ON accounts(rm_email)",
    """
    CREATE TABLE IF NOT EXISTS analyses (
      analysis_id   TEXT PRIMARY KEY,
      account_id    TEXT NOT NULL REFERENCES accounts(account_id),
      recommended_bundle    TEXT,
      bundle_fit_pct        REAL,
      risk_scores_json      TEXT,
      mandatory_covers_json TEXT,
      triggers_json         TEXT,
      result_json   TEXT NOT NULL,
      created_at    TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_analyses_account ON analyses(account_id)",
    """
    CREATE TABLE IF NOT EXISTS gwp_estimates (
      estimate_id   TEXT PRIMARY KEY,
      account_id    TEXT NOT NULL REFERENCES accounts(account_id),
      analysis_id   TEXT REFERENCES analyses(analysis_id),
      gwp_low_inr   INTEGER NOT NULL,
      gwp_high_inr  INTEGER NOT NULL,
      basis         TEXT,
      data_quality  REAL,
      disclaimer    TEXT NOT NULL,
      per_cover_json TEXT,
      created_at    TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_gwp_account ON gwp_estimates(account_id)",
    """
    CREATE TABLE IF NOT EXISTS pipeline_events (
      event_id    TEXT PRIMARY KEY,
      account_id  TEXT NOT NULL REFERENCES accounts(account_id),
      from_stage  TEXT,
      to_stage    TEXT NOT NULL,
      rm_email    TEXT REFERENCES rms(rm_email),
      gwp_low_inr  INTEGER,
      gwp_high_inr INTEGER,
      created_at  TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_pe_account ON pipeline_events(account_id)",
    "CREATE INDEX IF NOT EXISTS idx_pe_time    ON pipeline_events(created_at)",
    """
    CREATE TABLE IF NOT EXISTS alerts (
      alert_id    TEXT PRIMARY KEY,
      account_id  TEXT NOT NULL REFERENCES accounts(account_id),
      type        TEXT NOT NULL,
      reason      TEXT NOT NULL,
      trigger_detail_json TEXT,
      delta_gwp_low_inr  INTEGER,
      delta_gwp_high_inr INTEGER,
      status      TEXT NOT NULL DEFAULT 'open',
      created_at  TEXT NOT NULL DEFAULT (datetime('now')),
      resolved_at TEXT,
      resolved_by TEXT REFERENCES rms(rm_email)
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_alerts_account ON alerts(account_id)",
    "CREATE INDEX IF NOT EXISTS idx_alerts_status  ON alerts(status, type)",
    """
    CREATE TABLE IF NOT EXISTS proposals (
      proposal_id TEXT PRIMARY KEY,
      account_id  TEXT NOT NULL REFERENCES accounts(account_id),
      analysis_id TEXT REFERENCES analyses(analysis_id),
      pdf_path    TEXT NOT NULL,
      bundle      TEXT,
      gwp_low_inr  INTEGER,
      gwp_high_inr INTEGER,
      valid_until TEXT,
      rm_email    TEXT REFERENCES rms(rm_email),
      created_at  TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_proposals_account ON proposals(account_id)",
    """
    CREATE TABLE IF NOT EXISTS funding_leads (
      lead_id     TEXT PRIMARY KEY,
      company     TEXT NOT NULL,
      city        TEXT,
      sector      TEXT,
      stage       TEXT,
      amount_inr  INTEGER,
      round       TEXT,
      source      TEXT,
      announced_on TEXT,
      est_bundle  TEXT,
      est_gwp_low_inr  INTEGER,
      est_gwp_high_inr INTEGER,
      status      TEXT NOT NULL DEFAULT 'open',
      claimed_by  TEXT REFERENCES rms(rm_email),
      account_id  TEXT REFERENCES accounts(account_id),
      created_at  TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_leads_scope  ON funding_leads(city, sector, status)",
    "CREATE INDEX IF NOT EXISTS idx_leads_status ON funding_leads(status)",
    """
    CREATE TABLE IF NOT EXISTS events (
      id          INTEGER PRIMARY KEY AUTOINCREMENT,
      kind        TEXT NOT NULL,
      rm_email    TEXT REFERENCES rms(rm_email),
      account_id  TEXT REFERENCES accounts(account_id),
      gwp_low_inr  INTEGER,
      gwp_high_inr INTEGER,
      meta_json   TEXT,
      created_at  TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_events_rm   ON events(rm_email, kind)",
    "CREATE INDEX IF NOT EXISTS idx_events_time ON events(created_at)",
    """
    CREATE TABLE IF NOT EXISTS signals_seen (
      company    TEXT NOT NULL,
      signal_id  TEXT NOT NULL,
      first_seen_at TEXT NOT NULL DEFAULT (datetime('now')),
      PRIMARY KEY (company, signal_id)
    )
    """,
)


def get_conn(db_path: Path | str | None = None) -> sqlite3.Connection:
    """Return a sqlite3 connection with row factory and FK enforcement."""
    path = Path(db_path) if db_path is not None else DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def migrate(db_path: Path | str | None = None) -> None:
    """Run all schema statements. Idempotent — safe to call on every boot."""
    conn = get_conn(db_path)
    try:
        with conn:
            for stmt in _SCHEMA_STATEMENTS:
                conn.execute(stmt)
    finally:
        conn.close()


def _rm_records_from_contacts(contacts: object) -> Iterable[dict]:
    """Normalise the various shapes contacts.json could take into RM dicts."""
    if isinstance(contacts, dict):
        if isinstance(contacts.get("rms"), list):
            for entry in contacts["rms"]:
                if isinstance(entry, dict):
                    yield entry
            return
        if any(k in contacts for k in ("RM_EMAIL", "rm_email", "email")):
            yield contacts
            return
        for value in contacts.values():
            if isinstance(value, dict) and any(
                k in value for k in ("RM_EMAIL", "rm_email", "email")
            ):
                yield value
        return
    if isinstance(contacts, list):
        for entry in contacts:
            if isinstance(entry, dict):
                yield entry


def _norm(entry: dict) -> dict | None:
    email = (
        entry.get("RM_EMAIL")
        or entry.get("rm_email")
        or entry.get("email")
    )
    if not email:
        return None
    return {
        "rm_email": str(email).strip(),
        "name": str(entry.get("RM_NAME") or entry.get("name") or "").strip(),
        "phone": str(entry.get("RM_PHONE") or entry.get("phone") or "").strip() or None,
        "office": str(entry.get("RM_OFFICE") or entry.get("office") or "").strip() or None,
        "city": str(entry.get("RM_CITY") or entry.get("city") or "").strip() or None,
    }


def seed_rms_from_contacts(
    contacts_path: Path | str | None = None,
    db_path: Path | str | None = None,
) -> int:
    """Seed/refresh the rms table from contacts.json. Idempotent UPSERT.

    Returns the number of rows written (inserts + updates).
    """
    path = Path(contacts_path) if contacts_path else PROJECT_ROOT / "contacts.json"
    if not path.exists():
        return 0
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return 0

    written = 0
    conn = get_conn(db_path)
    try:
        with conn:
            for raw in _rm_records_from_contacts(data):
                rec = _norm(raw)
                if not rec or not rec["name"]:
                    continue
                conn.execute(
                    """
                    INSERT INTO rms (rm_email, name, phone, office, city)
                    VALUES (:rm_email, :name, :phone, :office, :city)
                    ON CONFLICT(rm_email) DO UPDATE SET
                      name   = excluded.name,
                      phone  = excluded.phone,
                      office = excluded.office,
                      city   = excluded.city
                    """,
                    rec,
                )
                written += 1
    finally:
        conn.close()
    return written


def get_seen_signal_keys(db_path=None) -> set:
    """Return set of 'company::signal_id' strings that have been marked seen."""
    migrate(db_path)
    conn = get_conn(db_path)
    try:
        rows = conn.execute("SELECT company, signal_id FROM signals_seen").fetchall()
        return {f"{r['company']}::{r['signal_id']}" for r in rows}
    finally:
        conn.close()


def mark_signals_seen(signals: list[dict], db_path=None) -> int:
    """Insert (company, signal_id) pairs. Ignores duplicates. Returns count inserted."""
    if not signals:
        return 0
    migrate(db_path)
    conn = get_conn(db_path)
    inserted = 0
    try:
        with conn:
            for s in signals:
                company = str(s.get("company") or "").strip()
                signal_id = str(s.get("signal_id") or "").strip()
                if not company or not signal_id:
                    continue
                conn.execute(
                    "INSERT OR IGNORE INTO signals_seen (company, signal_id) VALUES (?, ?)",
                    (company, signal_id),
                )
                inserted += 1
    finally:
        conn.close()
    return inserted
