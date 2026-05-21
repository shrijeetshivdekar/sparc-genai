import json
import sys
from pathlib import Path
from http.server import BaseHTTPRequestHandler

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

_import_error = None
try:
    from startup_shield_web.server import autofill_and_analyze
except Exception as _exc:
    _import_error = f"{type(_exc).__name__}: {_exc}"
    autofill_and_analyze = None


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps({
            "ok": autofill_and_analyze is not None,
            "endpoint": "/api/autofill",
            "import_error": _import_error,
            "message": "Use POST with {company_name, signal_context?}.",
        }).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if autofill_and_analyze is None:
            body = json.dumps({"error": f"Backend import failed: {_import_error}"}).encode("utf-8")
            self.send_response(500)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            company_name = (payload.get("company_name") or "").strip()
            if not company_name:
                body = json.dumps({"error": "company_name is required."}).encode("utf-8")
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            result = autofill_and_analyze(company_name, payload.get("signal_context"))
            status = 200 if not result.get("error") else 500
            body = json.dumps(result, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
        except Exception as exc:
            body = json.dumps({"error": str(exc)}).encode("utf-8")
            self.send_response(500)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
