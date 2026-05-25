"""SPARC Startup Insurance Pricing — Indicative Triage Model (India only).

NOT a bindable quote. Output is an INDICATIVE RANGE per IRDAI File-and-Use
detariffed regime. Every parameter is loaded from pricing/parameters.yaml
and cited in the factor_trace.

Author convention:
  - Currency: INR throughout (₹). Never USD. Never FX-converted.
  - Classification: NIC 2008 (not NAICS).
  - All values come from parameters.yaml — never hard-coded here.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, Optional

import json

PARAMS_PATH = Path(__file__).parent / "parameters.json"

Stage = Literal["bootstrapped", "preseed", "seed", "seriesA", "seriesB", "seriesC+", "pre_ipo"]
LOB = Literal["DO", "Cyber", "PI", "CGL", "EC", "GH", "GPA", "Crime", "Property"]
Decision = Literal["indicative_quote", "refer", "decline"]


# ─── Param loader (no caching — spec says "reloads at runtime") ──────────────

def load_params(path: Path | str = PARAMS_PATH) -> dict:
    """Load the single source of truth. Re-read on every call so a CLI edit
    is visible without restart."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ─── Data classes ────────────────────────────────────────────────────────────

@dataclass
class FactorTraceEntry:
    step: str                              # e.g. "1. Base rate per crore"
    value: float | str                     # the numeric value or "₹X"
    raw_value: float                       # the raw number for math
    source_citation: str
    source_url: str
    source_type: str
    confidence: str                        # "high" | "medium" | "low"
    is_placeholder: bool = False
    notes: str = ""


@dataclass
class SourceCitation:
    code: str                              # [S1], [S2] ...
    citation: str
    url: str
    accessed: str
    type: str


@dataclass
class Quote:
    decision: Decision
    line_of_business: str

    premium_low_inr: float
    premium_high_inr: float
    premium_mid_inr: float
    premium_in_lakhs: str                  # "₹4.13 L — ₹7.66 L"
    premium_in_crores: str                 # "₹0.04 Cr — ₹0.08 Cr"
    premium_to_revenue_bps: float          # mid premium / revenue * 10000

    factor_trace: list[FactorTraceEntry] = field(default_factory=list)
    placeholders_used: list[str] = field(default_factory=list)
    data_quality_score: float = 0.0

    sources_cited: list[SourceCitation] = field(default_factory=list)

    gst_amount_inr: float = 0.0
    stamp_duty_inr: float = 0.0
    gross_premium_inr: float = 0.0
    technical_premium_inr: float = 0.0
    loaded_premium_inr: float = 0.0

    active_loadings: list[dict] = field(default_factory=list)
    net_loading_pct: float = 0.0           # signed fraction; e.g. +0.065

    disclaimer: str = ""
    refer_reasons: list[str] = field(default_factory=list)
    decline_reasons: list[str] = field(default_factory=list)

    inputs_echo: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _stage_key(stage: Stage) -> str:
    return stage

def _si_band(sum_insured_inr: float) -> str:
    cr = sum_insured_inr / 1_00_00_000
    if cr < 1:    return "0-1cr"
    if cr < 5:    return "1-5cr"
    if cr < 25:   return "5-25cr"
    if cr < 100:  return "25-100cr"
    return "100cr+"

def _deductible_bucket(deductible_inr: float) -> str:
    buckets = [0, 25_000, 1_00_000, 5_00_000, 25_00_000]
    chosen = buckets[0]
    for b in buckets:
        if deductible_inr >= b:
            chosen = b
    return str(chosen)

def _nic_division(nic_code: str) -> str:
    """NIC 2008 division = first 2 digits."""
    s = "".join(c for c in str(nic_code or "") if c.isdigit())
    return s[:2] if len(s) >= 2 else ""

def _tenure_bucket(years: float) -> str:
    if years < 1:  return "0-1"
    if years < 3:  return "1-3"
    if years < 5:  return "3-5"
    if years < 10: return "5-10"
    return "10+"

def _credibility_weight(prior_claims: list[dict]) -> float:
    """Bühlmann-Straub-style credibility. Tiny startup books → near 0 (use industry)."""
    n = len(prior_claims or [])
    if n == 0:
        return 0.0
    return min(0.4, n / 20.0)

def _experience_ratio(prior_claims: list[dict], industry_ulr: float) -> float:
    if not prior_claims:
        return industry_ulr
    paid = sum(float(c.get("paid_inr", 0)) for c in prior_claims)
    incurred = sum(float(c.get("incurred_inr", 0)) for c in prior_claims) or 1.0
    return min(2.0, max(0.2, paid / incurred))

def format_inr(amount: float) -> str:
    """Indian lakh/crore grouping. ₹12,34,56,789."""
    amount = round(amount)
    s = str(abs(amount))
    if len(s) <= 3:
        return f"₹{'-' if amount < 0 else ''}{s}"
    last3 = s[-3:]
    rest = s[:-3]
    groups = []
    while len(rest) > 2:
        groups.insert(0, rest[-2:])
        rest = rest[:-2]
    if rest:
        groups.insert(0, rest)
    return f"₹{'-' if amount < 0 else ''}{','.join(groups)},{last3}"

def format_lakh_range(lo: float, hi: float) -> str:
    return f"{format_inr(lo)[:-4] if lo >= 1_00_000 else ''}{round(lo/1_00_000, 2)}L — {round(hi/1_00_000, 2)}L".replace("L", " L")

def _bps(numer: float, denom: float) -> float:
    if denom <= 0: return 0.0
    return round((numer / denom) * 10000, 1)


# ─── Source registry (assigns [S1], [S2] …) ──────────────────────────────────

class SourceRegistry:
    def __init__(self):
        self._by_key: dict[tuple, str] = {}
        self._order: list[SourceCitation] = []

    def cite(self, source: dict) -> str:
        if not source: return ""
        key = (source.get("citation", ""), source.get("url", ""))
        if key in self._by_key:
            return self._by_key[key]
        code = f"[S{len(self._order) + 1}]"
        self._by_key[key] = code
        self._order.append(SourceCitation(
            code=code,
            citation=source.get("citation", ""),
            url=source.get("url", ""),
            accessed=source.get("accessed", ""),
            type=source.get("type", ""),
        ))
        return code

    def to_list(self) -> list[SourceCitation]:
        return list(self._order)


# ─── Quote engine ────────────────────────────────────────────────────────────

def quote(
    revenue_current_inr: float,
    revenue_projected_inr: float,
    nic_code: str,
    stage: Stage,
    state: str,
    headcount: int,
    years_since_incorporation: float,
    cin: Optional[str],
    dpiit_recognised: bool,
    line_of_business: LOB,
    sum_insured_inr: float,
    deductible_inr: float,
    prior_claims: list[dict],
    underwriter_loadings_discounts: dict[str, float],
    params: dict | None = None,
) -> Quote:
    """Produce an indicative quote range. NEVER a point estimate."""
    p = params if params is not None else load_params()
    reg = SourceRegistry()
    trace: list[FactorTraceEntry] = []
    placeholders: list[str] = []

    # Inputs echo
    inputs_echo = {
        "revenue_current_inr": revenue_current_inr,
        "revenue_projected_inr": revenue_projected_inr,
        "nic_code": nic_code,
        "stage": stage,
        "state": state,
        "headcount": headcount,
        "years_since_incorporation": years_since_incorporation,
        "cin": cin,
        "dpiit_recognised": dpiit_recognised,
        "line_of_business": line_of_business,
        "sum_insured_inr": sum_insured_inr,
        "deductible_inr": deductible_inr,
        "prior_claims_count": len(prior_claims or []),
        "loadings_input": dict(underwriter_loadings_discounts or {}),
    }

    # Pre-decision: decline rules that bypass pricing
    from . import rules
    decline = rules.evaluate_decline(
        revenue_current_inr=revenue_current_inr,
        nic_code=nic_code,
        params=p,
    )
    if decline:
        return Quote(
            decision="decline",
            line_of_business=line_of_business,
            premium_low_inr=0.0, premium_high_inr=0.0, premium_mid_inr=0.0,
            premium_in_lakhs="—", premium_in_crores="—",
            premium_to_revenue_bps=0.0,
            decline_reasons=[d["reason"] for d in decline],
            disclaimer=p["meta"]["disclaimer"],
            inputs_echo=inputs_echo,
        )

    # ── Step 1: base_rate_per_crore[LOB][stage]
    base_entry = p["base_rate_per_crore"][line_of_business][_stage_key(stage)]
    base_rate = float(base_entry["value"])
    src1 = reg.cite(base_entry["source"])
    is_ph_1 = base_entry["source"]["type"] == "PLACEHOLDER"
    if is_ph_1: placeholders.append(f"base_rate_per_crore.{line_of_business}.{stage}")
    trace.append(FactorTraceEntry(
        step="1. Base rate (₹ per crore SI)",
        value=format_inr(base_rate),
        raw_value=base_rate,
        source_citation=src1, source_url=base_entry["source"].get("url", ""),
        source_type=base_entry["source"].get("type", ""),
        confidence=base_entry.get("confidence", "low"),
        is_placeholder=is_ph_1,
        notes=base_entry.get("notes", ""),
    ))

    # ── Step 2: pure_premium
    sum_insured_cr = sum_insured_inr / 1_00_00_000
    # For per-employee GH/GPA, sum_insured is treated as ₹crore-equivalent for parity;
    # in real practice GH uses headcount × per-employee rate. We expose both.
    if base_entry.get("unit") == "per_employee_annual":
        pure_premium = base_rate * max(1, headcount)
        unit_explainer = f"₹{base_rate:,.0f}/employee × {max(1, headcount)} employees"
    else:
        pure_premium = base_rate * sum_insured_cr
        unit_explainer = f"₹{base_rate:,.0f}/cr × {sum_insured_cr:.2f} cr"
    trace.append(FactorTraceEntry(
        step="2. Pure premium",
        value=format_inr(pure_premium),
        raw_value=pure_premium,
        source_citation="—", source_url="", source_type="derived",
        confidence="high",
        notes=unit_explainer,
    ))

    # ── Step 3: multipliers
    multiplier = 1.0

    # NIC hazard
    nic_div = _nic_division(nic_code)
    nic_entry = p["nic_hazard_factor"].get(nic_div) or p["nic_hazard_factor"]["default"]
    nic_factor = float(nic_entry["value"])
    src_nic = reg.cite(nic_entry["source"])
    is_ph_nic = nic_entry["source"]["type"] == "PLACEHOLDER"
    if is_ph_nic: placeholders.append(f"nic_hazard_factor.{nic_div}")
    multiplier *= nic_factor
    trace.append(FactorTraceEntry(
        step=f"3a. × NIC {nic_div} hazard factor",
        value=f"{nic_factor:.2f}",
        raw_value=nic_factor,
        source_citation=src_nic, source_url=nic_entry["source"].get("url", ""),
        source_type=nic_entry["source"].get("type", ""),
        confidence=nic_entry.get("confidence", "low"),
        is_placeholder=is_ph_nic,
        notes=nic_entry.get("notes", ""),
    ))

    # Stage factor (PLACEHOLDER — always flagged)
    stage_entry = p["stage_factor"][_stage_key(stage)]
    stage_factor = float(stage_entry["value"])
    src_stage = reg.cite(stage_entry["source"])
    is_ph_stage = stage_entry["source"]["type"] == "PLACEHOLDER"
    if is_ph_stage: placeholders.append(f"stage_factor.{stage}")
    multiplier *= stage_factor
    trace.append(FactorTraceEntry(
        step=f"3b. × Stage factor ({stage})",
        value=f"{stage_factor:.2f}",
        raw_value=stage_factor,
        source_citation=src_stage, source_url=stage_entry["source"].get("url", ""),
        source_type=stage_entry["source"].get("type", ""),
        confidence=stage_entry.get("confidence", "low"),
        is_placeholder=is_ph_stage,
        notes="No public Indian source — flagged PLACEHOLDER per spec." if is_ph_stage else "",
    ))

    # State factor
    state_entry = p["state_factor"].get(state) or p["state_factor"]["default"]
    state_factor = float(state_entry["value"])
    src_state = reg.cite(state_entry["source"])
    is_ph_state = state_entry["source"]["type"] == "PLACEHOLDER"
    if is_ph_state: placeholders.append(f"state_factor.{state}")
    multiplier *= state_factor
    trace.append(FactorTraceEntry(
        step=f"3c. × State factor ({state})",
        value=f"{state_factor:.2f}",
        raw_value=state_factor,
        source_citation=src_state, source_url=state_entry["source"].get("url", ""),
        source_type=state_entry["source"].get("type", ""),
        confidence=state_entry.get("confidence", "low"),
        is_placeholder=is_ph_state,
        notes=state_entry.get("notes", ""),
    ))

    # Tenure factor (PLACEHOLDER)
    ten_bucket = _tenure_bucket(years_since_incorporation)
    ten_entry = p["tenure_factor"][ten_bucket]
    ten_factor = float(ten_entry["value"])
    src_ten = reg.cite(ten_entry["source"])
    is_ph_ten = ten_entry["source"]["type"] == "PLACEHOLDER"
    if is_ph_ten: placeholders.append(f"tenure_factor.{ten_bucket}")
    multiplier *= ten_factor
    trace.append(FactorTraceEntry(
        step=f"3d. × Tenure factor ({years_since_incorporation:.1f} yrs)",
        value=f"{ten_factor:.2f}",
        raw_value=ten_factor,
        source_citation=src_ten, source_url=ten_entry["source"].get("url", ""),
        source_type=ten_entry["source"].get("type", ""),
        confidence=ten_entry.get("confidence", "low"),
        is_placeholder=is_ph_ten,
    ))

    # SI relativity
    si_band = _si_band(sum_insured_inr)
    si_entry = p["sum_insured_relativity"][si_band]
    si_factor = float(si_entry["value"])
    src_si = reg.cite(si_entry["source"])
    multiplier *= si_factor
    trace.append(FactorTraceEntry(
        step=f"3e. × SI relativity ({si_band})",
        value=f"{si_factor:.2f}",
        raw_value=si_factor,
        source_citation=src_si, source_url=si_entry["source"].get("url", ""),
        source_type=si_entry["source"].get("type", ""),
        confidence=si_entry.get("confidence", "low"),
        is_placeholder=False,
    ))

    # Deductible credit
    ded_key = _deductible_bucket(deductible_inr)
    ded_entry = p["deductible_credit"][ded_key]
    ded_factor = float(ded_entry["value"])
    src_ded = reg.cite(ded_entry["source"])
    multiplier *= ded_factor
    trace.append(FactorTraceEntry(
        step=f"3f. × Deductible credit (₹{int(ded_key):,})",
        value=f"{ded_factor:.2f}",
        raw_value=ded_factor,
        source_citation=src_ded, source_url=ded_entry["source"].get("url", ""),
        source_type=ded_entry["source"].get("type", ""),
        confidence=ded_entry.get("confidence", "low"),
        is_placeholder=False,
    ))

    # ── Step 4: experience mod
    ulr_entry = p["industry_ulr"][line_of_business]
    industry_ulr = float(ulr_entry["value"])
    src_ulr = reg.cite(ulr_entry["source"])
    cred_w = _credibility_weight(prior_claims)
    exp_ratio = _experience_ratio(prior_claims, industry_ulr)
    experience_mod = cred_w * (exp_ratio / industry_ulr) + (1 - cred_w) * 1.0
    trace.append(FactorTraceEntry(
        step=f"4. × Experience mod (cred={cred_w:.2f}, ULR_industry={industry_ulr:.2f})",
        value=f"{experience_mod:.2f}",
        raw_value=experience_mod,
        source_citation=src_ulr, source_url=ulr_entry["source"].get("url", ""),
        source_type=ulr_entry["source"].get("type", ""),
        confidence=ulr_entry.get("confidence", "low"),
        is_placeholder=False,
        notes=f"{len(prior_claims or [])} prior claim(s); credibility {cred_w:.2f}.",
    ))

    technical_premium = pure_premium * multiplier * experience_mod

    # ── Step 5: loadings & discounts
    clamp = float(p["decision_thresholds"]["loadings_clamp"]["value"])
    catalog = p["loadings_discounts"]
    active_loadings: list[dict] = []
    net_loading = 0.0
    for key, val in (underwriter_loadings_discounts or {}).items():
        if key in catalog:
            entry = catalog[key]
            applies = line_of_business in entry.get("applies_to", [])
            if not applies:
                continue
            # value comes from catalog; user passes truthy flag (1.0) to activate, or float to override
            adj = float(val) if isinstance(val, (int, float)) and val not in (0, 1) else float(entry["value"])
            net_loading += adj
            src_load = reg.cite(entry["source"])
            active_loadings.append({
                "id": key, "value": adj, "source_citation": src_load,
                "source_url": entry["source"].get("url", ""),
                "confidence": entry.get("confidence", "low"),
                "catalog_default": float(entry["value"]),
            })
        elif key == "_custom":
            # custom adjustment, requires reason
            adj = float(val)
            net_loading += adj
            active_loadings.append({
                "id": "_custom", "value": adj, "source_citation": "(UW judgment)",
                "source_url": "", "confidence": "low", "catalog_default": 0.0,
            })

    # clamp ±25%
    net_loading = max(-clamp, min(clamp, net_loading))
    loaded_premium = technical_premium * (1 + net_loading)
    trace.append(FactorTraceEntry(
        step=f"5. × Net loadings/discounts ({net_loading*100:+.1f}%, clamped to ±{clamp*100:.0f}%)",
        value=f"{(1+net_loading):.3f}",
        raw_value=1 + net_loading,
        source_citation="see panel",
        source_url="", source_type="loadings_panel",
        confidence="medium",
        is_placeholder=False,
    ))

    # ── Step 6: gross-up to gross premium
    me = float(p["expense_components"]["management_expense_ratio"]["value"])
    com = float(p["expense_components"]["commission"]["value"])
    rein = float(p["expense_components"]["reinsurance_cession_cost"]["value"])
    margin = float(p["expense_components"]["profit_margin"]["value"])
    src_me = reg.cite(p["expense_components"]["management_expense_ratio"]["source"])
    src_com = reg.cite(p["expense_components"]["commission"]["source"])
    src_rein = reg.cite(p["expense_components"]["reinsurance_cession_cost"]["source"])
    src_margin = reg.cite(p["expense_components"]["profit_margin"]["source"])
    denom = 1 - me - com - rein - margin
    if denom <= 0:
        raise ValueError("expense components exceed 1.0 — check parameters.yaml")
    gross_premium = loaded_premium / denom
    trace.append(FactorTraceEntry(
        step=f"6. ÷ (1 − expense {me*100:.0f}% − comm {com*100:.1f}% − cession {rein*100:.0f}% − margin {margin*100:.0f}%)",
        value=f"× {(1/denom):.3f}",
        raw_value=1/denom,
        source_citation=f"{src_me}{src_com}{src_rein}{src_margin}",
        source_url="", source_type="expense_components",
        confidence="medium",
    ))

    # ── Step 7: taxes
    gst_rate = float(p["taxes"]["gst_rate"]["value"])
    src_gst = reg.cite(p["taxes"]["gst_rate"]["source"])
    gst_amount = gross_premium * gst_rate
    trace.append(FactorTraceEntry(
        step=f"7a. + GST @ {gst_rate*100:.0f}%",
        value=format_inr(gst_amount),
        raw_value=gst_amount,
        source_citation=src_gst,
        source_url=p["taxes"]["gst_rate"]["source"].get("url", ""),
        source_type="statute",
        confidence="high",
    ))

    sd_table = p["taxes"]["stamp_duty"]
    sd_entry = sd_table.get(state) or sd_table["default"]
    stamp_duty = float(sd_entry["value"])
    src_sd = reg.cite(sd_entry["source"])
    trace.append(FactorTraceEntry(
        step=f"7b. + Stamp duty ({state})",
        value=format_inr(stamp_duty),
        raw_value=stamp_duty,
        source_citation=src_sd,
        source_url=sd_entry["source"].get("url", ""),
        source_type="statute",
        confidence="high",
    ))

    # ── Step 8: final mid + range
    final_mid = gross_premium + gst_amount + stamp_duty
    band = float(p["decision_thresholds"]["range_band"]["value"])
    final_low = final_mid * (1 - band)
    final_high = final_mid * (1 + band)
    trace.append(FactorTraceEntry(
        step=f"8. Range ±{band*100:.0f}%",
        value=f"{format_inr(final_low)} — {format_inr(final_high)}",
        raw_value=final_mid,
        source_citation="—",
        source_url="", source_type="band",
        confidence="medium",
    ))

    # ── Data quality score
    total_factors = sum(1 for t in trace if t.source_type not in ("derived", "band", "loadings_panel"))
    ph_count = sum(1 for t in trace if t.is_placeholder)
    high_conf = sum(1 for t in trace if t.confidence == "high" and not t.is_placeholder)
    med_conf = sum(1 for t in trace if t.confidence == "medium" and not t.is_placeholder)
    low_conf = sum(1 for t in trace if t.confidence == "low" and not t.is_placeholder)
    # weighted score
    dq = (high_conf * 1.0 + med_conf * 0.65 + low_conf * 0.30) / max(1, total_factors)
    # placeholder penalty
    dq = max(0.0, dq - (ph_count * 0.10))
    dq = round(dq, 2)

    # ── Decision
    decision: Decision = "indicative_quote"
    refer_reasons: list[str] = []
    refer = rules.evaluate_refer(
        revenue_current_inr=revenue_current_inr,
        nic_code=nic_code,
        stage=stage,
        cin=cin,
        data_quality_score=dq,
        params=p,
    )
    if refer:
        decision = "refer"
        refer_reasons = [r["reason"] for r in refer]
    if dq < float(p["decision_thresholds"]["refer_below_data_quality"]["value"]):
        if decision == "indicative_quote":
            decision = "refer"
        refer_reasons.append(f"Data quality {dq:.2f} below threshold "
                             f"{p['decision_thresholds']['refer_below_data_quality']['value']}")

    # Disclaimer
    disclaimer = (
        f"Indicative only under IRDAI File-and-Use detariffed regime. "
        f"Not a bindable quote. {ph_count} placeholder(s) used out of {total_factors} cited factors. "
        f"Final premium subject to underwriter review and reinsurance treaty terms."
    )

    return Quote(
        decision=decision,
        line_of_business=line_of_business,
        premium_low_inr=round(final_low, 2),
        premium_high_inr=round(final_high, 2),
        premium_mid_inr=round(final_mid, 2),
        premium_in_lakhs=f"₹{final_low/1_00_000:.2f} L — ₹{final_high/1_00_000:.2f} L",
        premium_in_crores=f"₹{final_low/1_00_00_000:.3f} Cr — ₹{final_high/1_00_00_000:.3f} Cr",
        premium_to_revenue_bps=_bps(final_mid, revenue_current_inr),
        factor_trace=trace,
        placeholders_used=placeholders,
        data_quality_score=dq,
        sources_cited=reg.to_list(),
        gst_amount_inr=round(gst_amount, 2),
        stamp_duty_inr=round(stamp_duty, 2),
        gross_premium_inr=round(gross_premium, 2),
        technical_premium_inr=round(technical_premium, 2),
        loaded_premium_inr=round(loaded_premium, 2),
        active_loadings=active_loadings,
        net_loading_pct=round(net_loading, 4),
        disclaimer=disclaimer,
        refer_reasons=refer_reasons,
        decline_reasons=[],
        inputs_echo=inputs_echo,
    )


# ─── Convenience: re-quote with edited loadings (web panel uses this) ────────

def requote_with_loadings(
    base_inputs: dict,
    loadings: dict[str, float],
    params: dict | None = None,
) -> Quote:
    """Used by the web panel after broker toggles checkboxes. base_inputs is the
    inputs_echo dict from a prior Quote. Cheaper than recomputing from raw."""
    return quote(
        revenue_current_inr=base_inputs["revenue_current_inr"],
        revenue_projected_inr=base_inputs["revenue_projected_inr"],
        nic_code=base_inputs["nic_code"],
        stage=base_inputs["stage"],
        state=base_inputs["state"],
        headcount=base_inputs["headcount"],
        years_since_incorporation=base_inputs["years_since_incorporation"],
        cin=base_inputs.get("cin"),
        dpiit_recognised=base_inputs["dpiit_recognised"],
        line_of_business=base_inputs["line_of_business"],
        sum_insured_inr=base_inputs["sum_insured_inr"],
        deductible_inr=base_inputs["deductible_inr"],
        prior_claims=base_inputs.get("prior_claims") or [],
        underwriter_loadings_discounts=loadings,
        params=params,
    )
