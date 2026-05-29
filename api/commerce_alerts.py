"""/api/commerce/alerts — F4 renewal / upsell / at-risk / coverage-gap.

GET ?status=open&type=... → list alerts (sorted by delta GWP high desc).
                            Always includes a summary tile (renewals ≤60d
                            count + GWP-at-risk range).
POST { action:"dismiss", alert_id, rm_email? } → mark dismissed
     { action:"sweep" }                       → re-evaluate all accounts
     { action:"evaluate", account_id, new_triggers?:[] } → re-evaluate one
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
    import alert_engine
except Exception as exc:
    _import_error = f"{type(exc).__name__}: {exc}"
    alert_engine = None  # type: ignore[assignment]


_DISCLAIMER = (
    "Indicative only under IRDAI File-and-Use detariffed regime. "
    "Not a bindable quote."
)


def _q(query: dict, key: str, default=None):
    val = query.get(key)
    if isinstance(val, list):
        return val[0] if val else default
    return val if val is not None else default


def handle_get_request(query: dict) -> tuple[int, dict]:
    if alert_engine is None:
        return 500, {"error": f"import failed: {_import_error}"}
    alerts = alert_engine.list_alerts(
        status=_q(query, "status", "open"),
        alert_type=_q(query, "type"),
    )
    return 200, {
        "alerts":     alerts,
        "count":      len(alerts),
        "summary":    alert_engine.at_risk_summary(),
        "disclaimer": _DISCLAIMER,
    }


def handle_post_request(payload: dict) -> tuple[int, dict]:
    if alert_engine is None:
        return 500, {"error": f"import failed: {_import_error}"}
    if not isinstance(payload, dict):
        return 400, {"error": "json object body required"}
    action = (payload.get("action") or "").strip()
    if action == "dismiss":
        return _wrap_dismiss(payload)
    if action == "sweep":
        return 200, alert_engine.evaluate_all()
    if action == "evaluate":
        account_id = (payload.get("account_id") or "").strip()
        if not account_id:
            return 400, {"error": "account_id required for evaluate"}
        new = alert_engine.evaluate_account(
            account_id, new_triggers=payload.get("new_triggers") or None,
        )
        return 200, {"created": len(new), "alerts": new}
    return 400, {"error": f"unknown action: {action!r}"}


def _wrap_dismiss(payload: dict) -> tuple[int, dict]:
    alert_id = (payload.get("alert_id") or "").strip()
    rm_email = (payload.get("rm_email") or "").strip() or None
    result = alert_engine.dismiss_alert(alert_id, rm_email=rm_email)
    return (200 if result.get("ok") else 400), result


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
