"""Metrics service — F1 dashboard aggregations.

Reads from accounts + gwp_estimates + funding_leads to produce the three
shapes the Opportunity screen needs (TRD §3 dashboard contract):

  territory_gwp = Σ low … Σ high over accounts in scope
  funnel        = per-stage count + GWP range (Schema §3 funnel view)
  top_leads     = accounts ranked by gwp_high desc (limit 10)

All money is in integer INR rupees. Every aggregate carries the IRDAI
File-and-Use indicative disclaimer.
"""

from __future__ import annotations

from pathlib import Path

import db

DISCLAIMER = (
    "Indicative only under IRDAI File-and-Use detariffed regime. "
    "Not a bindable quote."
)

# All five funnel stages defined in Schema §accounts. We always return
# all five (even at count=0) so the UI strip is stable.
_FUNNEL_STAGES = ("prospect", "analysed", "quoted", "converted", "lost")


def _scope_clause(city, sector, stage):
    where, params = [], {}
    if city:
        where.append("a.city = :city");     params["city"] = city
    if sector:
        where.append("a.sector = :sector"); params["sector"] = sector
    if stage:
        where.append("a.stage = :stage");   params["stage"] = stage
    return ((" WHERE " + " AND ".join(where)) if where else ""), params


def funnel(
    *,
    city: str | None = None,
    sector: str | None = None,
    db_path: Path | str | None = None,
) -> list[dict]:
    """Per-stage count + GWP low/high. Always returns all 5 stages."""
    where_sql, params = _scope_clause(city, sector, None)
    sql = (
        "SELECT a.stage AS stage, "
        "       COUNT(*) AS count, "
        "       COALESCE(SUM(g.gwp_low_inr), 0)  AS gwp_low, "
        "       COALESCE(SUM(g.gwp_high_inr), 0) AS gwp_high "
        "FROM accounts a "
        "LEFT JOIN gwp_estimates g ON g.estimate_id = ("
        "  SELECT estimate_id FROM gwp_estimates WHERE account_id = a.account_id "
        "  ORDER BY created_at DESC LIMIT 1"
        ") "
        + where_sql +
        " GROUP BY a.stage"
    )
    conn = db.get_conn(db_path)
    try:
        rows = {r["stage"]: dict(r) for r in conn.execute(sql, params).fetchall()}
    finally:
        conn.close()
    return [
        {
            "stage": s,
            "count": int(rows.get(s, {}).get("count", 0)),
            "gwp_low_inr":  int(rows.get(s, {}).get("gwp_low", 0)),
            "gwp_high_inr": int(rows.get(s, {}).get("gwp_high", 0)),
        }
        for s in _FUNNEL_STAGES
    ]


def territory_gwp(
    *,
    city: str | None = None,
    sector: str | None = None,
    stage: str | None = None,
    db_path: Path | str | None = None,
) -> dict:
    """Σ low … Σ high across accounts in scope (and the open funding-feed
    leads — those are addressable but not yet claimed)."""
    where_sql, params = _scope_clause(city, sector, stage)
    sql_accts = (
        "SELECT COALESCE(SUM(g.gwp_low_inr), 0)  AS lo, "
        "       COALESCE(SUM(g.gwp_high_inr), 0) AS hi, "
        "       COUNT(DISTINCT a.account_id)     AS n "
        "FROM accounts a "
        "LEFT JOIN gwp_estimates g ON g.estimate_id = ("
        "  SELECT estimate_id FROM gwp_estimates WHERE account_id = a.account_id "
        "  ORDER BY created_at DESC LIMIT 1"
        ") "
        + where_sql
    )

    # Open leads (status=open) contribute to addressable opportunity even
    # before they are claimed/analysed.
    lead_where, lead_params = [], {}
    if city:   lead_where.append("city = :city");     lead_params["city"] = city
    if sector: lead_where.append("sector = :sector"); lead_params["sector"] = sector
    lead_where.append("status = 'open'")
    sql_leads = (
        "SELECT COALESCE(SUM(est_gwp_low_inr), 0)  AS lo, "
        "       COALESCE(SUM(est_gwp_high_inr), 0) AS hi, "
        "       COUNT(*) AS n "
        "FROM funding_leads WHERE " + " AND ".join(lead_where)
    )

    conn = db.get_conn(db_path)
    try:
        a = dict(conn.execute(sql_accts, params).fetchone() or {})
        l = dict(conn.execute(sql_leads, lead_params).fetchone() or {})
    finally:
        conn.close()

    lo = int(a.get("lo", 0)) + int(l.get("lo", 0))
    hi = int(a.get("hi", 0)) + int(l.get("hi", 0))
    return {
        "low_inr": lo,
        "high_inr": hi,
        "currency": "INR",
        "account_count": int(a.get("n", 0)),
        "open_lead_count": int(l.get("n", 0)),
        "basis": "Σ accounts(gwp_estimates) + Σ open funding_leads(est_gwp)",
        "disclaimer": DISCLAIMER,
    }


def top_leads(
    *,
    city: str | None = None,
    sector: str | None = None,
    stage: str | None = None,
    limit: int = 10,
    sort_by: str = "gwp_high",
    db_path: Path | str | None = None,
) -> list[dict]:
    """Top accounts by indicative GWP high (default), gwp_low, sector, or city."""
    where_sql, params = _scope_clause(city, sector, stage)
    sort_col = {
        "gwp_high": "gwp_high_inr DESC",
        "gwp_low":  "gwp_low_inr DESC",
        "sector":   "a.sector ASC, gwp_high_inr DESC",
        "city":     "a.city ASC, gwp_high_inr DESC",
    }.get(sort_by, "gwp_high_inr DESC")
    params["limit"] = int(limit)
    sql = (
        "SELECT a.account_id, a.name, a.sector, a.funding_stage AS stage, "
        "       a.city, a.stage AS pipeline_stage, a.rm_email, "
        "       COALESCE(g.gwp_low_inr, 0)  AS gwp_low_inr, "
        "       COALESCE(g.gwp_high_inr, 0) AS gwp_high_inr, "
        "       g.basis AS basis "
        "FROM accounts a "
        "LEFT JOIN gwp_estimates g ON g.estimate_id = ("
        "  SELECT estimate_id FROM gwp_estimates WHERE account_id = a.account_id "
        "  ORDER BY created_at DESC LIMIT 1"
        ") "
        + where_sql +
        f" ORDER BY {sort_col} "
        "LIMIT :limit"
    )
    conn = db.get_conn(db_path)
    try:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]
    finally:
        conn.close()


def dashboard(
    *,
    city: str | None = None,
    sector: str | None = None,
    stage: str | None = None,
    limit: int = 10,
    sort_by: str = "gwp_high",
    db_path: Path | str | None = None,
) -> dict:
    """One-call payload matching the /api/commerce/dashboard contract."""
    return {
        "territory_gwp": territory_gwp(city=city, sector=sector, stage=stage, db_path=db_path),
        "funnel":        funnel(city=city, sector=sector, db_path=db_path),
        "top_leads":     top_leads(city=city, sector=sector, stage=stage, limit=limit, sort_by=sort_by, db_path=db_path),
        "scope":         {"city": city, "sector": sector, "stage": stage},
        "disclaimer":    DISCLAIMER,
    }


# ─── F2 RM Performance aggregations ────────────────────────────

_EVENT_KINDS = ("analysed", "quoted", "proposal_generated", "lead_claimed", "converted")


def _since_clause(since: str | None) -> tuple[str, dict]:
    if not since:
        return "", {}
    return " AND e.created_at >= :since", {"since": since}


def rm_leaderboard(
    *,
    since: str | None = None,
    db_path: Path | str | None = None,
) -> list[dict]:
    """Per-RM event counts + pipeline GWP (high snapshot at event time).

    Always returns one row per RM in ``rms`` (even at zero activity) so the
    leaderboard is stable across weeks.
    """
    since_sql, since_params = _since_clause(since)
    sql = (
        "SELECT r.rm_email, r.name, r.city, "
        "  SUM(CASE WHEN e.kind='analysed'           THEN 1 ELSE 0 END) AS analysed, "
        "  SUM(CASE WHEN e.kind='quoted'             THEN 1 ELSE 0 END) AS quoted, "
        "  SUM(CASE WHEN e.kind='proposal_generated' THEN 1 ELSE 0 END) AS proposals, "
        "  SUM(CASE WHEN e.kind='lead_claimed'       THEN 1 ELSE 0 END) AS claimed, "
        "  SUM(CASE WHEN e.kind='converted'          THEN 1 ELSE 0 END) AS converted, "
        "  COALESCE(SUM(CASE WHEN e.kind IN ('quoted','proposal_generated','converted') "
        "       THEN e.gwp_low_inr END), 0)  AS pipeline_gwp_low, "
        "  COALESCE(SUM(CASE WHEN e.kind IN ('quoted','proposal_generated','converted') "
        "       THEN e.gwp_high_inr END), 0) AS pipeline_gwp_high "
        "FROM rms r "
        "LEFT JOIN events e ON e.rm_email = r.rm_email" + since_sql + " "
        "GROUP BY r.rm_email, r.name, r.city "
        "ORDER BY pipeline_gwp_high DESC, proposals DESC, claimed DESC, r.name ASC"
    )
    conn = db.get_conn(db_path)
    try:
        rows = [dict(r) for r in conn.execute(sql, since_params).fetchall()]
    finally:
        conn.close()
    for r in rows:
        q = int(r.get("quoted") or 0)
        c = int(r.get("converted") or 0)
        r["conversion_rate"] = round(c / q, 3) if q else 0.0
    return rows


def conversion_by_sector(
    *,
    since: str | None = None,
    db_path: Path | str | None = None,
) -> list[dict]:
    since_sql, since_params = _since_clause(since)
    sql = (
        "SELECT a.sector AS sector, "
        "  SUM(CASE WHEN e.kind='quoted'    THEN 1 ELSE 0 END) AS quoted, "
        "  SUM(CASE WHEN e.kind='converted' THEN 1 ELSE 0 END) AS converted "
        "FROM accounts a "
        "LEFT JOIN events e ON e.account_id = a.account_id" + since_sql + " "
        "WHERE a.sector IS NOT NULL "
        "GROUP BY a.sector "
        "ORDER BY converted DESC, quoted DESC, a.sector ASC"
    )
    conn = db.get_conn(db_path)
    try:
        rows = [dict(r) for r in conn.execute(sql, since_params).fetchall()]
    finally:
        conn.close()
    for r in rows:
        q = int(r.get("quoted") or 0)
        c = int(r.get("converted") or 0)
        r["conv_rate"] = round(c / q, 3) if q else 0.0
    return rows


def speed_metrics(
    *,
    db_path: Path | str | None = None,
) -> dict:
    """Median time-in-stage between consecutive pipeline_events.

    Returned as seconds; UI formats to days/hours. We compute server-side
    medians rather than via SQL aggregates for portability across SQLite
    versions that lack PERCENTILE_CONT.
    """
    sql = (
        "SELECT account_id, to_stage, created_at "
        "FROM pipeline_events ORDER BY account_id, created_at"
    )
    transitions: dict[str, list[float]] = {
        "prospect_to_analysed": [],
        "analysed_to_quoted":   [],
        "quoted_to_converted":  [],
    }
    pair_to_key = {
        ("prospect", "analysed"):  "prospect_to_analysed",
        ("analysed", "quoted"):    "analysed_to_quoted",
        ("quoted",   "converted"): "quoted_to_converted",
    }
    from datetime import datetime as _dt

    def _parse(ts: str) -> float | None:
        try:
            # SQLite default datetime('now') yields 'YYYY-MM-DD HH:MM:SS'
            return _dt.fromisoformat(ts.replace(" ", "T")).timestamp()
        except Exception:
            return None

    conn = db.get_conn(db_path)
    try:
        rows = conn.execute(sql).fetchall()
    finally:
        conn.close()
    by_acct: dict[str, list[tuple[str, float]]] = {}
    for r in rows:
        ts = _parse(r["created_at"])
        if ts is None:
            continue
        by_acct.setdefault(r["account_id"], []).append((r["to_stage"], ts))
    for events in by_acct.values():
        for (s1, t1), (s2, t2) in zip(events, events[1:]):
            key = pair_to_key.get((s1, s2))
            if key:
                transitions[key].append(t2 - t1)

    def _median(xs: list[float]) -> float | None:
        if not xs:
            return None
        ys = sorted(xs)
        n = len(ys)
        mid = n // 2
        return ys[mid] if n % 2 else (ys[mid - 1] + ys[mid]) / 2

    return {
        key: {
            "median_seconds": _median(values),
            "n":              len(values),
        }
        for key, values in transitions.items()
    }


def weekly_digest(
    *,
    since: str | None = None,
    db_path: Path | str | None = None,
) -> dict:
    """Structured summary object — rendered to email by the outreach
    pipeline downstream. Schema §events + leaderboard + conversion."""
    leaders = rm_leaderboard(since=since, db_path=db_path)
    top_rm = max(leaders, key=lambda r: r["pipeline_gwp_high"], default=None)
    conv = conversion_by_sector(since=since, db_path=db_path)
    total_quoted    = sum(int(r.get("quoted") or 0)    for r in leaders)
    total_proposals = sum(int(r.get("proposals") or 0) for r in leaders)
    total_claimed   = sum(int(r.get("claimed") or 0)   for r in leaders)
    total_converted = sum(int(r.get("converted") or 0) for r in leaders)
    pipeline_low    = sum(int(r.get("pipeline_gwp_low") or 0)  for r in leaders)
    pipeline_high   = sum(int(r.get("pipeline_gwp_high") or 0) for r in leaders)
    return {
        "headline": (
            f"Pipeline {pipeline_low:,}–{pipeline_high:,} INR · "
            f"{total_proposals} proposals · {total_claimed} leads claimed"
        ),
        "totals": {
            "claimed":   total_claimed,
            "quoted":    total_quoted,
            "proposals": total_proposals,
            "converted": total_converted,
            "pipeline_gwp_low_inr":  pipeline_low,
            "pipeline_gwp_high_inr": pipeline_high,
        },
        "top_rm": (
            {
                "rm_email":              top_rm["rm_email"],
                "name":                  top_rm["name"],
                "pipeline_gwp_high_inr": top_rm["pipeline_gwp_high"],
                "proposals":             top_rm["proposals"],
                "conversion_rate":       top_rm["conversion_rate"],
            } if top_rm and top_rm["pipeline_gwp_high"] else None
        ),
        "leaderboard_top3":     leaders[:3],
        "best_converting_sectors": sorted(
            [s for s in conv if s["quoted"]],
            key=lambda s: s["conv_rate"], reverse=True,
        )[:3],
        "since":      since,
        "disclaimer": DISCLAIMER,
    }


def metrics(
    *,
    since: str | None = None,
    db_path: Path | str | None = None,
) -> dict:
    """One-call payload for /api/commerce/metrics."""
    return {
        "leaderboard":          rm_leaderboard(since=since, db_path=db_path),
        "conversion_by_sector": conversion_by_sector(since=since, db_path=db_path),
        "speed":                speed_metrics(db_path=db_path),
        "digest":               weekly_digest(since=since, db_path=db_path),
        "since":                since,
        "disclaimer":           DISCLAIMER,
    }
