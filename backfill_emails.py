"""
One-time script: backfill contact_email for verified companies missing it.
Calls Gemini with a minimal prompt — just asks for the best contact email.
Saves progress after every company so it's safe to interrupt and re-run.
"""
import json, os, time, urllib.request, urllib.error
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL   = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
JSON_PATH      = Path(__file__).parent / "startup_shield_web" / "verified_companies.json"


def ask_gemini_for_email(company_name: str) -> str | None:
    prompt = (
        f'What is the best public contact email for the Indian company "{company_name}"? '
        f'Try in order: (1) founder/CEO email if publicly listed, '
        f'(2) official contact like contact@, info@, hello@ + their domain, '
        f'(3) construct from known domain pattern. '
        f'Return ONLY the email address as a plain string, nothing else. '
        f'If truly unknown, return null.'
    )
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 64,
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    )
    data = json.dumps(payload).encode("utf-8")
    req  = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"    ERROR: {e}")
        return None

    parts = body.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    text  = "".join(p.get("text", "") for p in parts).strip().strip('"').strip("'")
    if not text or text.lower() in ("null", "none", "unknown", "n/a"):
        return None
    if "@" not in text:
        return None
    return text


def main():
    if not GEMINI_API_KEY:
        print("ERROR: GEMINI_API_KEY not set in .env")
        return

    companies = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    missing   = [i for i, c in enumerate(companies) if not c.get("contact_email")]
    print(f"Total companies: {len(companies)}")
    print(f"Missing contact_email: {len(missing)}")
    print()

    updated = 0
    for idx, i in enumerate(missing):
        name = companies[i].get("startup_name", "?")
        print(f"[{idx+1}/{len(missing)}] {name} ...", end=" ", flush=True)
        email = ask_gemini_for_email(name)
        if email:
            companies[i]["contact_email"] = email
            print(f"OK  {email}")
            updated += 1
        else:
            print("--  not found")

        # Save after every company — safe to interrupt and re-run
        JSON_PATH.write_text(json.dumps(companies, ensure_ascii=False, indent=2), encoding="utf-8")

        # Small delay to stay within Gemini free-tier rate limits
        time.sleep(0.4)

    print(f"\nDone. Updated {updated}/{len(missing)} companies.")


if __name__ == "__main__":
    main()
