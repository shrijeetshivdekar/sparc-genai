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


# ── Per-product context: label + key scenario for the prompt ────────────────
_PRODUCT_CONTEXT = {
    # ── Liability ─────────────────────────────────────────────────────────────
    "PI_TECH_EO": {
        "label": "Tech E&O / Professional Indemnity",
        "scenario": "A client claims your software caused a data migration failure costing them ₹80L in downtime — PI pays your legal defence and client settlement.",
    },
    "PI": {
        "label": "Professional Indemnity",
        "scenario": "A client claims your services caused a ₹60L financial loss — PI covers your legal defence costs and any damages awarded.",
    },
    "D_AND_O": {
        "label": "Directors & Officers (D&O) Liability",
        "scenario": "An investor files a personal suit against the founders alleging misrepresentation in the Series A deck — D&O pays defence costs and settlement, protecting personal assets.",
    },
    "DNO_LIABILITY": {
        "label": "Directors & Officers (D&O) Liability",
        "scenario": "A minority shareholder sues directors over a board decision — D&O covers legal defence and any award without touching company funds.",
    },
    "CYBER": {
        "label": "Cyber Insurance",
        "scenario": "A ransomware attack encrypts customer data; CERT-In mandates a 6-hour breach report — Cyber pays the forensics team, regulator notification, and customer letters.",
    },
    "CYBER_LIABILITY": {
        "label": "Cyber Insurance",
        "scenario": "A data breach exposes 50,000 customer records — Cyber covers CERT-In notification costs, legal defence, and regulatory penalties under the DPDP Act.",
    },
    "CRIME_FIDELITY": {
        "label": "Crime & Fidelity / Employee Dishonesty",
        "scenario": "A finance team member approves fraudulent vendor invoices worth ₹35L — Crime cover reimburses the loss after the FIR is filed.",
    },
    "EMPLOYMENT_PRACTICES": {
        "label": "Employment Practices Liability (EPLI)",
        "scenario": "An ex-employee files wrongful termination and POSH Act complaints — EPLI pays legal defence, HR consulting, and any tribunal award.",
    },
    "COMMERCIAL_GENERAL_LIABILITY": {
        "label": "Commercial General Liability (CGL)",
        "scenario": "A contractor injured at your office during a product demo files a ₹25L bodily-injury claim — CGL covers medical expenses and legal defence.",
    },
    "CGL": {
        "label": "Commercial General Liability (CGL)",
        "scenario": "A client's employee is injured at your premises during an on-site visit and files a ₹30L claim — CGL covers compensation and legal costs.",
    },
    "PUBLIC_LIABILITY": {
        "label": "Public Liability",
        "scenario": "A visitor slips and fractures their wrist at your office — Public Liability covers the ₹40L compensation and legal defence.",
    },
    "PRODUCT_LIABILITY": {
        "label": "Product Liability",
        "scenario": "A hardware defect in your IoT device causes a fire at a client's premises — Product Liability pays the property damage claim and legal costs.",
    },
    # ── Property & Engineering ────────────────────────────────────────────────
    "FIRE_AND_PROPERTY": {
        "label": "Fire & Property Insurance",
        "scenario": "A server room fire destroys ₹1.2Cr of equipment — Fire & Property pays replacement cost and covers business interruption while you rebuild.",
    },
    "MARINE_CARGO": {
        "label": "Marine Cargo Insurance",
        "scenario": "A shipment of hardware components is damaged in transit — Marine Cargo pays replacement cost and prevents a supply-chain delay from becoming a balance-sheet hit.",
    },
    "MOTOR_FLEET": {
        "label": "Motor Fleet Insurance",
        "scenario": "One of your delivery vehicles causes a third-party accident — Motor Fleet covers third-party liability and vehicle repair under a single policy.",
    },
    # ── Employee Benefits ─────────────────────────────────────────────────────
    "GROUP_HEALTH": {
        "label": "Group Health Insurance",
        "scenario": "A senior engineer requires emergency hospitalisation — a ₹5L floater family cover means zero out-of-pocket expense and zero attrition risk.",
    },
    "EMPLOYEE_HEALTH": {
        "label": "Employee Health Insurance (Group Mediclaim)",
        "scenario": "A key engineer is hospitalised for surgery costing ₹4.2L — Group Mediclaim covers the full bill, preventing the employee from dipping into personal savings and considering other offers.",
    },
    "GROUP_PA": {
        "label": "Group Personal Accident (GPA)",
        "scenario": "A field engineer fractures their arm on-site — GPA pays hospitalisation, temporary disability wages, and permanent disability compensation if applicable.",
    },
    "GPA": {
        "label": "Group Personal Accident (GPA)",
        "scenario": "An employee involved in a road accident while on company work suffers a disability — GPA covers medical costs and pays a disability benefit to the employee.",
    },
    "EMPLOYEES_COMP": {
        "label": "Employees' Compensation Insurance",
        "scenario": "A warehouse worker suffers a back injury lifting equipment — Employees' Compensation pays the statutory compensation under the EC Act 2023, protecting the company from a labour court claim.",
    },
    "WORKMEN_COMPENSATION": {
        "label": "Workmen's Compensation / EC Insurance",
        "scenario": "A field technician is injured during installation — WC pays statutory compensation under the EC Act, covering medical expenses and disability benefits.",
    },
    "KEY_PERSON": {
        "label": "Key Person Insurance",
        "scenario": "A co-founder's sudden critical illness forces a 6-month leave — Key Person pays the company a lump sum to hire an interim leader and cover revenue impact.",
    },
    "GROUP_CRITI_SHIELD": {
        "label": "Group Critical Illness Cover",
        "scenario": "A senior employee is diagnosed with cancer — Critical Illness pays a ₹10L lump sum directly to the employee, covering treatment costs not reimbursed by the primary health policy.",
    },
    "GROUP_HOSPISHIELD": {
        "label": "Group Hospital Cash / HospiShield",
        "scenario": "An employee is hospitalised for 7 days — HospiShield pays ₹2,000/day in cash benefit regardless of actual bills, covering daily incidentals and income loss during recovery.",
    },
    # ── Financial Lines ───────────────────────────────────────────────────────
    "TRADE_CREDIT": {
        "label": "Trade Credit Insurance",
        "scenario": "Your largest enterprise client goes into insolvency with ₹1.8Cr in unpaid invoices — Trade Credit reimburses up to 85% of the outstanding receivable.",
    },
}

def _product_context(key):
    ctx = _PRODUCT_CONTEXT.get(key)
    if ctx:
        return ctx
    clean = key.replace("_", " ").title()
    return {"label": clean, "scenario": f"Cover for {clean.lower()} exposures."}


# ── Collect all products to draft for ───────────────────────────────────────
def _all_products(recommendations, bundle_match, limit=8):
    seen = set()
    products = []
    bm = bundle_match or {}
    # primary bundle covers first
    for tier in ("mandatory_covers", "optional_covers"):
        for c in bm.get(tier, []):
            key = c if isinstance(c, str) else c.get("key", "")
            if key and key not in seen:
                seen.add(key)
                products.append(key)
    # companion bundle covers (Group Safeguard + Business Shield pairing)
    companion = bm.get("companion_bundle") or {}
    for tier in ("mandatory_covers", "optional_covers"):
        for c in companion.get(tier, []):
            key = c if isinstance(c, str) else c.get("key", "")
            if key and key not in seen:
                seen.add(key)
                products.append(key)
    # fill remaining slots from standalone recommendations
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
    name     = profile.get("startup_name", "the startup")
    sector   = profile.get("sector", "technology")
    stage    = profile.get("funding_stage", "early-stage")
    team     = profile.get("team_size", "")
    regs     = (profile.get("regulatory") or [])[:2]
    products = _all_products(recommendations, bundle_match, limit=8)

    top_risks = sorted((scores or {}).items(), key=lambda x: x[1], reverse=True)[:2]
    risk_names = " and ".join(k for k, _ in top_risks) if top_risks else "liability and cyber risk"

    team_line = f"{team}-person team" if team else "growing team"
    reg_line  = f", {', '.join(regs)}" if regs else ""

    product_lines = "\n".join(
        f"- {key}: {_product_context(key)['label']} | claim: {_product_context(key)['scenario']}"
        for key in products
    )

    contact_block = (
        f"Warm regards,\n{contacts['RM_NAME']}\n"
        f"{contacts['RM_PHONE']} | {contacts['RM_EMAIL']}\n"
        f"{contacts['RM_OFFICE']}"
    )

    signal_line = _signal_line(signal_context)

    return f"""You are an ICICI Lombard RM. Write outreach for {name} ({sector}, {stage}, {team_line}{reg_line}).
Top risks: {risk_names}.{f' Note: {signal_line}' if signal_line else ''}

For EACH product below write one email and one WhatsApp.

Products:
{product_lines}

EMAIL FORMAT (use for every product):
Subject: [specific to {name} and the cover]
Body:
Dear {name} team,
Greetings from ICICI Lombard!

• Why it matters for you: [1 sentence — company-specific reason referencing their sector/stage/regulatory exposure]
• If uninsured: [1 sentence realistic claim scenario using the claim hint above, include INR amount]
• What it covers: [1 sentence on policy scope]
• Next step: We'd love to walk you through this — no pressure, just a friendly conversation.

{contact_block}

WHATSAPP FORMAT (use for every product):
Hi {name} team! [1-2 sentences on the specific risk and cover]. Let's connect — {contacts['RM_NAME']}, {contacts['RM_PHONE']}

Return ONLY valid JSON, no markdown:
{{"PRODUCT_KEY": {{"email_subject": "...", "email_body": "...", "whatsapp": "..."}}}}
Keys must exactly match: {", ".join(products)}"""


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
            "temperature": 0.5,
            "maxOutputTokens": 2500,
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
    timeout = int(os.environ.get("GEMINI_TIMEOUT_SECONDS", "30"))
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
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
        self._send(200, json.dumps({"ok": True, "endpoint": "/api/outreach"}).encode())

    def do_POST(self):
        try:
            length  = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        except Exception:
            self._send(400, json.dumps({"error": "Invalid JSON."}).encode())
            return

        profile         = payload.get("profile") or {}
        scores          = payload.get("scores") or {}
        recommendations = payload.get("recommendations") or []
        bundle_match    = payload.get("bundle_match") or {}
        signal_context  = payload.get("signal_context") or {}

        contacts = _contacts()
        prompt   = _build_prompt(profile, scores, recommendations, bundle_match, signal_context, contacts)

        raw, err = _call_gemini(prompt)

        if not isinstance(raw, dict):
            self._send(500, json.dumps({"error": err or "Outreach generation failed."}).encode())
            return

        # Normalise: ensure every product key has all three fields
        products = _all_products(recommendations, bundle_match, limit=8)
        normalized = {}
        for key in products:
            item  = raw.get(key) or {}
            label = _product_context(key)["label"]
            company = profile.get("startup_name", "your company")
            normalized[key] = {
                "email_subject": item.get("email_subject") or f"A tailored {label} recommendation for {company}",
                "email_body":    item.get("email_body") or "",
                "whatsapp":      item.get("whatsapp") or "",
            }

        self._send(200, json.dumps({
            "outreach_prompts":   normalized,
            "outreach_source":    "gemini",
            "outreach_error":     None,
            "objection_handlers": [],
        }, ensure_ascii=False).encode("utf-8"))
