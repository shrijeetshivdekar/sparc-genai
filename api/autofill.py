"""
Vercel serverless autofill endpoint.
Self-contained — does NOT import server.py.
Only calls Gemini and returns the raw profile.
The frontend then calls /api/analyze for bundle matching.
"""
import json
import os
import sys
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))


def _prompt(company_name: str) -> str:
    return f"""You are a startup analyst. Return a JSON object for "{company_name}" using public knowledge.
Use ONLY the exact enum values shown. Return ONLY the JSON, no markdown fences.

{{
  "startup_name": "{company_name}",
  "sector": <one of: "Fintech","Healthtech","SaaS / Enterprise Software","Deeptech / AI / Robotics","Edtech","D2C / Consumer Brands","Logistics / Mobility","Agritech / Foodtech","Cleantech / Climatetech","Gaming / Media / Content","HRtech","Legaltech","Proptech","Spacetech","Insurtech","Other">,
  "funding_stage": <one of: "Pre-seed","Seed","Series A","Series B+">,
  "team_size": <integer>,
  "operations": <one of: "Digital-only","Hybrid (online+offline)","Offline / Physical","Hardware / IoT","Marketplace">,
  "data_handled": <array from: ["Payments / financial transactions","Health / medical records","Personal identity data (KYC / Aadhaar)","Employee / HR data (payroll, biometrics)","Minors' / children's data","Location / GPS tracking data","Intellectual property / source code","Customer behavioural / usage data","Physical inventory / goods","Sensitive personal data (DPDP Act)","None of the above"]>,
  "regulatory": <array from: ["RBI / SEBI / IRDAI licensed","FSSAI / food safety","CDSCO / medical devices","DPDP Act obligations","DGCA / drone operations","IT Act / CERT-In obligations","Labour Codes / gig worker regulations","BIS / QCO product certification","NMC / telemedicine regulations","MV Act / transport regulations","SEBI BRSR / ESG reporting","Competition Act / CCI","EPR / environmental compliance","None / minimal"]>,
  "physical_assets": <array from: ["Office / coworking space","Warehouse / fulfilment centre","Manufacturing plant / factory","Lab / R&D equipment","Medical devices / diagnostic equipment","Vehicles / delivery fleet","Drones / UAV equipment","Kitchen / food processing","Cold chain / refrigeration","Solar / clean energy infrastructure","Retail stores / kiosks","Data centre / server room","None - fully cloud"]>,
  "ai_in_product": <true or false>,
  "has_investors": <"Yes" or "No">,
  "annual_revenue_cr": <number in INR crores, 0 if unknown>,
  "healthcare_operations": <true or false>,
  "payment_or_card_program": <true or false>,
  "contact_email": <string or null>
}}"""


def _extract_json(text: str):
    start = text.find("{")
    end   = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        return None
    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return None


def _call_gemini(prompt: str):
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return None, "GEMINI_API_KEY not configured."

    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    url   = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 1024,
            "responseMimeType": "application/json",
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }
    data = json.dumps(payload).encode("utf-8")
    req  = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            detail = exc.read().decode("utf-8")[:300]
        except Exception:
            detail = str(exc)
        return None, f"Gemini HTTP {exc.code}: {detail}"
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return None, f"Gemini request failed: {exc}"
    except json.JSONDecodeError:
        return None, "Gemini returned non-JSON envelope."

    candidate     = body.get("candidates", [{}])[0]
    finish_reason = candidate.get("finishReason", "")
    parts         = candidate.get("content", {}).get("parts", [])
    text          = "".join(p.get("text", "") for p in parts)

    if finish_reason == "MAX_TOKENS":
        return None, "Gemini response truncated (MAX_TOKENS)."

    parsed = _extract_json(text)
    if not isinstance(parsed, dict):
        print(f"[autofill] Bad JSON; finishReason={finish_reason!r}; text={text[:300]!r}", flush=True)
        return None, "Gemini did not return valid JSON."

    return parsed, None


class handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _send(self, status: int, body: bytes):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._send(200, json.dumps({
            "ok": True, "endpoint": "/api/autofill",
            "message": "POST {company_name, signal_context?} — returns raw profile only. Call /api/analyze next.",
        }).encode())

    def do_POST(self):
        try:
            length  = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        except Exception:
            self._send(400, json.dumps({"error": "Invalid JSON body."}).encode())
            return

        company_name = (payload.get("company_name") or "").strip()
        if not company_name:
            self._send(400, json.dumps({"error": "company_name is required."}).encode())
            return

        profile, err = _call_gemini(_prompt(company_name))
        if not isinstance(profile, dict):
            self._send(500, json.dumps({"error": err or "Gemini call failed."}).encode())
            return

        # Attach signal context if provided — /api/analyze will use it
        signal_context = payload.get("signal_context")
        if signal_context:
            profile["signal_context"] = signal_context

        self._send(200, json.dumps(profile, ensure_ascii=False).encode("utf-8"))
