"""/api/commerce/dashboard — F1 Opportunity dashboard.

GET only. Returns territory GWP range, funnel (5 stages), top leads.
Mirrors api/commerce_funding.py style: pure-function handler callable
from both Vercel handler class and local server.py.
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
    try:
        limit = int(_q(query, "limit", 10))
    except (TypeError, ValueError):
        limit = 10
    payload = metrics_service.dashboard(
        city=_q(query, "city"),
        sector=_q(query, "sector"),
        stage=_q(query, "stage"),
        limit=limit,
        sort_by=_q(query, "sort_by", "gwp_high"),
    )
    return 200, payload


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
