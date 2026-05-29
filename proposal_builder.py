"""F3 Proposal builder — DESIGN-themed HTML proposal artifact.

Per TRD §6 and Risk register: ships HTML themed to DESIGN.md tokens; the
client converts to PDF via browser print (Save as PDF). Stays stdlib-light,
works inside the Vercel serverless context with no binary dependencies.

Public surface:
    build_proposal_payload(account_id, analysis, *, db_path=None) -> dict
    render_html(payload) -> str
    generate_proposal(account_id, analysis, *, db_path=None) -> dict

The mandatory disclaimer (PRD §4.F3) is locked verbatim in ``DISCLAIMER``
and rendered as plain text — it is not a template variable.
"""

from __future__ import annotations

import html as _html
import json
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path

import db
import gwp_estimator

PROJECT_ROOT = Path(__file__).resolve().parent
TEMPLATE_PATH = PROJECT_ROOT / "templates" / "proposal.html"

DISCLAIMER = (
    "Indicative only under IRDAI File-and-Use detariffed regime. "
    "Not a bindable quote. Valid 30 days, subject to underwriting confirmation."
)

_DEFAULT_RM = {
    "name":   "Shrijeet Shivdekar",
    "office": "ICICI Lombard General Insurance — Commercial Lines",
    "phone":  "9876543210",
    "email":  "ilom43171@icicilombard.com",
}


# ─── payload assembly ─────────────────────────────────────────

def _esc(s) -> str:
    return _html.escape(str(s) if s is not None else "", quote=True)


def _new_proposal_id() -> str:
    return "prop_" + secrets.token_hex(8)


def _fmt_inr_range(low: int, high: int) -> str:
    """Format a (low, high) INR rupee range as ``₹L–H Cr`` / ``₹L–H L``."""
    def _fmt_one(n: int) -> tuple[str, str]:
        n = int(n or 0)
        if n >= 10_000_000:  # ≥ 1 Cr
            cr = n / 1e7
            return (f"{cr:.1f}".rstrip("0").rstrip("."), "Cr")
        if n >= 100_000:     # ≥ 1 L
            return (f"{round(n / 1e5)}", "L")
        return (f"{n:,}", "")
    lo_n, lo_u = _fmt_one(low)
    hi_n, hi_u = _fmt_one(high)
    if lo_u == hi_u and lo_u:
        return f"₹{lo_n}–{hi_n} {hi_u}"
    return f"₹{lo_n}{(' ' + lo_u) if lo_u else ''} – ₹{hi_n}{(' ' + hi_u) if hi_u else ''}"


def _profile_facts(profile: dict, account_row: dict | None) -> dict:
    profile = profile or {}
    return {
        "company": (profile.get("startup_name")
                    or (account_row or {}).get("name")
                    or "—"),
        "sector":  profile.get("sector") or (account_row or {}).get("sector") or "—",
        "stage":   profile.get("funding_stage") or (account_row or {}).get("funding_stage") or "—",
        "city":    profile.get("city") or (account_row or {}).get("city") or "—",
    }


def _bundle_facts(analysis: dict) -> dict:
    """Pull bundle name, fit %, mandatory + optional covers from a SPARC result."""
    if not isinstance(analysis, dict):
        return {"name": "—", "fit_pct": 0.0, "covers": []}
    bm = analysis.get("bundle_match") or {}
    name = bm.get("name") or analysis.get("recommended_bundle") or "—"
    fit_pct = float(bm.get("fit_pct") or bm.get("fit") or 0)

    def _str_covers(items, default_why=""):
        out = []
        if isinstance(items, list):
            for it in items:
                if isinstance(it, str):
                    out.append({"cover": it, "why": default_why})
                elif isinstance(it, dict):
                    out.append({
                        "cover": str(it.get("name") or it.get("product_key") or it.get("key") or "—"),
                        "why": str(it.get("why") or it.get("reason") or default_why),
                    })
        return out

    covers = (
        _str_covers(bm.get("mandatory_covers"), default_why="Mandatory for this bundle profile.")
        + _str_covers(bm.get("optional_covers"), default_why="Optional cover indicated for this profile.")
    )
    if not covers:
        # Fall back to top-level recommendations if bundle_match was sparse.
        covers = _str_covers(analysis.get("recommendations"), default_why="Recommended by SPARC engine.")
    return {"name": name, "fit_pct": fit_pct, "covers": covers}


def _gwp_for_proposal(profile: dict, covers: list[dict]) -> dict:
    cover_keys = [c["cover"] for c in covers]
    g = gwp_estimator.estimate_gwp(profile or {}, covers=cover_keys)
    # Index per_cover by cover name for fast lookup in the template
    g["per_cover_by_name"] = {row["cover"]: row for row in g.get("per_cover", [])}
    return g


def _trigger_facts(analysis: dict) -> list[dict]:
    """Pull the regulatory-trigger list off the analysis result."""
    if not isinstance(analysis, dict):
        return []
    triggers = (
        analysis.get("display_regulatory_triggers")
        or analysis.get("regulatory_triggers_fired")
        or []
    )
    out = []
    for t in triggers[:8]:  # cap so the proposal stays one-sitting readable
        if isinstance(t, dict):
            out.append({
                "regulation": str(t.get("regulation") or t.get("reg") or t.get("name") or "—"),
                "requirement": str(t.get("requirement") or t.get("text") or t.get("description") or ""),
            })
        elif isinstance(t, str):
            out.append({"regulation": "Trigger", "requirement": t})
    return out


def _rm_facts(rm_row: dict | None) -> dict:
    if not rm_row:
        return dict(_DEFAULT_RM)
    return {
        "name":   rm_row.get("name")   or _DEFAULT_RM["name"],
        "office": rm_row.get("office") or _DEFAULT_RM["office"],
        "phone":  rm_row.get("phone")  or _DEFAULT_RM["phone"],
        "email":  rm_row.get("rm_email") or rm_row.get("email") or _DEFAULT_RM["email"],
    }


def _fetch_account(conn, account_id: str) -> tuple[dict | None, dict | None]:
    """Return (account_row_dict, rm_row_dict). Either may be None."""
    if not account_id:
        return None, None
    acct = conn.execute(
        "SELECT * FROM accounts WHERE account_id = ?", (account_id,),
    ).fetchone()
    if not acct:
        return None, None
    acct_d = dict(acct)
    rm_row = None
    if acct_d.get("rm_email"):
        rm = conn.execute(
            "SELECT * FROM rms WHERE rm_email = ?", (acct_d["rm_email"],),
        ).fetchone()
        rm_row = dict(rm) if rm else None
    return acct_d, rm_row


def build_proposal_payload(
    account_id: str | None,
    analysis: dict | None,
    *,
    db_path=None,
) -> dict:
    """Compose the dict the HTML template will consume.

    ``analysis`` is the SPARC engine result (``window.__result`` shape).
    ``account_id`` is optional — if present we enrich profile/RM from DB.
    """
    analysis = analysis or {}
    profile = analysis.get("profile") if isinstance(analysis.get("profile"), dict) else {}

    account_row, rm_row = None, None
    if account_id:
        db.migrate(db_path)
        conn = db.get_conn(db_path)
        try:
            account_row, rm_row = _fetch_account(conn, account_id)
            if account_row and not profile:
                try:
                    profile = json.loads(account_row.get("profile_json") or "{}")
                except Exception:
                    profile = {}
        finally:
            conn.close()

    bundle  = _bundle_facts(analysis)
    gwp     = _gwp_for_proposal(profile, bundle["covers"])
    facts   = _profile_facts(profile, account_row)
    rm      = _rm_facts(rm_row)
    trigs   = _trigger_facts(analysis)

    now = datetime.now(timezone.utc)
    valid_until = now + timedelta(days=30)

    proposal_id = _new_proposal_id()
    base = (analysis.get("_origin_url") or "https://sparc.icicilombard.com")
    analysis_url = f"{base}/?account={account_id}" if account_id else base

    return {
        "proposal_id":    proposal_id,
        "generated_at":   now.isoformat(),
        "generated_date": now.strftime("%d %b %Y"),
        "valid_until":    valid_until.isoformat(),
        "valid_until_date": valid_until.strftime("%d %b %Y"),
        "company":  facts["company"],
        "sector":   facts["sector"],
        "stage":    facts["stage"],
        "city":     facts["city"],
        "bundle":   bundle,        # {name, fit_pct, covers:[{cover, why}]}
        "gwp":      gwp,           # {low_inr, high_inr, basis, ..., per_cover_by_name}
        "triggers": trigs,         # [{regulation, requirement}]
        "rm":       rm,            # {name, office, phone, email}
        "analysis_url": analysis_url,
        "account_id": account_id,
        "disclaimer": DISCLAIMER,
    }


# ─── HTML rendering ───────────────────────────────────────────

def _render_covers_rows(payload: dict) -> str:
    bundle = payload.get("bundle") or {}
    per_cover_by_name = (payload.get("gwp") or {}).get("per_cover_by_name") or {}
    rows = []
    for c in bundle.get("covers", []):
        cover_name = c.get("cover") or "—"
        why = c.get("why") or ""
        band = per_cover_by_name.get(cover_name) or {}
        range_str = _fmt_inr_range(band.get("low_inr", 0), band.get("high_inr", 0)) \
            if (band.get("low_inr") or band.get("high_inr")) else "—"
        rows.append(
            f"<tr><td><strong>{_esc(cover_name)}</strong></td>"
            f"<td>{_esc(why)}</td>"
            f"<td class='range'>{_esc(range_str)}</td></tr>"
        )
    if not rows:
        rows.append("<tr><td colspan='3' style='color:var(--ink-faint);text-align:center;padding:24px;'>No covers in this bundle.</td></tr>")
    return "\n".join(rows)


def _render_triggers_block(payload: dict) -> str:
    triggers = payload.get("triggers") or []
    if not triggers:
        return ""
    items = "\n".join(
        f"<li><strong>{_esc(t.get('regulation', ''))}</strong> · {_esc(t.get('requirement', ''))}</li>"
        for t in triggers
    )
    return (
        '<section><div class="section-h">Regulatory triggers (Indian regime)</div>'
        f'<ul class="triggers">{items}</ul></section>'
    )


def render_html(payload: dict) -> str:
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    gwp = payload.get("gwp") or {}
    bundle = payload.get("bundle") or {}
    fit_pct = bundle.get("fit_pct") or 0
    bundle_fit_text = (
        f"{fit_pct:.0f}% fit for this profile"
        if fit_pct else "Recommended for this profile"
    )
    substitutions = {
        "{{PROPOSAL_ID}}":     _esc(payload.get("proposal_id", "")),
        "{{GENERATED_DATE}}":  _esc(payload.get("generated_date", "")),
        "{{VALID_UNTIL}}":     _esc(payload.get("valid_until_date", "")),
        "{{COMPANY_NAME}}":    _esc(payload.get("company", "—")),
        "{{SECTOR}}":          _esc(payload.get("sector", "—")),
        "{{STAGE}}":           _esc(payload.get("stage", "—")),
        "{{CITY}}":            _esc(payload.get("city", "—")),
        "{{BUNDLE_NAME}}":     _esc(bundle.get("name", "—")),
        "{{BUNDLE_FIT_TEXT}}": _esc(bundle_fit_text),
        "{{COVERS_ROWS}}":     _render_covers_rows(payload),
        "{{TOTAL_GWP_RANGE}}": _esc(_fmt_inr_range(gwp.get("low_inr", 0), gwp.get("high_inr", 0))),
        "{{TRIGGERS_BLOCK}}":  _render_triggers_block(payload),
        "{{RM_NAME}}":         _esc(payload["rm"]["name"]),
        "{{RM_OFFICE}}":       _esc(payload["rm"]["office"]),
        "{{RM_PHONE}}":        _esc(payload["rm"]["phone"]),
        "{{RM_EMAIL}}":        _esc(payload["rm"]["email"]),
        "{{ANALYSIS_URL}}":    _esc(payload.get("analysis_url", "")),
        "{{DISCLAIMER}}":      _esc(payload.get("disclaimer", DISCLAIMER)),
    }
    for key, value in substitutions.items():
        template = template.replace(key, value)
    return template


# ─── one-call orchestrator + persistence ───────────────────────

def generate_proposal(
    account_id: str | None,
    analysis: dict | None,
    *,
    db_path=None,
) -> dict:
    """Build payload, render HTML, persist a proposals row.

    Returns ``{proposal_id, html, generated_at, valid_until, disclaimer,
    bundle, gwp_low_inr, gwp_high_inr}``.
    """
    payload = build_proposal_payload(account_id, analysis, db_path=db_path)
    html = render_html(payload)

    gwp = payload.get("gwp") or {}
    bundle = payload.get("bundle") or {}

    # Persist if we have an account_id; otherwise return the artifact only.
    if account_id:
        db.migrate(db_path)
        conn = db.get_conn(db_path)
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO proposals (
                      proposal_id, account_id, analysis_id, pdf_path,
                      bundle, gwp_low_inr, gwp_high_inr,
                      valid_until, rm_email
                    ) VALUES (?, ?, NULL, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        payload["proposal_id"], account_id,
                        f"/proposals/{payload['proposal_id']}.html",
                        bundle.get("name"),
                        int(gwp.get("low_inr", 0)), int(gwp.get("high_inr", 0)),
                        payload.get("valid_until"),
                        payload["rm"].get("email"),
                    ),
                )
                conn.execute(
                    """
                    INSERT INTO events (
                      kind, rm_email, account_id, gwp_low_inr, gwp_high_inr, meta_json
                    ) VALUES ('proposal_generated', ?, ?, ?, ?, ?)
                    """,
                    (
                        payload["rm"].get("email"), account_id,
                        int(gwp.get("low_inr", 0)), int(gwp.get("high_inr", 0)),
                        json.dumps({"proposal_id": payload["proposal_id"]}),
                    ),
                )
        finally:
            conn.close()

    return {
        "proposal_id":  payload["proposal_id"],
        "html":         html,
        "generated_at": payload["generated_at"],
        "valid_until":  payload["valid_until"],
        "disclaimer":   payload["disclaimer"],
        "bundle":       bundle.get("name"),
        "gwp_low_inr":  int(gwp.get("low_inr", 0)),
        "gwp_high_inr": int(gwp.get("high_inr", 0)),
    }
