import json
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from company_profiles import company_profile_count, get_company_profile, search_company_profiles


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        query = (params.get("q") or [""])[0]
        name = (params.get("name") or [""])[0]
        try:
            limit = int((params.get("limit") or ["25"])[0])
        except ValueError:
            limit = 25

        if name:
            profile = get_company_profile(name)
            if not profile:
                body = json.dumps({"error": "Company profile not found"}).encode("utf-8")
                self.send_response(404)
            else:
                body = json.dumps({"profile": profile}, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
        else:
            body = json.dumps(
                {"count": company_profile_count(), "matches": search_company_profiles(query, limit=limit)},
                ensure_ascii=False,
            ).encode("utf-8")
            self.send_response(200)

        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
