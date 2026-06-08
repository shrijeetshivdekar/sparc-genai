"""CLI for pricing/parameters.yaml — single source of truth maintenance.

Sub-commands:
  list [--lob DO]               show current values + sources
  edit <path> <new_value>       update a value; --reason required; appends to
                                pricing/audit_log.csv
  validate                      schema check; every value has source + confidence
  diff <git_ref>                show what changed vs. a prior git commit
  export-deck                   render parameters.yaml → pricing/ceo_deck.md

Usage:
  python -m pricing.params list
  python -m pricing.params list --lob Cyber
  python -m pricing.params edit base_rate_per_crore.DO.seriesA 50000 \\
      --reason "Tata AIG FY25 brochure update, p.5"
  python -m pricing.params validate
  python -m pricing.params diff HEAD~1
  python -m pricing.params export-deck
"""
from __future__ import annotations

import argparse
import csv
import getpass
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

PARAMS = Path(__file__).parent / "parameters.yaml"
AUDIT = Path(__file__).parent / "audit_log.csv"
DECK = Path(__file__).parent / "ceo_deck.md"

REQUIRED_LEAF_KEYS = {"value", "source", "confidence", "editable"}
REQUIRED_SOURCE_KEYS = {"type", "citation", "url", "accessed"}
VALID_CONFIDENCE = {"high", "medium", "low"}
VALID_SOURCE_TYPES = {
    "regulator", "carrier_brochure", "public_disclosure", "statute",
    "industry_report", "underwriter_judgment", "PLACEHOLDER",
}


# --- IO ----------------------------------------------------------------------

def load() -> dict:
    with open(PARAMS, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def save(data: dict):
    with open(PARAMS, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True, width=120)


def append_audit(path: str, old: str, new: str, reason: str):
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    new_file = not AUDIT.exists() or AUDIT.stat().st_size == 0
    with open(AUDIT, "a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(["timestamp", "user", "parameter_path", "old_value", "new_value", "reason"])
        w.writerow([
            datetime.now(timezone.utc).isoformat(timespec="seconds"),
            getpass.getuser(),
            path,
            old,
            new,
            reason,
        ])


# --- Path resolution: "a.b.c" → nested dict navigation -----------------------

def _split_path(path: str) -> list[str]:
    # supports "base_rate_per_crore.DO.seriesA" but keep "seriesC+" intact
    return path.split(".")


def get_at(d: dict, path: str):
    cur = d
    for k in _split_path(path):
        if not isinstance(cur, dict) or k not in cur:
            raise KeyError(f"Path not found: {path} (failed at '{k}')")
        cur = cur[k]
    return cur


def set_at(d: dict, path: str, new_value):
    keys = _split_path(path)
    cur = d
    for k in keys[:-1]:
        cur = cur[k]
    last = keys[-1]
    if isinstance(cur.get(last), dict) and "value" in cur[last]:
        cur[last]["value"] = new_value
    else:
        cur[last] = new_value


# --- Commands ----------------------------------------------------------------

def cmd_list(args):
    data = load()
    lob = args.lob
    print()
    print(f"{'PATH':<55} {'VALUE':>14} {'CONF':>6}  SOURCE")
    print("-" * 130)

    def walk(node, prefix=""):
        if isinstance(node, dict):
            if {"value", "source"} <= set(node.keys()):
                conf = node.get("confidence", "—")
                val = node.get("value")
                src = node["source"].get("citation", "")[:55]
                if lob and lob not in prefix:
                    return
                # placeholder marker
                ph = " [w]PH" if node["source"].get("type") == "PLACEHOLDER" else ""
                print(f"{prefix:<55} {str(val):>14} {conf:>6}{ph}  {src}")
                return
            for k, v in node.items():
                walk(v, f"{prefix}.{k}" if prefix else k)

    walk(data)
    print()


def cmd_edit(args):
    data = load()
    try:
        node = get_at(data, args.path)
    except KeyError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)
    if not isinstance(node, dict) or "value" not in node:
        print(f"ERROR: {args.path} does not point to a leaf with 'value'", file=sys.stderr)
        sys.exit(2)
    if not args.reason:
        print("ERROR: --reason is required for every edit", file=sys.stderr)
        sys.exit(2)
    old = node["value"]
    new = args.new_value
    # coerce to original type
    try:
        if isinstance(old, int) and not isinstance(old, bool):
            new = int(new)
        elif isinstance(old, float):
            new = float(new)
        elif isinstance(old, bool):
            new = new.lower() in ("true", "yes", "1")
    except ValueError:
        pass
    node["value"] = new
    save(data)
    append_audit(args.path, str(old), str(new), args.reason)
    print(f"[ok] {args.path}: {old} → {new}  (logged to {AUDIT.name})")


def cmd_validate(args):
    data = load()
    errors: list[str] = []
    warnings: list[str] = []
    placeholders: list[str] = []

    def is_leaf(node):
        return isinstance(node, dict) and {"value", "source"} <= set(node.keys())

    def walk(node, prefix=""):
        if isinstance(node, dict):
            if is_leaf(node):
                missing = REQUIRED_LEAF_KEYS - set(node.keys())
                if missing:
                    errors.append(f"{prefix}: missing leaf keys {missing}")
                src = node.get("source") or {}
                if not isinstance(src, dict):
                    errors.append(f"{prefix}.source must be an object")
                else:
                    sm = REQUIRED_SOURCE_KEYS - set(src.keys())
                    if sm:
                        errors.append(f"{prefix}.source missing keys {sm}")
                    if src.get("type") not in VALID_SOURCE_TYPES:
                        errors.append(f"{prefix}.source.type='{src.get('type')}' not in {VALID_SOURCE_TYPES}")
                    if src.get("type") == "PLACEHOLDER":
                        placeholders.append(prefix)
                    if src.get("type") not in ("PLACEHOLDER",) and not src.get("url", "").startswith(("http://", "https://")):
                        warnings.append(f"{prefix}.source.url is not a valid URL")
                conf = node.get("confidence")
                if conf not in VALID_CONFIDENCE:
                    errors.append(f"{prefix}.confidence='{conf}' not in {VALID_CONFIDENCE}")
                return
            for k, v in node.items():
                walk(v, f"{prefix}.{k}" if prefix else k)
        elif isinstance(node, list):
            for i, item in enumerate(node):
                walk(item, f"{prefix}[{i}]")

    walk(data)

    print()
    print(f"  Errors:        {len(errors)}")
    print(f"  Warnings:      {len(warnings)}")
    print(f"  PLACEHOLDERs:  {len(placeholders)}")
    if errors:
        print("\n  -- ERRORS --")
        for e in errors[:50]:
            print(f"    [X] {e}")
    if warnings:
        print("\n  -- WARNINGS --")
        for w in warnings[:20]:
            print(f"    w {w}")
    if placeholders:
        print("\n  -- PLACEHOLDERs (acceptable, must be flagged) --")
        for p in placeholders[:30]:
            print(f"    [w] {p}")
    print()
    sys.exit(1 if errors else 0)


def cmd_diff(args):
    ref = args.git_ref
    try:
        out = subprocess.check_output(
            ["git", "diff", f"{ref}", "--", str(PARAMS)],
            cwd=PARAMS.parent.parent,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"git diff failed: {e}", file=sys.stderr)
        sys.exit(2)
    if not out.strip():
        print(f"No changes vs {ref}.")
        return
    print(out)


def cmd_export_deck(args):
    """Render parameters.yaml → ceo_deck.md (board-pack friendly Markdown table)."""
    data = load()
    lines: list[str] = []
    lines.append("# SPARC Pricing Parameters — CEO Deck Export")
    lines.append("")
    lines.append(f"_Auto-generated {datetime.now(timezone.utc).isoformat(timespec='minutes')}_")
    lines.append("")
    lines.append(f"**Version:** {data['meta']['version']}  ")
    lines.append(f"**Jurisdiction:** {data['meta']['jurisdiction']}  ")
    lines.append(f"**Currency:** {data['meta']['currency']}")
    lines.append("")
    lines.append(f"> {data['meta']['disclaimer'].strip()}")
    lines.append("")

    placeholders_count = [0]

    def walk(node, prefix=""):
        if isinstance(node, dict):
            if {"value", "source"} <= set(node.keys()):
                conf = node.get("confidence", "—")
                val = node.get("value")
                src_t = node["source"].get("type", "—")
                src = node["source"].get("citation", "")
                url = node["source"].get("url", "")
                marker = ""
                if src_t == "PLACEHOLDER":
                    marker = " [w] **PLACEHOLDER**"
                    placeholders_count[0] += 1
                # markdown table row will be assembled by section walker
                rows.append((prefix, val, conf, f"{src}{marker}", url))
                return
            for k, v in node.items():
                walk(v, f"{prefix}.{k}" if prefix else k)

    # Group by top-level section
    for section in data:
        if section == "meta": continue
        lines.append(f"## {section}")
        lines.append("")
        rows: list[tuple] = []
        walk(data[section], section)
        if not rows:
            lines.append("_(no entries)_")
            lines.append("")
            continue
        lines.append("| Parameter | Value | Confidence | Source |")
        lines.append("|---|---:|---|---|")
        for path, val, conf, src, url in rows:
            link = f"[{src}]({url})" if url else src
            lines.append(f"| `{path}` | {val} | {conf} | {link} |")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(f"**Placeholders rendered: {placeholders_count[0]}** — each marked [w] in the Source column above.")

    DECK.write_text("\n".join(lines), encoding="utf-8")
    print(f"[ok] Wrote {DECK} ({len(lines)} lines, {placeholders_count[0]} placeholders).")


# --- main --------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(prog="python -m pricing.params",
                                description="Manage pricing/parameters.yaml")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="show current values + sources")
    p_list.add_argument("--lob", help="filter by line of business (e.g. DO, Cyber)")
    p_list.set_defaults(func=cmd_list)

    p_edit = sub.add_parser("edit", help="update a value; appends to audit_log.csv")
    p_edit.add_argument("path", help="dotted path, e.g. base_rate_per_crore.DO.seriesA")
    p_edit.add_argument("new_value", help="new value (coerced to existing type)")
    p_edit.add_argument("--reason", required=True, help="why the change — written to audit log")
    p_edit.set_defaults(func=cmd_edit)

    p_val = sub.add_parser("validate", help="schema check")
    p_val.set_defaults(func=cmd_validate)

    p_diff = sub.add_parser("diff", help="show changes vs. a git ref")
    p_diff.add_argument("git_ref", help="git reference (e.g. HEAD~1, main)")
    p_diff.set_defaults(func=cmd_diff)

    p_deck = sub.add_parser("export-deck", help="render to ceo_deck.md")
    p_deck.set_defaults(func=cmd_export_deck)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
