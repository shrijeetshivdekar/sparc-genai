"""/api/commerce/metrics — F2 RM Performance & weekly digest.

GET ?since=YYYY-MM-DD → leaderboard, conversion-by-sector, speed, digest.
POST { action:"send_digest" } → returns the digest payload + a log marker.
  (The actual email delivery is downstream of the existing outreach pipe;
   per PRD §4.F2 the deliverable here is the structured digest object.)
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
    import metrics_service
except Exception as exc:
    _import_error = f"{type(exc).__name__}: {exc}"
    metrics_service = None  # type: ignore[assignment]


def _q(query: dict, key: str, default=None):
    val = query.get(key)
    if isinstance(val, list):
        return val[0] if val else default
    return val if val is not None else default


def handle_get_request(query: dict) -> tuple[int, dict]:
    if metrics_service is None:
        return 500, {"error": f"import failed: {_import_error}"}
    return 200, metrics_service.metrics(since=_q(query, "since"))


def handle_post_request(payload: dict) -> tuple[int, dict]:
    if metrics_service is None:
        return 500, {"error": f"import failed: {_import_error}"}
    if not isinstance(payload, dict):
        return 400, {"error": "json object body required"}
    action = (payload.get("action") or "").strip()
    if action == "send_digest":
        digest = metrics_service.weekly_digest(since=payload.get("since"))
        # Mark dispatch — real email integration is downstream of /api/outreach.
        print(f"[commerce_metrics] digest dispatched: {digest['headline']}", flush=True)
        return 200, {"ok": True, "digest": digest, "dispatched": True}
    return 400, {"error": f"unknown action: {action!r}"}


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
