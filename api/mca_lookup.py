"""POST /api/mca-lookup — returns canonical MCA snapshot for a CIN.

Body: {"cin": "U72900MH2019PTC123456", "force_refresh": false}
"""

import json
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from enrichment.mca_lookup import lookup_company  # noqa: E402


class handler(BaseHTTPRequestHandler):
    def _send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            cin = (body.get("cin") or "").strip().upper()
            if not cin:
                return self._send_json(400, {"error": "cin required"})
            snap = lookup_company(cin, force_refresh=bool(body.get("force_refresh")))
            self._send_json(200, snap)
        except Exception as exc:  # noqa: BLE001
            self._send_json(500, {"error": str(exc)})
