"""Document-driven modifier engine.

Walks the `loadings_discounts` catalog, evaluates each entry's `trigger`
against extracted document data, returns the list of applied modifiers
(multipliers and SI floors) per cover.

Triggers are JSON-expressible (no eval()). The DSL:

    "trigger": {
        "source_doc": "<doc_type>",        # required — drives field lookup
        "field":      "<field_name>",      # required — key in extracted dict
        "operator":   ">=" | "<=" | ">" | "<" | "==" | "!=" | "in" | "contains",
        "value":      <expected>,          # threshold or set or substring
        "auto_apply": true | false         # if false, modifier is suggested but not auto-applied
    }

Special direction "si_floor" emits a si_floor_inr override rather than a
multiplier; consumed by SI computation as a post-hoc minimum.
"""

from __future__ import annotations

from typing import Iterable, Optional


# ─── Field lookup ────────────────────────────────────────────────────────────

def _lookup_field(extracted_docs: dict, mca_snapshot: dict, source_doc: str, field: str):
    """Resolve `field` from the named source.

    Extractors return {"value": ..., "confidence": ..., "source": ...} per field.
    MCA snapshot returns flat key→value.
    """
    if source_doc == "mca_filings":
        snap = mca_snapshot or {}
        # Nested aoc4 fields are also exposed flat on the snapshot for convenience.
        if field in snap:
            return snap[field]
        return (snap.get("latest_aoc4") or {}).get(field)
    bucket = (extracted_docs or {}).get(source_doc) or {}
    entry = bucket.get(field)
    if isinstance(entry, dict) and "value" in entry:
        return entry["value"]
    return entry


# ─── Operator evaluation ─────────────────────────────────────────────────────

def _evaluate(operator: str, actual, expected) -> bool:
    if actual is None:
        return False
    try:
        if operator == ">=":
            return float(actual) >= float(expected)
        if operator == "<=":
            return float(actual) <= float(expected)
        if operator == ">":
            return float(actual) > float(expected)
        if operator == "<":
            return float(actual) < float(expected)
        if operator == "==":
            return actual == expected or (
                isinstance(actual, bool) and isinstance(expected, bool) and actual == expected
            ) or str(actual).strip().lower() == str(expected).strip().lower()
        if operator == "!=":
            return actual != expected
        if operator == "in":
            return actual in (expected or [])
        if operator == "contains":
            if isinstance(actual, (list, tuple, set)):
                return expected in actual
            return str(expected).lower() in str(actual).lower()
    except (TypeError, ValueError):
        return False
    return False


# ─── Modifier evaluation ─────────────────────────────────────────────────────

def evaluate_document_modifiers(
    extracted_docs: dict,
    mca_snapshot: dict,
    catalog: dict,
) -> list[dict]:
    """Walk catalog, return list of fired modifiers.

    Each result entry:
        {
          "key": str,
          "label": str,
          "direction": "loading" | "discount" | "si_floor",
          "multiplier": float,         # for loading/discount only
          "si_floor_inr": int,         # for si_floor only
          "applies_to": [cover keys],
          "rationale": str,
          "source_doc": str,
          "source_field": str,
          "extracted_value": <any>,
          "confidence": str,
        }
    """
    out: list[dict] = []
    for key, entry in (catalog or {}).items():
        trigger = entry.get("trigger")
        if not trigger:
            continue
        source_doc = trigger.get("source_doc")
        field = trigger.get("field")
        operator = trigger.get("operator")
        expected = trigger.get("value")
        if not (source_doc and field and operator):
            continue
        actual = _lookup_field(extracted_docs, mca_snapshot, source_doc, field)
        if not _evaluate(operator, actual, expected):
            continue
        direction = entry.get("direction", "loading")
        value = float(entry.get("value", 0))
        applied = {
            "key": key,
            "label": entry.get("label") or key,
            "direction": direction,
            "applies_to": list(entry.get("applies_to") or []),
            "rationale": entry.get("rationale", ""),
            "source_doc": source_doc,
            "source_field": field,
            "extracted_value": actual,
            "confidence": entry.get("confidence", "low"),
            "auto_apply": bool(trigger.get("auto_apply", True)),
        }
        if direction == "si_floor":
            applied["si_floor_inr"] = int(entry.get("si_floor_inr") or 0)
        else:
            # value is a signed fraction (e.g., 0.4 = +40%, -0.15 = -15%);
            # convert to multiplier (1 + value).
            applied["multiplier"] = round(1.0 + value, 4)
            applied["value_pct"] = round(value * 100, 2)
        out.append(applied)
    return out


# ─── Aggregation ─────────────────────────────────────────────────────────────

def aggregate_per_cover(applied_modifiers: Iterable[dict]) -> dict:
    """Combine fired modifiers per cover.

    Returns:
        {
          "<COVER_KEY>": {
            "multiplier": float,              # product of all applied multipliers (loadings/discounts only)
            "si_floor_inr": int | None,       # max si_floor across applied modifiers
            "applied": [modifier dicts in original order]
          }
        }
    """
    out: dict = {}
    for mod in applied_modifiers:
        if not mod.get("auto_apply", True):
            continue
        for cover in mod.get("applies_to") or []:
            entry = out.setdefault(cover, {"multiplier": 1.0, "si_floor_inr": None, "applied": []})
            if mod.get("direction") == "si_floor":
                floor = int(mod.get("si_floor_inr") or 0)
                if floor and (entry["si_floor_inr"] is None or floor > entry["si_floor_inr"]):
                    entry["si_floor_inr"] = floor
            elif "multiplier" in mod:
                entry["multiplier"] = round(entry["multiplier"] * float(mod["multiplier"]), 4)
            entry["applied"].append(mod)
    return out


# ─── Convenience: combined pipeline ──────────────────────────────────────────

def evaluate_and_aggregate(
    extracted_docs: dict,
    mca_snapshot: dict,
    catalog: dict,
) -> tuple[list[dict], dict]:
    """One-call pipeline. Returns (applied_modifiers, per_cover_aggregate)."""
    applied = evaluate_document_modifiers(extracted_docs, mca_snapshot, catalog)
    aggregated = aggregate_per_cover(applied)
    return applied, aggregated
