"""Commerce Pipeline API — list accounts by stage and move stage."""
from __future__ import annotations
from urllib.parse import parse_qs
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import pipeline_service


def _q(query: dict, key: str, default=None):
    v = query.get(key)
    return v[0] if isinstance(v, list) and v else (v if v is not None else default)


def handle_get_request(query: dict) -> tuple[int, dict]:
    rm_email = _q(query, "rm_email") or None
    stage    = _q(query, "stage")    or None
    accounts = pipeline_service.list_pipeline(rm_email=rm_email, stage=stage)
    summary  = pipeline_service.pipeline_summary()
    return 200, {
        "ok": True,
        "accounts": accounts,
        "summary": summary,
        "disclaimer": "Indicative only under IRDAI File-and-Use detariffed regime. Not a bindable quote.",
    }


def handle_post_request(payload: dict) -> tuple[int, dict]:
    action = payload.get("action", "")
    if action == "move_stage":
        account_id = payload.get("account_id", "")
        to_stage   = payload.get("to_stage", "")
        rm_email   = payload.get("rm_email", "")
        if not account_id or not to_stage:
            return 400, {"ok": False, "error": "account_id and to_stage required"}
        result = pipeline_service.move_stage(account_id, to_stage, rm_email)
        status = 200 if result.get("ok") else 400
        return status, result
    return 400, {"ok": False, "error": f"unknown action: {action}"}


# Vercel handler shim
class handler:
    def __init__(self, environ, start_response):
        method = environ.get("REQUEST_METHOD", "GET").upper()
        qs = environ.get("QUERY_STRING", "")
        query = parse_qs(qs)
        if method == "GET":
            status, body = handle_get_request(query)
        elif method == "POST":
            try:
                length = int(environ.get("CONTENT_LENGTH") or 0)
                raw = environ["wsgi.input"].read(length)
                payload = json.loads(raw) if raw else {}
            except Exception:
                payload = {}
            status, body = handle_post_request(payload)
        else:
            status, body = 405, {"error": "Method not allowed"}
        data = json.dumps(body, ensure_ascii=False).encode()
        start_response(f"{status} OK", [
            ("Content-Type", "application/json"),
            ("Content-Length", str(len(data))),
        ])
        self.response = [data]

    def __iter__(self):
        return iter(self.response)
