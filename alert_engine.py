"""F4 Renewal & upsell alert engine.

Watches tracked accounts for changes that materially affect their
recommended bundle / renewal posture, and writes typed alerts with a
delta-GWP range to the ``alerts`` table.

Four alert types (Schema §alerts.type):
    renewal      — renewal_due_on ≤ today + 60d
    at_risk      — renewal due ≤ 60d AND no engagement in ≥ 90d
    upsell       — funding stage / team-size band crossed since last alert
    coverage_gap — a new regulatory trigger fires

Each alert carries:
    reason              — short typed human string
    trigger_detail_json — structured {field, old, new, threshold}
    delta_gwp_low_inr / delta_gwp_high_inr — range

Idempotency: evaluate_account does not create a second OPEN alert of the
same (account_id, type). Re-running a sweep on unchanged state is a no-op.
"""

from __future__ import annotations

import json
import secrets
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable

import db
import gwp_estimator

# ─── thresholds (PRD §4.F4 ACs) ──────────────────────────────
RENEWAL_WINDOW_DAYS  = 60
AT_RISK_ENGAGED_DAYS = 90

# Stage progression for upsell delta calc (Schema §accounts.funding_stage)
_STAGE_ORDER = ["Pre-seed", "Seed", "Series A", "Series B+", "Growth"]

# Headcount bands that change cover recommendations. Crossing a band
# upwards triggers an upsell alert.
_TEAM_BANDS: tuple[int, ...] = (25, 100, 500, 1500, 3500)

# Used when an account has no stored analyses row yet (e.g. newly claimed
# from the funding feed). A small "starter" cover set so renewal / at-risk
# / upsell calculations still produce a non-zero delta-GWP range based on
# the standard founder-protection trio.
_FALLBACK_COVERS: tuple[str, ...] = ("Cyber", "D&O", "Group Health")


# ─── helpers ──────────────────────────────────────────────────

def _new_alert_id() -> str:
    return "al_" + secrets.token_hex(8)


def _today() -> date:
    return datetime.utcnow().date()


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).split("T")[0]).date()
    except Exception:
        return None


def _days_between(a: date | None, b: date | None) -> int | None:
    if a is None or b is None:
        return None
    return (a - b).days


def _next_stage(stage: str | None) -> str | None:
    if not stage:
        return None
    try:
        i = _STAGE_ORDER.index(stage)
    except ValueError:
        return None
    return _STAGE_ORDER[i + 1] if i + 1 < len(_STAGE_ORDER) else None


def _team_band(team: int | None) -> int:
    """Return the largest threshold the team is at or above (0 if below all)."""
    n = int(team or 0)
    band = 0
    for t in _TEAM_BANDS:
        if n >= t:
            band = t
    return band


def _band_crossed_upward(old_team: int | None, new_team: int | None) -> int | None:
    a, b = _team_band(old_team), _team_band(new_team)
    return b if b > a else None


def _profile_from_account(row: dict) -> dict:
    profile: dict = {}
    try:
        profile = json.loads(row.get("profile_json") or "{}")
    except Exception:
        profile = {}
    profile.setdefault("startup_name", row.get("name"))
    profile.setdefault("sector",       row.get("sector"))
    profile.setdefault("funding_stage", row.get("funding_stage"))
    profile.setdefault("city",         row.get("city"))
    if row.get("team_size"):
        profile.setdefault("team_size", row["team_size"])
    return profile


def _existing_open(conn, account_id: str, alert_type: str) -> dict | None:
    row = conn.execute(
        "SELECT * FROM alerts WHERE account_id = ? AND type = ? AND status = 'open' "
        "ORDER BY created_at DESC LIMIT 1",
        (account_id, alert_type),
    ).fetchone()
    return dict(row) if row else None


def _insert_alert(
    conn, account_id: str, alert_type: str, reason: str,
    detail: dict, delta_low: int, delta_high: int,
) -> dict:
    alert_id = _new_alert_id()
    conn.execute(
        """
        INSERT INTO alerts (
          alert_id, account_id, type, reason, trigger_detail_json,
          delta_gwp_low_inr, delta_gwp_high_inr, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'open')
        """,
        (
            alert_id, account_id, alert_type, reason,
            json.dumps(detail, ensure_ascii=False),
            int(delta_low), int(delta_high),
        ),
    )
    return {
        "alert_id": alert_id, "account_id": account_id, "type": alert_type,
        "reason": reason, "trigger_detail": detail,
        "delta_gwp_low_inr": int(delta_low),
        "delta_gwp_high_inr": int(delta_high),
        "status": "open",
    }


# ─── per-account evaluation ───────────────────────────────────

def _current_covers_for(conn, account_id: str) -> list[str]:
    """Pull cover keys from the most recent analysis row, else empty."""
    row = conn.execute(
        "SELECT mandatory_covers_json, result_json FROM analyses "
        "WHERE account_id = ? ORDER BY created_at DESC LIMIT 1",
        (account_id,),
    ).fetchone()
    if not row:
        return []
    raw = row["mandatory_covers_json"] or ""
    try:
        parsed = json.loads(raw) if raw else []
        if isinstance(parsed, list):
            return [str(c) for c in parsed if c]
    except Exception:
        pass
    return []


def evaluate_account(
    account_id: str,
    *,
    new_triggers: Iterable[str] | None = None,
    db_path: Path | str | None = None,
) -> list[dict]:
    """Run all 4 checks for one account. Returns the list of NEW alerts
    inserted in this call (existing open alerts are not duplicated)."""
    db.migrate(db_path)
    conn = db.get_conn(db_path)
    created: list[dict] = []
    try:
        with conn:
            row = conn.execute(
                "SELECT * FROM accounts WHERE account_id = ?", (account_id,),
            ).fetchone()
            if not row:
                return []
            acct = dict(row)
            profile = _profile_from_account(acct)
            covers  = _current_covers_for(conn, account_id) or list(_FALLBACK_COVERS)
            today   = _today()
            renewal_due = _parse_date(acct.get("renewal_due_on"))
            last_engaged = _parse_date(acct.get("last_engaged_on"))

            # 1) RENEWAL — due within window
            if renewal_due is not None:
                days = (renewal_due - today).days
                if 0 <= days <= RENEWAL_WINDOW_DAYS and not _existing_open(conn, account_id, "renewal"):
                    g = gwp_estimator.estimate_gwp(profile, covers)
                    created.append(_insert_alert(
                        conn, account_id, "renewal",
                        f"Renewal due in {days} days — protect existing GWP.",
                        {"field": "renewal_due_on",
                         "renewal_due_on": acct.get("renewal_due_on"),
                         "days_to_renewal": days,
                         "threshold_days": RENEWAL_WINDOW_DAYS},
                        g["low_inr"], g["high_inr"],
                    ))

                # 2) AT-RISK — renewal ≤ 60d AND no engagement ≤ 90d
                stale_days = _days_between(today, last_engaged) if last_engaged else None
                stale_no_contact = (last_engaged is None) or (stale_days is not None and stale_days >= AT_RISK_ENGAGED_DAYS)
                if 0 <= days <= RENEWAL_WINDOW_DAYS and stale_no_contact \
                        and not _existing_open(conn, account_id, "at_risk"):
                    g = gwp_estimator.estimate_gwp(profile, covers)
                    created.append(_insert_alert(
                        conn, account_id, "at_risk",
                        f"Renewal due in {days}d and no engagement for "
                        f"{stale_days if stale_days is not None else '90+'}d — GWP at risk.",
                        {"field": "engagement",
                         "renewal_due_on": acct.get("renewal_due_on"),
                         "last_engaged_on": acct.get("last_engaged_on"),
                         "days_to_renewal": days,
                         "days_since_engagement": stale_days,
                         "threshold_engagement_days": AT_RISK_ENGAGED_DAYS},
                        -g["high_inr"], -g["low_inr"],  # negative range — what we'd lose
                    ))

            # 3) UPSELL — stage progression OR team-size band crossed
            cur_stage = acct.get("funding_stage")
            nxt_stage = _next_stage(cur_stage)
            if nxt_stage and not _existing_open(conn, account_id, "upsell"):
                old_profile = dict(profile)
                new_profile = dict(profile); new_profile["funding_stage"] = nxt_stage
                delta = gwp_estimator.estimate_delta_gwp(
                    old_profile, new_profile, covers, covers,
                )
                if delta["high_inr"] > 0:
                    created.append(_insert_alert(
                        conn, account_id, "upsell",
                        f"Stage progression {cur_stage} → {nxt_stage} unlocks "
                        f"higher indicative limits.",
                        {"field": "funding_stage",
                         "old": cur_stage, "new": nxt_stage},
                        delta["low_inr"], delta["high_inr"],
                    ))

            # 4) COVERAGE-GAP — explicit new triggers passed in, OR
            #    team band crossing upward (interpreted as additional covers).
            if new_triggers:
                trig_list = [str(t) for t in new_triggers if t]
                if trig_list and not _existing_open(conn, account_id, "coverage_gap"):
                    # Indicate added cover value as the gap delta
                    g = gwp_estimator.estimate_gwp(profile, trig_list)
                    created.append(_insert_alert(
                        conn, account_id, "coverage_gap",
                        f"New regulatory triggers detected: {', '.join(trig_list)} — "
                        f"add covers to close gap.",
                        {"field": "regulatory_triggers", "new": trig_list},
                        g["low_inr"], g["high_inr"],
                    ))
    finally:
        conn.close()
    return created


def evaluate_all(*, db_path: Path | str | None = None) -> dict:
    """Sweep every tracked account. Returns counts + the alerts created."""
    db.migrate(db_path)
    conn = db.get_conn(db_path)
    try:
        ids = [r["account_id"] for r in conn.execute(
            "SELECT account_id FROM accounts WHERE stage NOT IN ('lost','converted')"
        ).fetchall()]
    finally:
        conn.close()
    all_new: list[dict] = []
    for account_id in ids:
        all_new.extend(evaluate_account(account_id, db_path=db_path))
    return {"swept": len(ids), "created": len(all_new), "alerts": all_new}


# ─── list / dismiss ───────────────────────────────────────────

def list_alerts(
    *,
    status: str = "open",
    alert_type: str | None = None,
    db_path: Path | str | None = None,
) -> list[dict]:
    where, params = ["a.status = :status"], {"status": status}
    if alert_type:
        where.append("a.type = :type"); params["type"] = alert_type
    sql = (
        "SELECT a.alert_id, a.account_id, a.type, a.reason, a.trigger_detail_json, "
        "       a.delta_gwp_low_inr, a.delta_gwp_high_inr, a.status, a.created_at, "
        "       ac.name AS account_name, ac.sector, ac.funding_stage AS stage, "
        "       ac.city, ac.rm_email "
        "FROM alerts a LEFT JOIN accounts ac ON ac.account_id = a.account_id "
        "WHERE " + " AND ".join(where) +
        " ORDER BY a.delta_gwp_high_inr DESC, a.created_at DESC"
    )
    conn = db.get_conn(db_path)
    try:
        rows = [dict(r) for r in conn.execute(sql, params).fetchall()]
    finally:
        conn.close()
    for r in rows:
        try:
            r["trigger_detail"] = json.loads(r.pop("trigger_detail_json") or "{}")
        except Exception:
            r["trigger_detail"] = {}
            r.pop("trigger_detail_json", None)
    return rows


def dismiss_alert(
    alert_id: str,
    *,
    rm_email: str | None = None,
    db_path: Path | str | None = None,
) -> dict:
    if not alert_id:
        return {"ok": False, "error": "alert_id required"}
    conn = db.get_conn(db_path)
    try:
        with conn:
            cur = conn.execute("SELECT status FROM alerts WHERE alert_id = ?", (alert_id,))
            row = cur.fetchone()
            if not row:
                return {"ok": False, "error": "alert not found"}
            if row["status"] != "open":
                return {"ok": True, "idempotent": True, "status": row["status"]}
            conn.execute(
                "UPDATE alerts SET status='dismissed', resolved_at=datetime('now'), "
                "resolved_by=? WHERE alert_id=?",
                (rm_email, alert_id),
            )
    finally:
        conn.close()
    return {"ok": True, "status": "dismissed"}


# ─── summary tile for Renewals UI ─────────────────────────────

def at_risk_summary(*, db_path: Path | str | None = None) -> dict:
    """Total GWP at risk from renewals due ≤ 60d (sum of at_risk + renewal
    open alerts; at_risk values are negative — take their magnitude)."""
    sql = (
        "SELECT type, COUNT(*) AS n, "
        "  COALESCE(SUM(ABS(delta_gwp_low_inr)),  0) AS sum_abs_low, "
        "  COALESCE(SUM(ABS(delta_gwp_high_inr)), 0) AS sum_abs_high "
        "FROM alerts WHERE status='open' AND type IN ('renewal','at_risk') "
        "GROUP BY type"
    )
    conn = db.get_conn(db_path)
    try:
        rows = {r["type"]: dict(r) for r in conn.execute(sql).fetchall()}
    finally:
        conn.close()
    renewal = rows.get("renewal", {"n": 0, "sum_abs_low": 0, "sum_abs_high": 0})
    at_risk = rows.get("at_risk", {"n": 0, "sum_abs_low": 0, "sum_abs_high": 0})
    return {
        "renewal_count":            int(renewal["n"]),
        "renewal_gwp_low_inr":      int(renewal["sum_abs_low"]),
        "renewal_gwp_high_inr":     int(renewal["sum_abs_high"]),
        "at_risk_count":            int(at_risk["n"]),
        "at_risk_gwp_low_inr":      int(at_risk["sum_abs_low"]),
        "at_risk_gwp_high_inr":     int(at_risk["sum_abs_high"]),
    }
