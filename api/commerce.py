"""Single Vercel entry-point for all /api/commerce/* routes.

Dispatches by path segment to the individual handler modules so local
server.py routing and the individual module imports remain unchanged.

Routes handled:
  GET/POST /api/commerce/funding
  GET      /api/commerce/dashboard
  POST     /api/commerce/proposal
  GET/POST /api/commerce/metrics
  GET/POST /api/commerce/alerts
  GET/POST /api/commerce/pipeline
"""
from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))


def _parse_body(rfile, headers) -> dict:
    try:
        length = int(headers.get("Content-Length") or 0)
        raw = rfile.read(length) if length else b""
        return json.loads(raw) if raw else {}
    except Exception:
        return {}


class handler(BaseHTTPRequestHandler):
    def _write(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _segment(self) -> str:
        """Return the last path segment, e.g. 'funding' from /api/commerce/funding."""
        return urlparse(self.path).path.rstrip("/").split("/")[-1]

    def _query(self) -> dict:
        return parse_qs(urlparse(self.path).query)

    def do_GET(self):
        seg = self._segment()
        q = self._query()
        try:
            if seg == "funding":
                from api.commerce_funding import handle_get_request
                status, body = handle_get_request(q)
            elif seg == "dashboard":
                from api.commerce_dashboard import handle_get_request
                status, body = handle_get_request(q)
            elif seg == "metrics":
                from api.commerce_metrics import handle_get_request
                status, body = handle_get_request(q)
            elif seg == "alerts":
                from api.commerce_alerts import handle_get_request
                status, body = handle_get_request(q)
            elif seg == "pipeline":
                from api.commerce_pipeline import handle_get_request
                status, body = handle_get_request(q)
            else:
                status, body = 404, {"error": f"unknown commerce route: {seg}"}
        except Exception as exc:
            status, body = 500, {"error": str(exc)}
        self._write(status, body)

    def do_POST(self):
        seg = self._segment()
        payload = _parse_body(self.rfile, self.headers)
        try:
            if seg == "funding":
                from api.commerce_funding import handle_post_request
                status, body = handle_post_request(payload)
            elif seg == "proposal":
                from api.commerce_proposal import handle_post_request
                status, body = handle_post_request(payload)
            elif seg == "metrics":
                from api.commerce_metrics import handle_post_request
                status, body = handle_post_request(payload)
            elif seg == "alerts":
                from api.commerce_alerts import handle_post_request
                status, body = handle_post_request(payload)
            elif seg == "pipeline":
                from api.commerce_pipeline import handle_post_request
                status, body = handle_post_request(payload)
            else:
                status, body = 404, {"error": f"unknown commerce route: {seg}"}
        except Exception as exc:
            status, body = 500, {"error": str(exc)}
        self._write(status, body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
