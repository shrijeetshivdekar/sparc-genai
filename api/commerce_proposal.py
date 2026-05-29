"""/api/commerce/proposal — F3 one-click branded proposal.

POST { account_id, analysis } → { proposal_id, html, generated_at,
       valid_until, disclaimer, bundle, gwp_low_inr, gwp_high_inr }

We return the rendered HTML inline rather than a separate file path. The
client opens it in a new tab and uses the browser's Save-as-PDF flow
(per TRD §6 risk register — keeps the route stdlib-light and works on
Vercel without binary dependencies).
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
    import proposal_builder
except Exception as exc:
    _import_error = f"{type(exc).__name__}: {exc}"
    proposal_builder = None  # type: ignore[assignment]


def handle_post_request(payload: dict) -> tuple[int, dict]:
    if proposal_builder is None:
        return 500, {"error": f"import failed: {_import_error}"}
    if not isinstance(payload, dict):
        return 400, {"error": "json object body required"}
    analysis = payload.get("analysis")
    if analysis is None:
        return 400, {"error": "analysis field required"}
    account_id = (payload.get("account_id") or "").strip() or None
    try:
        result = proposal_builder.generate_proposal(account_id, analysis)
    except Exception as exc:
        return 500, {"error": f"proposal generation failed: {exc}"}
    return 200, result


class handler(BaseHTTPRequestHandler):
    def _write(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        except Exception as exc:
            return self._write(400, {"error": f"bad request body: {exc}"})
        status, body = handle_post_request(payload)
        self._write(status, body)
