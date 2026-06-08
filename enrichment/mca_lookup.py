"""MCA company snapshot lookup.

Provider-agnostic adapter. Reads provider creds from env vars; cache stored
locally so first-look is paid once per CIN per 90 days.

Supported providers (env var MCA_PROVIDER):
    - "setu"     : Setu Bridge MCA API   (env: SETU_CLIENT_ID, SETU_CLIENT_SECRET)
    - "signzy"   : Signzy Verify API     (env: SIGNZY_API_KEY)
    - "mock"     : returns synthetic data; used when no credentials provided

Cache file: data/mca_cache.json (created on first lookup)
Cache TTL: 90 days; stale entries auto-refetch.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

_ROOT = Path(__file__).resolve().parent.parent
_CACHE_PATH = _ROOT / "data" / "mca_cache.json"
_CACHE_TTL_DAYS = 90


CIN_RE = re.compile(r"^[ULFP][0-9]{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6}$")


def _is_valid_cin(cin: str) -> bool:
    return bool(cin and CIN_RE.match(cin.strip().upper()))


def _load_cache() -> dict:
    if not _CACHE_PATH.exists():
        return {}
    try:
        return json.loads(_CACHE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _save_cache(cache: dict) -> None:
    _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _CACHE_PATH.write_text(json.dumps(cache, indent=2, default=str), encoding="utf-8")


def _is_stale(fetched_at: str) -> bool:
    try:
        ts = datetime.fromisoformat(fetched_at.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return True
    return (datetime.now(timezone.utc) - ts) > timedelta(days=_CACHE_TTL_DAYS)


def _empty_snapshot(cin: str, reason: str) -> dict:
    """Returned when provider is unavailable or lookup fails — degrades gracefully."""
    return {
        "cin": cin,
        "company_name": None,
        "incorporation_date": None,
        "registered_office_state": _state_from_cin(cin),
        "company_type": _company_type_from_cin(cin),
        "authorized_capital_cr": None,
        "paid_up_capital_cr": None,
        "directors": [],
        "director_changes_24mo": None,
        "director_resignations_24mo": None,
        "directors_associated_struck_off_count": None,
        "independent_director_share": None,
        "max_other_directorships": None,
        "shareholders": [],
        "shareholder_concentration_top3_pct": None,
        "charges": [],
        "charges_unsatisfied_count": None,
        "total_secured_debt_cr": None,
        "latest_aoc4": {
            "fy": None,
            "revenue_cr": None,
            "pat_cr": None,
            "net_worth_cr": None,
            "contingent_liabilities_cr": None,
            "related_party_transactions": [],
            "auditor_opinion_modified": None,
        },
        "contingent_liability_to_revenue": None,
        "rpt_share_of_revenue": None,
        "paid_up_capital_to_revenue": None,
        "net_worth_cr": None,
        "auditor_opinion_modified": None,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": "unavailable",
        "reason": reason,
    }


def _state_from_cin(cin: str) -> Optional[str]:
    """CIN positions 6–7 are state code (e.g., 'MH', 'DL')."""
    if not _is_valid_cin(cin):
        return None
    return cin[6:8].upper()


def _company_type_from_cin(cin: str) -> Optional[str]:
    if not _is_valid_cin(cin):
        return None
    prefix = cin[0].upper()
    return {"L": "listed", "U": "private", "F": "foreign", "P": "llp"}.get(prefix)


def _normalise_provider_response(raw: dict, cin: str, provider: str) -> dict:
    """Translate provider-specific payload into our canonical schema.

    Best-effort field mapping; missing keys come back as None.
    """
    snap = _empty_snapshot(cin, reason="")
    snap["source"] = provider
    snap.pop("reason", None)

    snap["company_name"] = raw.get("company_name") or raw.get("companyName")
    snap["incorporation_date"] = raw.get("incorporation_date") or raw.get("dateOfIncorporation")
    snap["registered_office_state"] = raw.get("state") or snap["registered_office_state"]
    snap["company_type"] = raw.get("company_type") or snap["company_type"]
    snap["authorized_capital_cr"] = _to_cr(raw.get("authorized_capital") or raw.get("authorizedCapital"))
    snap["paid_up_capital_cr"] = _to_cr(raw.get("paid_up_capital") or raw.get("paidUpCapital"))

    directors = raw.get("directors") or []
    snap["directors"] = directors
    snap["director_resignations_24mo"] = sum(
        1 for d in directors if (d.get("status") or "").lower() == "resigned" and _within_24mo(d.get("change_date"))
    )
    snap["director_changes_24mo"] = sum(1 for d in directors if _within_24mo(d.get("change_date")))
    snap["directors_associated_struck_off_count"] = sum(
        1 for d in directors if int(d.get("associated_struck_off_count") or 0) >= 1
    )
    ind = [d for d in directors if (d.get("designation") or "").lower() == "independent"]
    snap["independent_director_share"] = (
        round(len(ind) / len(directors), 3) if directors else None
    )
    snap["max_other_directorships"] = max(
        (int(d.get("other_directorships_count") or 0) for d in directors), default=None
    )

    shareholders = raw.get("shareholders") or []
    snap["shareholders"] = shareholders
    if shareholders:
        top3 = sorted((float(s.get("holding_pct") or 0) for s in shareholders), reverse=True)[:3]
        snap["shareholder_concentration_top3_pct"] = round(sum(top3), 2)

    charges = raw.get("charges") or []
    snap["charges"] = charges
    snap["charges_unsatisfied_count"] = sum(
        1 for c in charges if (c.get("status") or "").lower() != "satisfied"
    )
    snap["total_secured_debt_cr"] = round(
        sum(_to_cr(c.get("amount") or 0) or 0 for c in charges if (c.get("status") or "").lower() != "satisfied"),
        2,
    )

    aoc4 = raw.get("latest_aoc4") or raw.get("financials") or {}
    snap["latest_aoc4"] = {
        "fy": aoc4.get("fy"),
        "revenue_cr": _to_cr(aoc4.get("revenue")),
        "pat_cr": _to_cr(aoc4.get("pat") or aoc4.get("profit_after_tax")),
        "net_worth_cr": _to_cr(aoc4.get("net_worth") or aoc4.get("netWorth")),
        "contingent_liabilities_cr": _to_cr(aoc4.get("contingent_liabilities")),
        "related_party_transactions": aoc4.get("related_party_transactions") or [],
        "auditor_opinion_modified": bool(aoc4.get("auditor_opinion_modified") or False),
    }
    rev = snap["latest_aoc4"]["revenue_cr"]
    cl = snap["latest_aoc4"]["contingent_liabilities_cr"]
    pcap = snap["paid_up_capital_cr"]
    rpt_sum = sum(_to_cr(rpt.get("amount") or 0) or 0 for rpt in snap["latest_aoc4"]["related_party_transactions"])
    snap["contingent_liability_to_revenue"] = round(cl / rev, 3) if rev and rev > 0 and cl is not None else None
    snap["rpt_share_of_revenue"] = round(rpt_sum / rev, 3) if rev and rev > 0 else None
    snap["paid_up_capital_to_revenue"] = round(pcap / rev, 3) if rev and rev > 0 and pcap is not None else None
    snap["net_worth_cr"] = snap["latest_aoc4"]["net_worth_cr"]
    snap["auditor_opinion_modified"] = snap["latest_aoc4"]["auditor_opinion_modified"]
    snap["fetched_at"] = datetime.now(timezone.utc).isoformat()
    return snap


def _to_cr(value) -> Optional[float]:
    """Coerce a provider value (string '5,00,00,000' / number) to crore."""
    if value is None or value == "":
        return None
    try:
        if isinstance(value, str):
            value = float(value.replace(",", "").replace("Rs.", "").replace("₹", "").strip())
        return round(float(value) / 1_00_00_000, 2) if value > 1_00_000 else round(float(value), 2)
    except (TypeError, ValueError):
        return None


def _within_24mo(date_str) -> bool:
    if not date_str:
        return False
    try:
        d = datetime.fromisoformat(str(date_str).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return False
    return (datetime.now(timezone.utc) - d) < timedelta(days=24 * 30)


def _fetch_setu(cin: str) -> Optional[dict]:
    cid = os.environ.get("SETU_CLIENT_ID")
    csec = os.environ.get("SETU_CLIENT_SECRET")
    if not (cid and csec):
        return None
    url = os.environ.get("SETU_MCA_URL", "https://api.setu.co/api/verify/mca/company")
    req = urllib.request.Request(
        url,
        data=json.dumps({"cin": cin}).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-client-id": cid,
            "x-client-secret": csec,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8")).get("data") or {}
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError):
        return None


def _fetch_signzy(cin: str) -> Optional[dict]:
    key = os.environ.get("SIGNZY_API_KEY")
    if not key:
        return None
    url = os.environ.get("SIGNZY_MCA_URL", "https://api.signzy.com/api/v3/mca/company")
    req = urllib.request.Request(
        url,
        data=json.dumps({"cin": cin}).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": key},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8")).get("result") or {}
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError):
        return None


def lookup_company(cin: str, *, force_refresh: bool = False) -> dict:
    """Return normalized MCA snapshot for `cin`.

    Honours cache (TTL 90 days) unless force_refresh=True. Falls back to
    CIN-regex-only data if no provider credentials are configured.
    """
    cin = (cin or "").strip().upper()
    if not _is_valid_cin(cin):
        return _empty_snapshot(cin, reason="invalid_cin")

    cache = _load_cache()
    cached = cache.get(cin)
    if cached and not force_refresh and not _is_stale(cached.get("fetched_at", "")):
        cached["source"] = "cache"
        return cached

    provider = (os.environ.get("MCA_PROVIDER") or "").lower()
    raw: Optional[dict] = None
    if provider == "setu":
        raw = _fetch_setu(cin)
    elif provider == "signzy":
        raw = _fetch_signzy(cin)

    if not raw:
        # No provider or provider failure — return CIN-derived snapshot only
        snap = _empty_snapshot(cin, reason="no_provider" if not provider else "provider_unavailable")
    else:
        snap = _normalise_provider_response(raw, cin, provider)

    cache[cin] = snap
    _save_cache(cache)
    return snap
