"""
Vercel serverless outreach endpoint.
Self-contained — no server.py import.
Generates AI-crafted email + WhatsApp outreach for the top recommended products.
Falls back gracefully; the frontend already shows static fallback while this loads.
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

# ── Load RM contact block ────────────────────────────────────────────────────
def _contacts():
    try:
        p = _root / "contacts.json"
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {
        "RM_NAME": "{{RM_NAME}}",
        "RM_PHONE": "{{RM_PHONE}}",
        "RM_EMAIL": "{{RM_EMAIL}}",
        "RM_OFFICE": "ICICI Lombard General Insurance - Commercial Lines",
    }


# ── Extract top products to write outreach for ──────────────────────────────
_PRODUCT_LABELS = {
    "PI_TECH_EO": "Tech E&O / PI",
    "D_AND_O": "Directors & Officers (D&O)",
    "CYBER": "Cyber Insurance",
    "CRIME_FIDELITY": "Crime & Fidelity",
    "EMPLOYMENT_PRACTICES": "Employment Practices Liability",
    "PRODUCT_LIABILITY": "Product Liability",
    "COMMERCIAL_GENERAL_LIABILITY": "Commercial General Liability",
    "WORKMEN_COMPENSATION": "Workmen's Compensation / GPA",
    "MARINE_CARGO": "Marine Cargo",
    "FIRE_AND_PROPERTY": "Fire & Property",
    "MOTOR_FLEET": "Motor Fleet",
    "GROUP_HEALTH": "Group Health Insurance",
}

def _top_products(recommendations, bundle_match, limit=3):
    seen = set()
    products = []
    # mandatory first, then optional
    for tier in ("mandatory", "optional"):
        covers = (bundle_match or {}).get(tier + "_covers", [])
        for c in covers:
            key = c if isinstance(c, str) else c.get("key", "")
            if key and key not in seen:
                seen.add(key)
                products.append(key)
    # fill from recommendations
    for r in (recommendations or []):
        key = r if isinstance(r, str) else r.get("key", "")
        if key and key not in seen:
            seen.add(key)
            products.append(key)
    return products[:limit]


def _signal_line(signal_context):
    sc = signal_context or {}
    signal = sc.get("signal") or sc.get("signal_type") or ""
    company = sc.get("company_name") or ""
    if signal and company:
        return f"We noticed {company}'s recent {signal.lower()} — congratulations!"
    if signal:
        return f"Your recent {signal.lower()} caught our attention — congratulations!"
    return ""


def _build_prompt(profile, scores, recommendations, bundle_match, signal_context, contacts):
    name = profile.get("startup_name", "the startup")
    sector = profile.get("sector", "")
    stage = profile.get("funding_stage", "")
    team = profile.get("team_size", "")
    products = _top_products(recommendations, bundle_match, limit=3)

    top_risks = sorted((scores or {}).items(), key=lambda x: x[1], reverse=True)[:3]
    risk_names = ", ".join(k for k, _ in top_risks) if top_risks else "operational, cyber, and liability"

    product_lines = "\n".join(
        f"- {key}: {_PRODUCT_LABELS.get(key, key)}" for key in products
    )
    signal_line = _signal_line(signal_context)
    contact_block = (
        f"Warm regards,\n{contacts['RM_NAME']}\n"
        f"{contacts['RM_PHONE']} | {contacts['RM_EMAIL']}\n"
        f"{contacts['RM_OFFICE']}"
    )

    return f"""You are a warm ICICI Lombard Relationship Manager writing personalised outreach for {name} ({sector}, {stage}, {team} people).

Key risk areas identified by our underwriters: {risk_names}.
{f"Signal context: {signal_line}" if signal_line else ""}

TONE RULES:
- Open every email with: "Dear {name} team,\\nGreetings from ICICI Lombard!"
- If signal context is given, use it in the first line as the reason for reaching out now.
- Attribute risk insights to "our expert underwriters" — never use scores or numbers.
- Be warm and friendly, like a trusted advisor not a salesperson.
- Emails: 80-100 words. Include subject line. Close with the contact block below.
- WhatsApp: 30-40 words, casual, include RM name and phone.
- Soft CTA: "We'd love to walk you through this — no pressure, just a friendly conversation."

Write outreach for these {len(products)} products:
{product_lines}

Contact block:
{contact_block}

Return ONLY valid JSON, no markdown fences:
{{
  "PRODUCT_KEY": {{
    "email_subject": "...",
    "email_body": "...",
    "whatsapp": "..."
  }}
}}
Use the exact product keys shown above (e.g. CYBER, D_AND_O). No extra keys."""


# ── Gemini call ──────────────────────────────────────────────────────────────
def _extract_json(text):
    start = text.find("{")
    end   = text.rfind("}")
    if start == -1 or end < start:
        return None
    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return None


def _call_gemini(prompt):
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
            "temperature": 0.4,
            "maxOutputTokens": 1500,
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
        return None, "Non-JSON envelope from Gemini."

    candidate     = body.get("candidates", [{}])[0]
    finish_reason = candidate.get("finishReason", "")
    parts         = candidate.get("content", {}).get("parts", [])
    text          = "".join(p.get("text", "") for p in parts)

    if finish_reason == "MAX_TOKENS":
        parsed = _extract_json(text)
        if isinstance(parsed, dict):
            return parsed, None
        return None, "Response truncated."

    parsed = _extract_json(text)
    if not isinstance(parsed, dict):
        return None, "Gemini did not return valid JSON."
    return parsed, None


# ── Handler ──────────────────────────────────────────────────────────────────
class handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _send(self, status, body):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._send(200, json.dumps({"ok": True, "endpoint": "/api/outreach"}).encode())

    def do_POST(self):
        try:
            length  = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        except Exception:
            self._send(400, json.dumps({"error": "Invalid JSON."}).encode())
            return

        profile        = payload.get("profile") or {}
        scores         = payload.get("scores") or {}
        recommendations = payload.get("recommendations") or []
        bundle_match   = payload.get("bundle_match") or {}
        signal_context = payload.get("signal_context") or {}

        contacts = _contacts()
        prompt   = _build_prompt(profile, scores, recommendations, bundle_match, signal_context, contacts)

        raw, err = _call_gemini(prompt)

        if not isinstance(raw, dict):
            # Return error — frontend will silently keep showing the fallback
            self._send(500, json.dumps({"error": err or "Outreach generation failed."}).encode())
            return

        # Normalise: ensure every product key has all three fields
        products = _top_products(recommendations, bundle_match, limit=3)
        normalized = {}
        for key in products:
            item = raw.get(key) or {}
            label = _PRODUCT_LABELS.get(key, key)
            company = profile.get("startup_name", "your company")
            normalized[key] = {
                "email_subject": item.get("email_subject") or f"A tailored {label} recommendation for {company}",
                "email_body":    item.get("email_body") or "",
                "whatsapp":      item.get("whatsapp") or "",
            }

        self._send(200, json.dumps({
            "outreach_prompts":  normalized,
            "outreach_source":   "gemini",
            "outreach_error":    None,
            "objection_handlers": [],
        }, ensure_ascii=False).encode("utf-8"))
