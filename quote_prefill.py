"""Deterministic underwriting input suggestions for quote forms.

These values are not binding and are not used for pricing unless the user
explicitly submits them. They exist to reduce blank-form friction while keeping
quote calculation auditable and user-confirmed.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional


def suggest_quote_inputs(profile: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Return suggested quote inputs derived from startup profile fields."""
    profile = profile or {}
    stage = _stage(profile)
    sector = str(profile.get("sector") or "")
    team = _team_size(profile)
    assets = profile.get("physical_assets") or []
    data = profile.get("data_handled") or []
    data_sensitivity = str(profile.get("data_sensitivity") or "Medium")
    b2b_pct = _bounded(_float(profile.get("b2b_pct"), 0.5), 0.0, 1.0)

    revenue, revenue_source, revenue_confidence = _revenue(profile, stage, team, sector)
    property_si = _property_si(profile, stage, assets)
    equipment_si = _equipment_si(profile, property_si, assets)
    gross_profit_si = _explicit_cr(profile, "gross_profit_si_cr", "gross_profit_cr")
    if gross_profit_si is None:
        gross_profit_si = round(max(0.25, revenue * (0.35 if stage == "Series B+" else 0.30)), 2)
    payroll_cr = _payroll_proxy(profile, stage, sector, team)
    records_lakhs = _data_records_proxy(profile, revenue, team, sector, data, data_sensitivity)

    cyber_limit = _cyber_limit(profile, stage, sector, data_sensitivity, revenue)
    dno_limit = _dno_limit(profile, stage, revenue)
    pi_limit = _pi_limit(profile, stage, sector, revenue, b2b_pct)
    product_limit = _product_liability_limit(profile, sector, revenue, assets, data)
    public_limit = _explicit_cr(profile, "public_liability_limit_cr") or round(max(1.0, property_si * 0.75), 2)
    crime_limit = _explicit_cr(profile, "crime_limit_cr") or min(15.0, {
        "pre_seed": 0.5, "seed": 1.0, "series_a": 2.0, "series_b": 5.0,
        "series_b_plus": 10.0, "growth": 10.0, "late_stage": 15.0,
    }.get(stage, 2.0))
    epli_limit = _explicit_cr(profile, "employment_practices_limit_cr") or min(10.0, round(max(0.5, pi_limit * 0.4), 2))

    has_trade = _has_any(assets, "Warehouse / fulfilment centre", "Retail stores / kiosks") or "Physical inventory / goods" in data
    export_share = _float(profile.get("export_eu_pct")) + _float(profile.get("export_us_pct")) + _float(profile.get("export_china_pct"))
    cargo_turnover = _explicit_cr(profile, "cargo_annual_turnover_cr", "cargo_turnover_cr")
    if cargo_turnover is None:
        cargo_turnover = round(max(0.25, revenue * (0.55 if has_trade or export_share > 0 else 0.10)), 2)

    suggestions = {
        "annual_revenue_cr": _item(
            revenue,
            revenue_source,
            revenue_confidence,
            "Revenue is taken from the profile when present; otherwise estimated from stage, team size, and sector.",
        ),
        "team_size": _item(team, "profile", "high", "Team size from the company profile."),
        "employee_count": _item(team, "profile", "high", "Employee count suggested from team size."),
        "payroll_cr": _item(
            payroll_cr,
            "deterministic_estimate",
            "medium",
            "Payroll proxy uses team size, funding stage, and sector salary intensity.",
        ),
        "data_records_lakhs": _item(
            records_lakhs,
            "deterministic_estimate",
            "medium" if data_sensitivity == "High" or data else "low",
            "Cyber records proxy uses sector, data sensitivity, revenue, team size, and handled data categories.",
        ),
        "cyber_limit_cr": _item(
            cyber_limit,
            "deterministic_estimate",
            "medium",
            "Cyber limit proxy uses stage, sector, revenue, and data sensitivity.",
        ),
        "dno_limit_cr": _item(
            dno_limit,
            "deterministic_estimate",
            "medium",
            "D&O limit proxy uses funding stage, investor status, and revenue scale.",
        ),
        "pi_limit_cr": _item(
            pi_limit,
            "deterministic_estimate",
            "medium",
            "PI/E&O limit proxy uses stage, revenue, B2B exposure, and regulated-sector intensity.",
        ),
        "product_liability_limit_cr": _item(
            product_limit,
            "deterministic_estimate",
            "medium" if product_limit > 1.0 else "low",
            "Product liability proxy increases for physical goods, healthcare, food, hardware, and manufacturing exposure.",
        ),
        "public_liability_limit_cr": _item(
            public_limit,
            "deterministic_estimate",
            "medium",
            "Public liability proxy scales from physical asset exposure.",
        ),
        "property_sum_insured_cr": _item(
            property_si,
            "profile" if _explicit_cr(profile, "property_sum_insured_cr", "total_insurable_asset_value_cr") is not None else "deterministic_estimate",
            "high" if _explicit_cr(profile, "property_sum_insured_cr", "total_insurable_asset_value_cr") is not None else "medium",
            "Property SI uses declared asset value when present; otherwise stage and physical assets.",
        ),
        "equipment_sum_insured_cr": _item(
            equipment_si,
            "deterministic_estimate",
            "medium",
            "Equipment SI allocates property exposure to electronics, machinery, lab, server, or plant assets.",
        ),
        "gross_profit_si_cr": _item(
            round(gross_profit_si, 2),
            "profile" if _explicit_cr(profile, "gross_profit_si_cr", "gross_profit_cr") is not None else "deterministic_estimate",
            "medium",
            "BI/gross-profit SI uses declared gross profit or a revenue percentage proxy.",
        ),
        "stock_sum_insured_cr": _item(
            round(max(0.10, property_si * (0.35 if has_trade else 0.12)), 2),
            "deterministic_estimate",
            "medium" if has_trade else "low",
            "Stock SI proxy uses inventory, warehouse, retail, and physical-goods signals.",
        ),
        "cargo_turnover_cr": _item(
            cargo_turnover,
            "deterministic_estimate",
            "medium" if has_trade or export_share > 0 else "low",
            "Cargo turnover proxy uses revenue, inventory, warehouse, and export exposure.",
        ),
        "receivables_on_credit_cr": _item(
            round(max(0.25, revenue * max(0.10, b2b_pct) * 0.18), 2),
            "deterministic_estimate",
            "medium",
            "Receivables proxy uses annual revenue and B2B share.",
        ),
        "project_value_cr": _item(
            _explicit_cr(profile, "project_value_cr", "capex_project_value_cr") or round(max(0.50, property_si * 0.75), 2),
            "profile" if _explicit_cr(profile, "project_value_cr", "capex_project_value_cr") is not None else "deterministic_estimate",
            "low",
            "Project value is only a rough proxy unless capex/project value is declared.",
        ),
        "claims_last_3_years": _item(False, "deterministic_default", "low", "Use No only if confirmed by the customer."),
        "crime_limit_cr": _item(
            round(crime_limit, 2),
            "deterministic_estimate",
            "medium",
            "Crime/fidelity limit scales with funding stage and payment operations exposure.",
        ),
        "employment_practices_limit_cr": _item(
            round(epli_limit, 2),
            "deterministic_estimate",
            "medium",
            "EPLI limit proxied at 50% of PI limit — scales with headcount and governance exposure.",
        ),
    }
    return suggestions


def _item(value: Any, source: str, confidence: str, reason: str) -> Dict[str, Any]:
    return {
        "value": value,
        "source": source,
        "confidence": confidence,
        "reason": reason,
    }


def _float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _positive(value: Any) -> Optional[float]:
    number = _float(value)
    return number if number > 0 else None


def _explicit_cr(profile: Dict[str, Any], *keys: str) -> Optional[float]:
    for key in keys:
        value = _positive(profile.get(key))
        if value is not None:
            return round(value, 2)
    return None


def _stage(profile: Dict[str, Any]) -> str:
    return str(profile.get("funding_stage") or profile.get("stage") or "Seed")


def _team_size(profile: Dict[str, Any]) -> int:
    return max(1, int(_float(profile.get("team_size") or profile.get("headcount_total"), 10)))


def _bounded(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _has_any(items: Iterable[str], *needles: str) -> bool:
    item_set = set(items or [])
    return any(needle in item_set for needle in needles)


def _revenue(profile: Dict[str, Any], stage: str, team: int, sector: str) -> tuple[float, str, str]:
    explicit = _explicit_cr(profile, "annual_revenue_cr", "revenue_cr")
    if explicit is not None:
        return explicit, "profile", "high"
    stage_base = {"Pre-seed": 0.75, "Seed": 3.0, "Series A": 20.0, "Series B+": 100.0}.get(stage, 3.0)
    sector_mult = {
        "Fintech": 1.15,
        "SaaS / Enterprise Software": 1.10,
        "Logistics / Mobility": 1.25,
        "D2C / Consumer Brands": 1.20,
        "Foodtech / Cloud Kitchen": 1.10,
        "Healthtech": 0.85,
        "Deeptech / AI / Robotics": 0.70,
    }.get(sector, 1.0)
    return round(stage_base * max(1.0, team / 50.0) * sector_mult, 2), "deterministic_estimate", "medium"


def _property_si(profile: Dict[str, Any], stage: str, assets: Iterable[str]) -> float:
    explicit = _explicit_cr(profile, "property_sum_insured_cr", "total_insurable_asset_value_cr")
    if explicit is not None:
        return explicit
    stage_base = {"Pre-seed": 0.50, "Seed": 1.50, "Series A": 6.00, "Series B+": 20.00}.get(stage, 1.50)
    adders = {
        "Office / coworking space": 0.50,
        "Warehouse / fulfilment centre": 2.00,
        "Manufacturing plant / factory": 8.00,
        "Lab / R&D equipment": 3.00,
        "Medical devices / diagnostic equipment": 3.00,
        "Vehicles / delivery fleet": 1.00,
        "Drones / UAV equipment": 1.00,
        "Kitchen / food processing": 1.50,
        "Cold chain / refrigeration": 2.00,
        "Solar / clean energy infrastructure": 6.00,
        "Retail stores / kiosks": 1.00,
        "Data centre / server room": 2.50,
    }
    inferred = stage_base + sum(adders.get(asset, 0.0) for asset in assets or [])
    if not assets or "None - fully cloud" in set(assets or []):
        inferred = min(inferred, 1.0)
    return round(max(0.25, inferred), 2)


def _equipment_si(profile: Dict[str, Any], property_si: float, assets: Iterable[str]) -> float:
    explicit = _explicit_cr(profile, "equipment_sum_insured_cr")
    if explicit is not None:
        return explicit
    heavy_assets = _has_any(
        assets,
        "Manufacturing plant / factory",
        "Lab / R&D equipment",
        "Solar / clean energy infrastructure",
        "Data centre / server room",
        "Medical devices / diagnostic equipment",
    )
    return round(max(0.10, property_si * (0.45 if heavy_assets else 0.18)), 2)


def _payroll_proxy(profile: Dict[str, Any], stage: str, sector: str, team: int) -> float:
    explicit = _explicit_cr(profile, "payroll_cr")
    if explicit is not None:
        return explicit
    salary_lakh = {"Pre-seed": 10.0, "Seed": 14.0, "Series A": 18.0, "Series B+": 24.0}.get(stage, 14.0)
    salary_lakh *= {
        "Fintech": 1.20,
        "SaaS / Enterprise Software": 1.15,
        "Deeptech / AI / Robotics": 1.30,
        "Healthtech": 1.00,
        "Logistics / Mobility": 0.75,
        "D2C / Consumer Brands": 0.80,
        "Foodtech / Cloud Kitchen": 0.70,
    }.get(sector, 1.0)
    return round(max(0.25, team * salary_lakh / 100.0), 2)


def _data_records_proxy(
    profile: Dict[str, Any],
    revenue: float,
    team: int,
    sector: str,
    data: Iterable[str],
    data_sensitivity: str,
) -> float:
    explicit = _explicit_cr(profile, "data_records_lakhs")
    if explicit is not None:
        return explicit
    base = max(0.5, revenue * 0.30 + team * 0.015)
    if sector in ("Fintech", "Healthtech"):
        base *= 1.8
    if sector in ("D2C / Consumer Brands", "Gaming / Media / Content", "Edtech"):
        base *= 1.4
    if data_sensitivity == "High":
        base *= 1.5
    if _has_any(data, "Payments / financial transactions", "Health / medical records", "Personal identity data (KYC / Aadhaar)"):
        base *= 1.35
    return round(min(max(base, 0.25), 500.0), 2)


def _cyber_limit(profile: Dict[str, Any], stage: str, sector: str, data_sensitivity: str, revenue: float) -> float:
    explicit = _explicit_cr(profile, "cyber_limit_cr")
    if explicit is not None:
        return explicit
    base = {"Pre-seed": 1.0, "Seed": 2.0, "Series A": 5.0, "Series B+": 20.0}.get(stage, 2.0)
    if data_sensitivity == "High":
        base *= 1.5
    if sector in ("Fintech", "Healthtech"):
        base *= 1.3
    # Scale with revenue but cap at 50 Cr — Indian cyber market max for startup segment
    scaled = max(base, min(revenue * 0.12, 50.0))
    return round(scaled, 2)


def _dno_limit(profile: Dict[str, Any], stage: str, revenue: float) -> float:
    explicit = _explicit_cr(profile, "dno_limit_cr")
    if explicit is not None:
        return explicit
    base = {"Pre-seed": 1.0, "Seed": 2.0, "Series A": 5.0, "Series B+": 25.0}.get(stage, 2.0)
    if profile.get("has_investors") == "Yes":
        base *= 1.2
    # Cap at 30 Cr — Indian D&O market limit for pre-IPO startups
    scaled = max(base, min(revenue * 0.10, 30.0))
    return round(scaled, 2)


def _pi_limit(profile: Dict[str, Any], stage: str, sector: str, revenue: float, b2b_pct: float) -> float:
    explicit = _explicit_cr(profile, "pi_limit_cr", "professional_indemnity_limit_cr")
    if explicit is not None:
        return explicit
    base = {"Pre-seed": 1.0, "Seed": 2.0, "Series A": 5.0, "Series B+": 15.0}.get(stage, 2.0)
    if sector in ("Fintech", "Healthtech", "SaaS / Enterprise Software"):
        base *= 1.25
    base *= 1.0 + b2b_pct * 0.25
    # Cap at 25 Cr — standard Indian PI/Tech E&O market ceiling for startups
    scaled = max(base, min(revenue * 0.12, 25.0))
    return round(scaled, 2)


def _product_liability_limit(profile: Dict[str, Any], sector: str, revenue: float, assets: Iterable[str], data: Iterable[str]) -> float:
    explicit = _explicit_cr(profile, "product_liability_limit_cr")
    if explicit is not None:
        return explicit
    product_exposed = (
        profile.get("product_recall_exposure")
        or profile.get("food_or_pharma_manufacturing")
        or sector in ("D2C / Consumer Brands", "Foodtech / Cloud Kitchen", "Healthtech")
        or _has_any(assets, "Manufacturing plant / factory", "Medical devices / diagnostic equipment", "Kitchen / food processing")
        or "Physical inventory / goods" in set(data or [])
    )
    multiplier = 0.22 if product_exposed else 0.08
    return round(max(1.0, revenue * multiplier), 2)
