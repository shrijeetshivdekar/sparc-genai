"""
Structured GenAI reranking for SPARC recommendations.

This module never decides eligibility. It only lets a model rerank products and
bundles that the deterministic engine has already shortlisted.
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple


VALID_GENAI_MODES = {"off", "shadow", "primary"}


class GenAIRecommendationError(ValueError):
    """Raised when model output is malformed or violates deterministic gates."""


@dataclass
class GenAIRerankResult:
    payload: Dict[str, Any]
    mode: str
    enabled: bool
    source: str
    error: Optional[str]
    recommendations: List[Dict[str, Any]]
    bundle_match: Optional[Dict[str, Any]]
    audit: Dict[str, Any]
    shadow_diff: Optional[Dict[str, Any]]
    applied: bool = False


def normalize_mode(value: Optional[str]) -> str:
    mode = (value or "off").strip().lower()
    return mode if mode in VALID_GENAI_MODES else "off"


def build_shortlist(payload: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    products = []
    for item in payload.get("recommendations") or []:
        key = item.get("key")
        if not key:
            continue
        products.append({
            "key": key,
            "name": item.get("name", key),
            "score": item.get("score"),
            "priority": item.get("priority"),
            "mandatory": bool(item.get("mandatory")),
            "appetite": item.get("appetite"),
            "what_it_covers": item.get("what_it_covers"),
            "nudge": item.get("nudge"),
        })

    bundles = []
    seen = set()

    def add_bundle(bundle: Optional[Dict[str, Any]]) -> None:
        if not isinstance(bundle, dict):
            return
        name = bundle.get("name")
        if not name or name in seen:
            return
        seen.add(name)
        bundles.append({
            "name": name,
            "fit_pct": bundle.get("fit_pct"),
            "criticality": bundle.get("criticality"),
            "mandatory_covers": bundle.get("mandatory_covers") or [],
            "optional_covers": bundle.get("optional_covers") or [],
            "compliance_flags": bundle.get("compliance_flags") or [],
            "regulatory_triggers_fired": bundle.get("regulatory_triggers_fired") or [],
            "description": bundle.get("description"),
        })

    add_bundle(payload.get("bundle_match"))
    for bundle in payload.get("recommended_bundle_set") or []:
        add_bundle(bundle)
    for bundle in payload.get("bundle_alternatives") or []:
        add_bundle(bundle)

    return products, bundles


def build_prompt(payload: Dict[str, Any], products: List[Dict[str, Any]], bundles: List[Dict[str, Any]]) -> str:
    profile = payload.get("profile") or {}
    profile_context = {
        "startup_name": profile.get("startup_name"),
        "sector": profile.get("sector"),
        "sub_sector": profile.get("sub_sector"),
        "funding_stage": profile.get("funding_stage"),
        "team_size": profile.get("team_size"),
        "operations": profile.get("operations"),
        "data_sensitivity": profile.get("data_sensitivity"),
        "data_handled": profile.get("data_handled") or [],
        "regulatory": profile.get("regulatory") or [],
        "physical_assets": profile.get("physical_assets") or [],
        "customer_type": profile.get("customer_type") or [],
        "annual_revenue_cr": profile.get("annual_revenue_cr"),
        "total_insurable_asset_value_cr": profile.get("total_insurable_asset_value_cr"),
        "fleet_count": profile.get("fleet_count"),
        "hardware_software_split": profile.get("hardware_software_split"),
        "gig_headcount_pct": profile.get("gig_headcount_pct"),
        "ai_in_product": profile.get("ai_in_product"),
    }
    allowed_product_keys = [item["key"] for item in products]
    allowed_bundle_names = [item["name"] for item in bundles]
    mandatory_keys = [item["key"] for item in products if item.get("mandatory")]
    regulatory_triggers = (
        payload.get("display_regulatory_triggers")
        or payload.get("regulatory_triggers_fired")
        or payload.get("regulatory_triggers")
        or []
    )
    data = {
        "profile": profile_context,
        "risk_scores": payload.get("scores") or {},
        "shortlisted_products": products,
        "shortlisted_bundles": bundles,
        "allowed_product_keys": allowed_product_keys,
        "allowed_bundle_names": allowed_bundle_names,
        "mandatory_product_keys": mandatory_keys,
        "compliance_flags": payload.get("compliance_flags") or [],
        "regulatory_triggers": regulatory_triggers,
    }
    instructions = (
        "You are an insurance underwriting AI. Rerank the shortlisted products and bundles for this startup.\n"
        "RULES:\n"
        "- Only use product_key values from allowed_product_keys. Do not invent new products.\n"
        "- Only use bundle name values from allowed_bundle_names. Do not invent new bundles.\n"
        "- Keep mandatory_product_keys in the recommendations.\n"
        "- Be concise: rationale and why_it_fits should each be one short sentence.\n"
        "- missing_information should list specific data fields that would improve confidence.\n\n"
        "INPUT DATA:\n"
        + json.dumps(data, ensure_ascii=False, sort_keys=True)
        + "\n\nRespond with ONLY a JSON object matching this exact structure (no explanation, no markdown):\n"
        '{"recommendations": [{"product_key": "<key>", "confidence": 0.0, "rationale": "<text>", '
        '"why_it_fits": "<text>", "missing_information": []}], '
        '"bundle_match": {"name": "<name>", "confidence": 0.0, "rationale": "<text>", '
        '"why_it_fits": "<text>", "missing_information": []}, '
        '"audit": {"guardrails_followed": true, "notes": []}}'
    )
    return instructions


def parse_genai_response(
    raw: Any,
    products: List[Dict[str, Any]],
    bundles: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]], Dict[str, Any]]:
    if not isinstance(raw, dict):
        raise GenAIRecommendationError("GenAI response must be a JSON object.")

    allowed_products = {item["key"]: item for item in products}
    allowed_bundles = {item["name"]: item for item in bundles}
    raw_recs = raw.get("recommendations")
    if not isinstance(raw_recs, list):
        raise GenAIRecommendationError("GenAI response missing recommendations list.")

    parsed_recs: List[Dict[str, Any]] = []
    seen_products = set()
    for item in raw_recs:
        if not isinstance(item, dict):
            raise GenAIRecommendationError("Each GenAI recommendation must be an object.")
        key = str(item.get("product_key") or item.get("key") or "").strip()
        if not key:
            raise GenAIRecommendationError("GenAI recommendation missing product_key.")
        if key not in allowed_products:
            raise GenAIRecommendationError(f"GenAI recommended ineligible product: {key}")
        if key in seen_products:
            continue
        seen_products.add(key)
        parsed_recs.append({
            "rank": len(parsed_recs) + 1,
            "product_key": key,
            "name": allowed_products[key].get("name", key),
            "confidence": _confidence(item.get("confidence")),
            "rationale": _clean_text(item.get("rationale")),
            "why_it_fits": _clean_text(item.get("why_it_fits")),
            "missing_information": _clean_string_list(item.get("missing_information")),
        })

    if not parsed_recs and allowed_products:
        raise GenAIRecommendationError("GenAI response produced no eligible product recommendations.")

    bundle_item = raw.get("bundle_match")
    parsed_bundle = None
    if bundle_item is not None:
        if not isinstance(bundle_item, dict):
            raise GenAIRecommendationError("bundle_match must be an object.")
        name = str(bundle_item.get("name") or "").strip()
        if not name:
            raise GenAIRecommendationError("bundle_match missing name.")
        if name not in allowed_bundles:
            raise GenAIRecommendationError(f"GenAI recommended ineligible bundle: {name}")
        parsed_bundle = {
            "name": name,
            "confidence": _confidence(bundle_item.get("confidence")),
            "rationale": _clean_text(bundle_item.get("rationale")),
            "why_it_fits": _clean_text(bundle_item.get("why_it_fits")),
            "missing_information": _clean_string_list(bundle_item.get("missing_information")),
        }

    audit = raw.get("audit") if isinstance(raw.get("audit"), dict) else {}
    audit = {
        "guardrails_followed": bool(audit.get("guardrails_followed", True)),
        "notes": _clean_string_list(audit.get("notes")),
        "shortlisted_product_count": len(products),
        "shortlisted_bundle_count": len(bundles),
    }
    return parsed_recs, parsed_bundle, audit


def rerank_payload(
    payload: Dict[str, Any],
    mode: str,
    model_available: bool,
    call_json: Callable[[str], Tuple[Any, Optional[str]]],
) -> GenAIRerankResult:
    mode = normalize_mode(mode)
    baseline = copy.deepcopy(payload)
    products, bundles = build_shortlist(baseline)
    base_fields = {
        "recommendation_mode": mode,
        "genai_enabled": bool(mode != "off" and model_available),
        "genai_source": "disabled" if mode == "off" else "fallback",
        "genai_error": None,
        "genai_recommendations": [],
        "genai_bundle_match": None,
        "genai_audit": _base_audit(products, bundles),
        "genai_shadow_diff": None,
    }
    baseline.update(base_fields)

    if mode == "off":
        return GenAIRerankResult(baseline, mode, False, "disabled", None, [], None, base_fields["genai_audit"], None)
    if not model_available:
        error = "GenAI recommendation mode requested but GEMINI_API_KEY is not configured."
        baseline["genai_error"] = error
        return GenAIRerankResult(baseline, mode, False, "fallback", error, [], None, baseline["genai_audit"], None)
    if not products and not bundles:
        error = "No deterministic shortlist available for GenAI reranking."
        baseline["genai_error"] = error
        return GenAIRerankResult(baseline, mode, True, "fallback", error, [], None, baseline["genai_audit"], None)

    prompt = build_prompt(baseline, products, bundles)
    try:
        raw, call_error = call_json(prompt)
    except Exception as exc:  # pragma: no cover - defensive around external client
        raw, call_error = None, str(exc)
    if call_error:
        baseline["genai_error"] = call_error
        return GenAIRerankResult(baseline, mode, True, "fallback", call_error, [], None, baseline["genai_audit"], None)

    try:
        genai_recs, genai_bundle, audit = parse_genai_response(raw, products, bundles)
    except GenAIRecommendationError as exc:
        error = str(exc)
        baseline["genai_error"] = error
        baseline["genai_audit"] = {**baseline["genai_audit"], "validation_error": error}
        return GenAIRerankResult(baseline, mode, True, "fallback", error, [], None, baseline["genai_audit"], None)

    diff = shadow_diff(payload, genai_recs, genai_bundle)
    updated = copy.deepcopy(payload)
    if mode == "primary":
        _apply_primary(updated, genai_recs, genai_bundle)

    updated.update({
        "recommendation_mode": mode,
        "genai_enabled": True,
        "genai_source": "gemini",
        "genai_error": None,
        "genai_recommendations": genai_recs,
        "genai_bundle_match": genai_bundle,
        "genai_audit": {
            **audit,
            **_base_audit(products, bundles),
            "applied": mode == "primary",
        },
        "genai_shadow_diff": diff,
    })
    return GenAIRerankResult(
        updated,
        mode,
        True,
        "gemini",
        None,
        genai_recs,
        genai_bundle,
        updated["genai_audit"],
        diff,
        applied=(mode == "primary"),
    )


def shadow_diff(
    payload: Dict[str, Any],
    genai_recs: List[Dict[str, Any]],
    genai_bundle: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    deterministic_product_keys = [item.get("key") for item in payload.get("recommendations") or [] if item.get("key")]
    genai_product_keys = [item["product_key"] for item in genai_recs]
    deterministic_bundle = (payload.get("bundle_match") or {}).get("name")
    genai_bundle_name = (genai_bundle or {}).get("name")
    product_order_changed = bool(genai_product_keys and genai_product_keys != deterministic_product_keys[:len(genai_product_keys)])
    bundle_changed = bool(genai_bundle_name and genai_bundle_name != deterministic_bundle)
    return {
        "deterministic_product_keys": deterministic_product_keys,
        "genai_product_keys": genai_product_keys,
        "product_order_changed": product_order_changed,
        "deterministic_bundle": deterministic_bundle,
        "genai_bundle": genai_bundle_name,
        "bundle_changed": bundle_changed,
        "changed": product_order_changed or bundle_changed,
    }


def _apply_primary(
    payload: Dict[str, Any],
    genai_recs: List[Dict[str, Any]],
    genai_bundle: Optional[Dict[str, Any]],
) -> None:
    original_products = payload.get("recommendations") or []
    by_key = {item.get("key"): item for item in original_products if item.get("key")}
    selected_keys = [item["product_key"] for item in genai_recs if item["product_key"] in by_key]
    selected = [by_key[key] for key in selected_keys]
    selected_set = set(selected_keys)

    mandatory = [
        item for item in original_products
        if item.get("mandatory") and item.get("key") not in selected_set
    ]
    selected_set.update(item.get("key") for item in mandatory if item.get("key"))
    remainder = [
        item for item in original_products
        if item.get("key") not in selected_set
    ]
    payload["recommendations"] = selected + mandatory + remainder

    if genai_bundle:
        bundle = _find_bundle_by_name(payload, genai_bundle["name"])
        if bundle:
            enriched = copy.deepcopy(bundle)
            enriched["genai_confidence"] = genai_bundle.get("confidence")
            enriched["genai_rationale"] = genai_bundle.get("rationale")
            enriched["genai_why_it_fits"] = genai_bundle.get("why_it_fits")
            enriched["genai_missing_information"] = genai_bundle.get("missing_information", [])
            payload["bundle_match"] = enriched


def _find_bundle_by_name(payload: Dict[str, Any], name: str) -> Optional[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    for key in ("bundle_match",):
        if isinstance(payload.get(key), dict):
            candidates.append(payload[key])
    for key in ("recommended_bundle_set", "bundle_alternatives"):
        for item in payload.get(key) or []:
            if isinstance(item, dict):
                candidates.append(item)
    for item in candidates:
        if item.get("name") == name:
            return item
    return None


def _base_audit(products: List[Dict[str, Any]], bundles: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "shortlist_source": "deterministic",
        "allowed_product_keys": [item["key"] for item in products],
        "allowed_bundle_names": [item["name"] for item in bundles],
        "mandatory_product_keys": [item["key"] for item in products if item.get("mandatory")],
    }


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _clean_string_list(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item or "").strip()]


def _confidence(value: Any) -> float:
    if isinstance(value, (int, float)):
        return max(0.0, min(1.0, float(value)))
    if isinstance(value, str):
        mapped = {"high": 0.85, "medium": 0.6, "low": 0.35, "very_low": 0.2}
        return mapped.get(value.strip().lower(), 0.5)
    return 0.5
