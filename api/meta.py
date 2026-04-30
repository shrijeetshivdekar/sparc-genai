import json
from http.server import BaseHTTPRequestHandler

from startup_shield_web.server import meta


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps(meta(), ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
