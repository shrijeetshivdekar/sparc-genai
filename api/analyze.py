import json
import sys
from pathlib import Path
from http.server import BaseHTTPRequestHandler

# Ensure project root is on sys.path before any local imports
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

# Wrap import so a crash returns JSON instead of HTML (helps diagnose Vercel errors)
_import_error = None
try:
    from startup_shield_web.server import analyze as _analyze
except Exception as _exc:
    _import_error = f"{type(_exc).__name__}: {_exc}"
    _analyze = None


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps({
            "ok": _analyze is not None,
            "endpoint": "/api/analyze",
            "import_error": _import_error,
            "message": "Use POST with a startup profile JSON body.",
        }).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if _analyze is None:
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
            body = json.dumps(_analyze(payload), ensure_ascii=False).encode("utf-8")
            self.send_response(200)
        except Exception as exc:
            body = json.dumps({"error": str(exc)}).encode("utf-8")
            self.send_response(500)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
