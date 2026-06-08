"""GET /api/iib/rm-dashboard - RM dashboard payload from ICICI/IIB workbooks."""

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
    import iib_dashboard_service
except Exception as exc:  # pragma: no cover
    _import_error = f"{type(exc).__name__}: {exc}"
    iib_dashboard_service = None  # type: ignore[assignment]


def _q(query: dict, key: str, default=None):
    val = query.get(key)
    if isinstance(val, list):
        return val[0] if val else default
    return val if val is not None else default


def handle_get_request(query: dict) -> tuple[int, dict]:
    if iib_dashboard_service is None:
        return 500, {"error": f"import failed: {_import_error}"}
    try:
        payload = iib_dashboard_service.load_dashboard(
            book_path=_q(query, "book_path"),
            dictionary_path=_q(query, "dictionary_path"),
        )
        return 200, payload
    except FileNotFoundError as exc:
        return 404, {"error": str(exc)}
    except Exception as exc:
        return 500, {"error": str(exc)}


class handler(BaseHTTPRequestHandler):
    def _write(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        from urllib.parse import parse_qs, urlparse

        qs = parse_qs(urlparse(self.path).query)
        status, body = handle_get_request(qs)
        self._write(status, body)

