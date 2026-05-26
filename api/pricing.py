import dataclasses
import json
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_import_error = None
try:
    from pricing.model import load_params, quote  # noqa: E402
except Exception as _exc:
    _import_error = f"{type(_exc).__name__}: {_exc}"
    load_params = None
    quote = None


def _to_json(obj):
    if dataclasses.is_dataclass(obj):
        return _to_json(dataclasses.asdict(obj))
    if isinstance(obj, list):
        return [_to_json(item) for item in obj]
    if isinstance(obj, dict):
        return {key: _to_json(value) for key, value in obj.items()}
    return obj


def make_pricing_response(body):
    if quote is None or load_params is None:
        raise RuntimeError(f"Pricing backend import failed: {_import_error}")

    q = quote(
        revenue_current_inr=float(body["revenue_current_inr"]),
        revenue_projected_inr=float(body.get("revenue_projected_inr", float(body["revenue_current_inr"]) * 1.5)),
        nic_code=str(body["nic_code"]),
        stage=str(body["stage"]),
        state=str(body["state"]),
        headcount=int(body.get("headcount", 50)),
        years_since_incorporation=float(body.get("years_since_incorporation", 3)),
        cin=str(body.get("cin", "U99999MH2020PTC000000")),
        dpiit_recognised=bool(body.get("dpiit_recognised", False)),
        line_of_business=str(body["line_of_business"]),
        sum_insured_inr=float(body["sum_insured_inr"]),
        deductible_inr=float(body.get("deductible_inr", 100000)),
        prior_claims=[],
        underwriter_loadings_discounts=body.get("loadings", {}) or {},
    )

    params = load_params()
    catalog = {}
    for key, entry in (params.get("loadings_discounts") or {}).items():
        raw_value = entry.get("value")
        raw_confidence = entry.get("confidence", "low")
        catalog[key] = {
            "value": raw_value.get("value") if isinstance(raw_value, dict) else raw_value,
            "label": entry.get("label") or key,
            "direction": entry.get("direction", "loading"),
            "low_pct": entry.get("low_pct"),
            "mid_pct": entry.get("mid_pct"),
            "high_pct": entry.get("high_pct"),
            "applies_to": entry.get("applies_to", []),
            "rationale": entry.get("rationale", ""),
            "notes": entry.get("notes", ""),
            "source": entry.get("source", {}),
            "confidence": raw_confidence.get("value") if isinstance(raw_confidence, dict) else raw_confidence,
            "irdai_formalised": bool(entry.get("irdai_formalised", False)),
        }

    return {
        "quote": _to_json(q),
        "loadings_catalog": catalog,
    }


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

    def do_GET(self):
        self._send_json(200, {
            "ok": quote is not None and load_params is not None,
            "endpoint": "/api/pricing",
            "import_error": _import_error,
            "message": "Use POST with a pricing payload JSON body.",
        })

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            self._send_json(200, make_pricing_response(body))
        except Exception as exc:
            self._send_json(400, {"error": str(exc)})
