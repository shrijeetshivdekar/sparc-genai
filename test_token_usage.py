"""
Measures actual Gemini token usage across all 4 call sites per recommendation.
Patches call_gemini_json to log usageMetadata before returning.

COST WARNING: This fires 4 real Gemini API calls (~20,000 tokens).
Run only when you need to benchmark. Requires: RUN_TOKEN_BENCHMARK=1
"""

import os, sys, json, types

if not os.environ.get("RUN_TOKEN_BENCHMARK"):
    print("Skipped — set RUN_TOKEN_BENCHMARK=1 to run this benchmark (costs ~20,000 Gemini tokens).")
    sys.exit(0)

# ── load env ──────────────────────────────────────────────────────────────────
from pathlib import Path
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

# ── add server module to path ─────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent / "startup_shield_web"))
import server  # noqa: E402  (imports after sys.path patch)

# ── patch call_gemini_json to capture usageMetadata ──────────────────────────
# Must patch at module level so all internal server.py calls see the new version.
import urllib.request as _urllib_req, urllib.error as _urllib_err

_token_log: list[dict] = []
_original_call = server.call_gemini_json

def _patched_call(prompt):
    api_key = os.environ.get("GEMINI_API_KEY", "")
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{server.GEMINI_MODEL}:generateContent?key={api_key}"
    )
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": server.GEMINI_MAX_TOKENS,
            "responseMimeType": "application/json",
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }
    data = json.dumps(payload).encode("utf-8")
    body = None
    for attempt in range(2):
        try:
            req = _urllib_req.Request(
                url, data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with _urllib_req.urlopen(req, timeout=server.GEMINI_TIMEOUT_SECONDS) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            break
        except _urllib_err.HTTPError as exc:
            detail = exc.read().decode("utf-8")[:500]
            if exc.code == 503 and attempt == 0:
                import time; time.sleep(2); continue
            return None, f"Gemini HTTP {exc.code}: {detail}"
        except Exception as exc:
            return None, str(exc)

    if body is None:
        return None, "no response"

    # ── log token counts from usageMetadata ──
    usage = body.get("usageMetadata", {})
    prompt_tokens = usage.get("promptTokenCount", 0)
    output_tokens = usage.get("candidatesTokenCount", 0)
    total_tokens  = usage.get("totalTokenCount", prompt_tokens + output_tokens)
    label = prompt.strip()[:80].replace("\n", " ")
    _token_log.append({
        "label": label,
        "prompt_tokens": prompt_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
    })
    print(f"  [token] {prompt_tokens:>5} in  {output_tokens:>5} out  {total_tokens:>5} total")

    # ── parse response (mirrors server.call_gemini_json logic) ──
    candidate = body.get("candidates", [{}])[0]
    finish_reason = candidate.get("finishReason", "")
    parts = candidate.get("content", {}).get("parts", [])
    text = "".join(part.get("text", "") for part in parts)
    if finish_reason == "MAX_TOKENS":
        return None, f"MAX_TOKENS at {server.GEMINI_MAX_TOKENS}"
    parsed = server.extract_json_object(text)
    if not isinstance(parsed, dict):
        return None, f"non-JSON response (finishReason={finish_reason!r})"
    return parsed, None

# Patch at module level so all internal calls inside server.py see it
server.call_gemini_json = _patched_call


# ── sample profile (Zepto-like) ───────────────────────────────────────────────
PROFILE = {
    "startup_name": "Zepto",
    "sector": "Quick Commerce",
    "funding_stage": "Series B+",
    "team_size": 20000,
    "business_model": "B2C",
    "operations": "Hybrid",
    "physical_assets": "warehouse",
    "data_handled": ["PII", "payment_data"],
    "regulatory": ["DPDP", "FSSAI", "GST"],
    "data_records_lakhs": 500,
    "data_sensitivity": "High",
    "revenue_cr": 4454,
    "customer_type": ["consumer"],
    "payment_or_card_program": True,
    "ai_in_product": False,
    "healthcare_operations": False,
    "b2b_pct": 0,
    "export_eu_pct": 0,
}

# ── get a recommendation so we have bundle_match / scores / recommendations ───
print("\n=== Running score engine ===")
result = server.score(PROFILE)
bundle_match    = result.get("bundle_match") or {}
recommendations = result.get("recommendations") or []
scores          = result.get("scores") or {}
triggers        = result.get("triggers") or []
revenue_breakdown = result.get("revenue_breakdown") or {}
graduation_path   = result.get("graduation_path") or []
size_bucket       = result.get("size_bucket") or "mid"

print(f"Bundle matched: {bundle_match.get('name')}")
print(f"Top products  : {[r.get('key') for r in recommendations[:5]]}")

# ── fire all 4 Gemini calls ───────────────────────────────────────────────────
print("\n=== Call 1: generate_why_it_matters ===")
server.generate_why_it_matters(PROFILE, bundle_match, recommendations)

print("\n=== Call 2: generate_bundle_insights ===")
server.generate_bundle_insights(PROFILE, bundle_match, revenue_breakdown, triggers, graduation_path)

print("\n=== Call 3: outreach_prompts ===")
server.outreach_prompts(PROFILE, scores, recommendations, bundle_match, size_bucket)

print("\n=== Call 4: generate_objection_handlers ===")
server.generate_objection_handlers(PROFILE, bundle_match, scores, triggers)

# ── summary ───────────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print(f"{'Call':<5} {'Prompt in':>10} {'Output':>8} {'Total':>8}")
print("-" * 65)
call_labels = [
    "why_it_matters",
    "bundle_insights",
    "outreach_prompts",
    "objection_handlers",
]
for i, entry in enumerate(_token_log):
    label = call_labels[i] if i < len(call_labels) else f"call_{i+1}"
    print(f"{label:<22} {entry['prompt_tokens']:>8}  {entry['output_tokens']:>8}  {entry['total_tokens']:>8}")

if _token_log:
    total_in  = sum(e["prompt_tokens"] for e in _token_log)
    total_out = sum(e["output_tokens"] for e in _token_log)
    total_all = sum(e["total_tokens"]  for e in _token_log)
    print("-" * 65)
    print(f"{'TOTAL':<22} {total_in:>8}  {total_out:>8}  {total_all:>8}")
    print(f"\nGemini calls fired: {len(_token_log)}")
