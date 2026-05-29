"""/api/commerce/funding — F5 Funding Feed.

Pure-function handlers (``handle_get_request`` / ``handle_post_request``) so
both the Vercel handler class below and the local ``startup_shield_web.server``
router can dispatch through one code path.

GET  → list open funding leads (filterable by city/sector/stage/status).
POST → action="import"  (CSV text → leads, returns counts)
     | action="claim"   (lead_id + rm_email → account_id)
"""

from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

_import_error = None
try:
    import funding_ingest
    import pipeline_service
except Exception as exc:
    _import_error = f"{type(exc).__name__}: {exc}"
    funding_ingest = None  # type: ignore[assignment]
    pipeline_service = None  # type: ignore[assignment]

_DISCLAIMER = (
    "Indicative only under IRDAI File-and-Use detariffed regime. "
    "Not a bindable quote."
)


def handle_get_request(query: dict) -> tuple[int, dict]:
    """List open leads. ``query`` is parse_qs-shape (values are lists)."""
    if funding_ingest is None:
        return 500, {"error": f"import failed: {_import_error}"}

    def _q(key, default=None):
        val = query.get(key)
        if isinstance(val, list):
            return val[0] if val else default
        return val if val is not None else default

    try:
        limit = int(_q("limit", 200))
    except (TypeError, ValueError):
        limit = 200
    leads = funding_ingest.list_leads(
        city=_q("city"),
        sector=_q("sector"),
        stage=_q("stage"),
        status=_q("status", "open"),
        limit=limit,
    )
    return 200, {"leads": leads, "count": len(leads), "disclaimer": _DISCLAIMER}


def handle_post_request(payload: dict) -> tuple[int, dict]:
    if funding_ingest is None or pipeline_service is None:
        return 500, {"error": f"import failed: {_import_error}"}
    if not isinstance(payload, dict):
        return 400, {"error": "json object body required"}

    action = (payload.get("action") or "").strip()
    if action == "import":
        csv_text = payload.get("csv") or ""
        if not csv_text.strip():
            return 400, {"error": "csv field required"}
        try:
            result = funding_ingest.ingest_csv(
                csv_text, is_text=True,
                source_label=payload.get("source_label") or "csv:upload",
            )
        except Exception as exc:
            return 500, {"error": f"ingest failed: {exc}"}
        result.setdefault("disclaimer", _DISCLAIMER)
        return 200, result

    if action == "claim":
        lead_id = (payload.get("lead_id") or "").strip()
        rm_email = (payload.get("rm_email") or "").strip()
        result = pipeline_service.claim_lead(lead_id, rm_email)
        return (200 if result.get("ok") else 400), result

    if action == "sync_signals":
        try:
            from startup_shield_web.server import get_signal_radar
            radar = get_signal_radar(limit=50, live=False)
            signals = radar.get("signals", [])
            result = funding_ingest.sync_from_signals(signals)
            result["disclaimer"] = _DISCLAIMER
            return 200, result
        except Exception as exc:
            return 500, {"error": f"sync failed: {exc}"}

    return 400, {"error": f"unknown action: {action!r}"}


# ----- Vercel handler shim (kept thin; logic lives in handle_* above) -----

class handler(BaseHTTPRequestHandler):
    def _write(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        from urllib.parse import urlparse, parse_qs
        qs = parse_qs(urlparse(self.path).query)
        status, body = handle_get_request(qs)
        self._write(status, body)

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        except Exception as exc:
            return self._write(400, {"error": f"bad request body: {exc}"})
        status, body = handle_post_request(payload)
        self._write(status, body)
