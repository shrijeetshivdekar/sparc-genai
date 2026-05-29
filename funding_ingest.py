"""F5 Funding Feed — CSV ingestion + auto-valuation.

Reads a CSV of funding events, synthesises a minimal profile per row using
the existing ``DEFAULT_PROFILE`` shape, runs the deterministic non-LLM
analyse path (``startup_shield_web.server.analyze``), values the lead with
``gwp_estimator.estimate_gwp``, and persists each as a ``funding_leads``
row (status=open).

Required CSV columns (per TRD §7): company, city, sector, stage,
amount_inr, round, source, announced_on.
"""

from __future__ import annotations

import csv
import io
import json
import secrets
from pathlib import Path
from typing import Iterable, Iterator

import db
import gwp_estimator

# Import the deterministic analyse path. Wrapped so import errors surface
# cleanly during tests/early dev rather than crashing the module at load.
try:
    from startup_shield_web.server import DEFAULT_PROFILE, analyze
except Exception as exc:  # pragma: no cover - imported in normal use
    DEFAULT_PROFILE = {}
    analyze = None  # type: ignore[assignment]
    _IMPORT_ERROR = f"{type(exc).__name__}: {exc}"
else:
    _IMPORT_ERROR = None

REQUIRED_COLUMNS = (
    "company", "city", "sector", "stage",
    "amount_inr", "round", "source", "announced_on",
)

# Loose mapping from common CSV stage labels to DEFAULT_PROFILE.funding_stage
# canonical values used by the engine.
_STAGE_CANON = {
    "pre-seed": "Pre-seed", "preseed": "Pre-seed",
    "seed": "Seed",
    "series a": "Series A", "a": "Series A",
    "series b": "Series B+", "series b+": "Series B+",
    "series c": "Series B+", "series c+": "Series B+", "series d": "Series B+",
    "growth": "Series B+", "late": "Series B+",
}


def _new_lead_id() -> str:
    return "lead_" + secrets.token_hex(8)


def _canon_stage(raw: str) -> str:
    return _STAGE_CANON.get(str(raw or "").strip().lower(), "Seed")


def _to_int(value, default=0) -> int:
    try:
        return int(float(str(value).replace(",", "").strip()))
    except (TypeError, ValueError):
        return default


def _profile_from_row(row: dict) -> dict:
    """Synthesise a minimal DEFAULT_PROFILE-shaped dict from one CSV row."""
    profile = dict(DEFAULT_PROFILE)  # copy so we don't mutate the module default
    profile["startup_name"] = (row.get("company") or "").strip()
    sector = (row.get("sector") or "").strip()
    if sector:
        profile["sector"] = sector
    profile["funding_stage"] = _canon_stage(row.get("stage"))
    # Cumulative fundraising is stored in INR Cr in the engine; CSV gives INR
    amount = _to_int(row.get("amount_inr"))
    if amount > 0:
        profile["cumulative_fundraising_inr_cr"] = round(amount / 1e7, 2)
    return profile


def _extract_covers(result: dict) -> list[str]:
    """Pull the list of recommended cover keys from an analyse() result."""
    if not isinstance(result, dict):
        return []
    recs = result.get("recommendations")
    covers: list[str] = []
    if isinstance(recs, list):
        for rec in recs:
            if isinstance(rec, str):
                covers.append(rec)
            elif isinstance(rec, dict):
                key = rec.get("product_key") or rec.get("key") or rec.get("name")
                if isinstance(key, str):
                    covers.append(key)
    return covers


def _extract_bundle_name(result: dict) -> str | None:
    if not isinstance(result, dict):
        return None
    bm = result.get("bundle_match") or {}
    name = bm.get("name") if isinstance(bm, dict) else None
    return str(name) if name else None


def _rows_from_csv_text(csv_text: str) -> Iterator[dict]:
    reader = csv.DictReader(io.StringIO(csv_text))
    for row in reader:
        if any((row.get(c) or "").strip() for c in ("company", "Company")):
            yield {k.lower().strip(): v for k, v in row.items() if k}


def ingest_csv(
    source: str | Path,
    *,
    is_text: bool = False,
    db_path: Path | str | None = None,
    source_label: str | None = None,
) -> dict:
    """Ingest a funding CSV; analyse + value each row; persist as leads.

    ``source`` is a path to a CSV file unless ``is_text`` is True, in which
    case it's the CSV text itself.

    Returns ``{"ingested": N, "leads": [{lead_id, company, est_bundle,
    est_gwp_low_inr, est_gwp_high_inr}, ...]}``.
    """
    if analyze is None:
        raise RuntimeError(f"analyze() unavailable: {_IMPORT_ERROR}")

    if is_text:
        csv_text = str(source)
        label = source_label or "csv:inline"
    else:
        path = Path(source)
        csv_text = path.read_text(encoding="utf-8-sig")
        label = source_label or f"csv:{path.name}"

    db.migrate(db_path)

    leads_summary: list[dict] = []
    conn = db.get_conn(db_path)
    try:
        with conn:
            for row in _rows_from_csv_text(csv_text):
                company = (row.get("company") or "").strip()
                if not company:
                    continue
                profile = _profile_from_row(row)
                try:
                    result = analyze(profile)
                except Exception as exc:  # don't poison the whole import on one bad row
                    result = {"_analyze_error": str(exc)}
                covers = _extract_covers(result)
                gwp = gwp_estimator.estimate_gwp(profile, covers=covers)
                bundle_name = _extract_bundle_name(result)

                lead_id = _new_lead_id()
                conn.execute(
                    """
                    INSERT INTO funding_leads (
                      lead_id, company, city, sector, stage, amount_inr, round,
                      source, announced_on, est_bundle,
                      est_gwp_low_inr, est_gwp_high_inr, status
                    ) VALUES (
                      :lead_id, :company, :city, :sector, :stage, :amount_inr, :round,
                      :source, :announced_on, :est_bundle,
                      :est_gwp_low_inr, :est_gwp_high_inr, 'open'
                    )
                    """,
                    {
                        "lead_id": lead_id,
                        "company": company,
                        "city": (row.get("city") or "").strip() or None,
                        "sector": (row.get("sector") or "").strip() or None,
                        "stage": _canon_stage(row.get("stage")),
                        "amount_inr": _to_int(row.get("amount_inr")) or None,
                        "round": (row.get("round") or "").strip() or None,
                        "source": (row.get("source") or "").strip() or label,
                        "announced_on": (row.get("announced_on") or "").strip() or None,
                        "est_bundle": bundle_name,
                        "est_gwp_low_inr": int(gwp["low_inr"]),
                        "est_gwp_high_inr": int(gwp["high_inr"]),
                    },
                )
                leads_summary.append({
                    "lead_id": lead_id,
                    "company": company,
                    "est_bundle": bundle_name,
                    "est_gwp_low_inr": int(gwp["low_inr"]),
                    "est_gwp_high_inr": int(gwp["high_inr"]),
                })
    finally:
        conn.close()

    return {"ingested": len(leads_summary), "leads": leads_summary}


def sync_from_signals(
    signals: list[dict],
    *,
    db_path: Path | str | None = None,
) -> dict:
    """Upsert signal-radar entries as funding_leads (idempotent on company+stage).

    Each signal carries company, sector, funding_stage, premium_min_lakh,
    premium_max_lakh, recommended_bundle, and signal_id.  We convert the lakh
    premium bands to INR integers and write one open lead per unique
    (company, stage) pair — skipping duplicates that are already in the table.
    """
    if not signals:
        return {"synced": 0, "skipped": 0}

    db.migrate(db_path)
    conn = db.get_conn(db_path)
    synced = skipped = 0
    try:
        with conn:
            for sig in signals:
                company = (sig.get("company") or "").strip()
                if not company:
                    continue
                sector = sig.get("sector") or ""
                stage  = sig.get("funding_stage") or ""
                lo = int(float(sig.get("premium_min_lakh") or 0) * 100_000)
                hi = int(float(sig.get("premium_max_lakh") or 0) * 100_000)
                bundle = sig.get("recommended_bundle") or sig.get("est_bundle") or ""
                source = f"signal_radar:{sig.get('signal_id','')}"

                # Skip if an open or claimed lead already exists for this company+stage
                existing = conn.execute(
                    "SELECT lead_id FROM funding_leads WHERE company = ? AND stage = ? "
                    "AND status IN ('open','claimed') LIMIT 1",
                    (company, stage),
                ).fetchone()
                if existing:
                    skipped += 1
                    continue

                conn.execute(
                    """INSERT INTO funding_leads
                       (lead_id, company, sector, stage, est_gwp_low_inr,
                        est_gwp_high_inr, est_bundle, status, source)
                       VALUES (?, ?, ?, ?, ?, ?, ?, 'open', ?)""",
                    ("lead_" + secrets.token_hex(8), company, sector, stage, lo, hi, bundle, source),
                )
                synced += 1
    finally:
        conn.close()
    return {"synced": synced, "skipped": skipped}


def list_leads(
    *,
    city: str | None = None,
    sector: str | None = None,
    stage: str | None = None,
    status: str = "open",
    limit: int = 200,
    db_path: Path | str | None = None,
) -> list[dict]:
    """List funding leads with optional scope filters."""
    where = ["status = :status"]
    params: dict = {"status": status, "limit": int(limit)}
    if city:
        where.append("city = :city");   params["city"] = city
    if sector:
        where.append("sector = :sector"); params["sector"] = sector
    if stage:
        where.append("stage = :stage");   params["stage"] = stage
    sql = (
        "SELECT lead_id, company, city, sector, stage, amount_inr, round, "
        "source, announced_on, est_bundle, est_gwp_low_inr, est_gwp_high_inr, "
        "status, claimed_by, account_id, created_at "
        "FROM funding_leads WHERE " + " AND ".join(where) +
        " ORDER BY est_gwp_high_inr DESC, created_at DESC LIMIT :limit"
    )
    conn = db.get_conn(db_path)
    try:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]
    finally:
        conn.close()
