import json
import sys
import urllib.parse
from pathlib import Path
from http.server import BaseHTTPRequestHandler

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

_import_error = None
try:
    from startup_shield_web.server import clean_int, get_pipeline
except Exception as _exc:
    _import_error = f"{type(_exc).__name__}: {_exc}"
    clean_int = None
    get_pipeline = None


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if get_pipeline is None:
            body = json.dumps({"error": f"Backend import failed: {_import_error}"}).encode("utf-8")
            self.send_response(500)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        sector_filter = (params.get("sector") or [""])[0].strip()
        stage_filter  = (params.get("stage")  or [""])[0].strip()
        limit         = clean_int((params.get("limit") or ["500"])[0], 500)

        body = json.dumps(
            get_pipeline(sector_filter, stage_filter, limit),
            ensure_ascii=False,
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
