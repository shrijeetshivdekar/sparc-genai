"""Pipeline service — account + stage transitions for the Commerce Layer.

M1 ships the ``claim_lead`` flow only (the F5 acceptance path). Later
milestones extend with ``move_stage`` and ``upsert_account`` enrichment.
"""

from __future__ import annotations

import json
import secrets
from pathlib import Path

import db


def _new_id(prefix: str) -> str:
    return f"{prefix}_" + secrets.token_hex(8)


def _row_to_dict(row) -> dict | None:
    return dict(row) if row is not None else None


def claim_lead(
    lead_id: str,
    rm_email: str,
    *,
    db_path: Path | str | None = None,
) -> dict:
    """Claim an open funding lead.

    Idempotent: if the lead is already claimed by the same RM, returns the
    existing account_id. If it's been claimed by someone else, returns a
    structured error and leaves state untouched.
    """
    if not lead_id or not rm_email:
        return {"ok": False, "error": "lead_id and rm_email required"}

    db.migrate(db_path)
    conn = db.get_conn(db_path)
    try:
        with conn:
            lead = _row_to_dict(conn.execute(
                "SELECT * FROM funding_leads WHERE lead_id = ?", (lead_id,),
            ).fetchone())
            if not lead:
                return {"ok": False, "error": f"lead not found: {lead_id}"}

            if lead["status"] == "claimed":
                if lead["claimed_by"] == rm_email:
                    return {
                        "ok": True, "account_id": lead["account_id"],
                        "stage": "prospect", "idempotent": True,
                    }
                return {
                    "ok": False, "error": "lead already claimed by another RM",
                    "claimed_by": lead["claimed_by"],
                }

            # Ensure the RM exists (FK constraint on accounts.rm_email).
            # In production this row is normally seeded from contacts.json;
            # for ad-hoc / pilot RMs not yet seeded, insert a stub row so the
            # claim can proceed without forcing a separate setup step.
            conn.execute(
                "INSERT OR IGNORE INTO rms (rm_email, name) VALUES (?, ?)",
                (rm_email, rm_email.split("@")[0] or rm_email),
            )

            account_id = _new_id("acc")
            profile = {
                "startup_name": lead["company"],
                "sector": lead["sector"],
                "funding_stage": lead["stage"],
                "city": lead["city"],
            }
            conn.execute(
                """
                INSERT INTO accounts (
                  account_id, name, sector, funding_stage, city,
                  profile_json, stage, rm_email, source
                ) VALUES (
                  :account_id, :name, :sector, :funding_stage, :city,
                  :profile_json, 'prospect', :rm_email, 'funding_feed'
                )
                """,
                {
                    "account_id": account_id,
                    "name": lead["company"],
                    "sector": lead["sector"],
                    "funding_stage": lead["stage"],
                    "city": lead["city"],
                    "profile_json": json.dumps(profile, ensure_ascii=False),
                    "rm_email": rm_email,
                },
            )
            conn.execute(
                """
                UPDATE funding_leads
                   SET status = 'claimed', claimed_by = ?, account_id = ?
                 WHERE lead_id = ?
                """,
                (rm_email, account_id, lead_id),
            )
            conn.execute(
                """
                INSERT INTO pipeline_events (
                  event_id, account_id, from_stage, to_stage, rm_email,
                  gwp_low_inr, gwp_high_inr
                ) VALUES (?, ?, NULL, 'prospect', ?, ?, ?)
                """,
                (
                    _new_id("pe"), account_id, rm_email,
                    lead["est_gwp_low_inr"], lead["est_gwp_high_inr"],
                ),
            )
            # Snapshot the lead's indicative GWP into gwp_estimates so the
            # F1 dashboard funnel query (Schema §3) can SUM low/high without
            # waiting for a full analyse round.
            conn.execute(
                """
                INSERT INTO gwp_estimates (
                  estimate_id, account_id, analysis_id,
                  gwp_low_inr, gwp_high_inr, basis, data_quality,
                  disclaimer, per_cover_json
                ) VALUES (?, ?, NULL, ?, ?, ?, ?, ?, NULL)
                """,
                (
                    _new_id("gwp"), account_id,
                    lead["est_gwp_low_inr"], lead["est_gwp_high_inr"],
                    "funding_feed claim snapshot",
                    0.5,
                    "Indicative only under IRDAI File-and-Use detariffed regime. Not a bindable quote.",
                ),
            )
            conn.execute(
                """
                INSERT INTO events (
                  kind, rm_email, account_id, gwp_low_inr, gwp_high_inr, meta_json
                ) VALUES ('lead_claimed', ?, ?, ?, ?, ?)
                """,
                (
                    rm_email, account_id,
                    lead["est_gwp_low_inr"], lead["est_gwp_high_inr"],
                    json.dumps({"lead_id": lead_id}),
                ),
            )
        return {"ok": True, "account_id": account_id, "stage": "prospect"}
    finally:
        conn.close()


def list_pipeline(
    *,
    rm_email: str | None = None,
    stage: str | None = None,
    db_path: Path | str | None = None,
) -> list[dict]:
    where, params = [], {}
    if rm_email:
        where.append("rm_email = :rm_email"); params["rm_email"] = rm_email
    if stage:
        where.append("stage = :stage");       params["stage"] = stage
    sql = (
        "SELECT account_id, name, sector, funding_stage, city, stage, rm_email, "
        "source, created_at, updated_at FROM accounts"
        + (" WHERE " + " AND ".join(where) if where else "")
        + " ORDER BY updated_at DESC"
    )
    conn = db.get_conn(db_path)
    try:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]
    finally:
        conn.close()
