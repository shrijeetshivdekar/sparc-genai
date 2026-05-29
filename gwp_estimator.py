"""GWP estimation helper for the SPARC Commerce Layer.

Wraps the read-only ``premium_estimator`` lakh-band tables to produce an
indicative annual GWP **range** (low / high) in integer INR rupees, with
basis, data-quality, disclaimer, and per-cover breakdown. Never returns a
single-point estimate (Schema §4; PRD §6).

Public surface:
    estimate_gwp(profile, covers=None) -> dict
    estimate_delta_gwp(old_profile, new_profile, old_covers, new_covers) -> dict
"""

from __future__ import annotations

from typing import Iterable

from premium_estimator import (  # read-only consumer
    PREMIUM_RANGES,
    get_size_bucket,
)

INDICATIVE_DISCLAIMER: str = (
    "Indicative only under IRDAI File-and-Use detariffed regime. "
    "Not a bindable quote."
)

_LAKH_TO_RUPEES = 100_000


# Maps engine-facing cover names (recommendation keys + bundle cover labels)
# to the premium_estimator.PREMIUM_RANGES band keys. Lookup is normalised
# (uppercase, non-alphanumeric collapsed to '_'), so both "D&O" and
# "D_AND_O" resolve to the same entry.
_COVER_TO_BAND_KEY: dict[str, str] = {
    # Liability / management
    "CYBER":                          "cyber_liability",
    "CYBER_LIABILITY":                "cyber_liability",
    "D_O":                            "dno_liability",
    "D_AND_O":                        "dno_liability",
    "DIRECTORS_AND_OFFICERS":         "dno_liability",
    "PI":                             "professional_indemnity",
    "PI_TECH_EO":                     "professional_indemnity",
    "PROFESSIONAL_INDEMNITY":         "professional_indemnity",
    "CGL":                            "comprehensive_general_liability",
    "COMPREHENSIVE_GENERAL_LIABILITY": "comprehensive_general_liability",
    "GENERAL_LIABILITY":              "comprehensive_general_liability",
    "PUBLIC_LIABILITY":               "public_liability",
    "PRODUCT_LIABILITY":              "product_liability",
    "PRODUCT_RECALL":                 "product_recall",
    "EMPLOYMENT_PRACTICES":           "employment_practices",
    "EMPLOYMENT_PRACTICES_LIABILITY": "employment_practices",
    "EPLI":                           "employment_practices",
    "CRIME":                          "crime_fidelity",
    "CRIME_FIDELITY":                 "crime_fidelity",
    # People
    "GROUP_HEALTH":                   "employee_health",
    "EMPLOYEE_HEALTH":                "employee_health",
    "GH":                             "employee_health",
    "GROUP_PA":                       "group_pa",
    "GPA":                            "group_pa",
    "GROUP_PERSONAL_ACCIDENT":        "group_pa",
    "GROUP_CRITI_SHIELD":             "group_criti_shield",
    "GROUP_HOSPISHIELD":              "group_hospishield",
    "EMPLOYEES_COMP":                 "employees_comp",
    "EC":                             "employees_comp",
    "EMPLOYERS_LIABILITY":            "employees_comp",
    "KEY_PERSON":                     "key_person",
    "KEYMAN":                         "key_person",
    # Property / assets
    "PROPERTY_FIRE":                  "property_fire",
    "FIRE":                           "property_fire",
    "PROPERTY":                       "property_all_risk",
    "PROPERTY_ALL_RISK":              "property_all_risk",
    "BUSINESS_INTERRUPTION":          "business_interruption",
    "BI":                             "business_interruption",
    "MACHINERY_BREAKDOWN":            "machinery_breakdown",
    "MB":                             "machinery_breakdown",
    "ELECTRONIC_EQUIPMENT":           "electronic_equipment",
    "EEI":                            "electronic_equipment",
    "GADGET_EQUIPMENT":               "gadget_equipment",
    "MARINE_TRANSIT":                 "marine_transit",
    "MOTOR_FLEET":                    "motor_fleet",
    "CONTRACTORS_ALL_RISK":           "contractors_all_risk",
    "CAR":                            "contractors_all_risk",
    # Specialty
    "CLINICAL_TRIALS":                "clinical_trials",
    "HEALTHCARE_PI":                  "healthcare_pi",
    "FINANCIAL_SERVICES_PI":          "financial_services_pi",
    "PAYMENT_PROTECTION":             "payment_protection",
    "EVENT_PRODUCTION":               "event_production",
    "SURETY":                         "surety",
    "TRADE_CREDIT":                   "trade_credit",
    "MONEY_INSURANCE":                "money_insurance",
    "DRONE_INSURANCE":                "drone_insurance",
    "DRONE":                          "drone_insurance",
    # Packages
    "BUSINESS_EDGE":                  "business_edge",
    "MSME_SURAKSHA":                  "msme_suraksha",
    "ENTERPRISE_SECURE":              "enterprise_secure",
}


def _norm_cover(cover: str) -> str:
    out = []
    for ch in cover.upper():
        out.append(ch if ch.isalnum() else "_")
    # collapse runs of underscores and strip
    s = "".join(out)
    while "__" in s:
        s = s.replace("__", "_")
    return s.strip("_")


def _resolve_band_key(cover: str) -> str | None:
    return _COVER_TO_BAND_KEY.get(_norm_cover(cover))


def _bucket_for(profile: dict) -> str:
    stage = str(profile.get("funding_stage") or "").strip()
    try:
        team = int(profile.get("team_size") or 0)
    except (TypeError, ValueError):
        team = 0
    return get_size_bucket(stage, team)


def estimate_gwp(
    profile: dict,
    covers: Iterable[str] | None = None,
) -> dict:
    """Return an indicative GWP range for a profile + cover list.

    Output shape (Schema §gwp_estimates + TRD §2):
        {
          "low_inr":  int,
          "high_inr": int,
          "basis":    str,
          "data_quality": float,    # 0..1
          "disclaimer":   str,
          "per_cover":    [{"cover": str, "band_key": str|None,
                             "low_inr": int, "high_inr": int, "basis": str}]
        }
    Unknown cover names are recorded with band_key=None and zero rupees, and
    they reduce ``data_quality``. They never raise.
    """
    profile = profile or {}
    bucket = _bucket_for(profile)
    covers_list = [str(c) for c in (covers or []) if str(c).strip()]

    per_cover: list[dict] = []
    total_low = 0
    total_high = 0
    matched = 0

    for cover in covers_list:
        band_key = _resolve_band_key(cover)
        band = PREMIUM_RANGES.get(band_key, {}).get(bucket) if band_key else None
        if band is None:
            per_cover.append({
                "cover": cover,
                "band_key": band_key,
                "low_inr": 0,
                "high_inr": 0,
                "basis": "unmapped cover; excluded from total",
            })
            continue
        low = int(round(float(band["min_lakh"]) * _LAKH_TO_RUPEES))
        high = int(round(float(band["max_lakh"]) * _LAKH_TO_RUPEES))
        per_cover.append({
            "cover": cover,
            "band_key": band_key,
            "low_inr": low,
            "high_inr": high,
            "basis": str(band.get("basis", "")),
        })
        total_low += low
        total_high += high
        matched += 1

    if covers_list:
        data_quality = round(matched / len(covers_list), 3)
    else:
        data_quality = 0.0

    return {
        "low_inr": int(total_low),
        "high_inr": int(total_high),
        "basis": f"premium_estimator bands; bucket={bucket}; covers_matched={matched}/{len(covers_list)}",
        "data_quality": data_quality,
        "disclaimer": INDICATIVE_DISCLAIMER,
        "per_cover": per_cover,
    }


def estimate_delta_gwp(
    old_profile: dict,
    new_profile: dict,
    old_covers: Iterable[str] | None = None,
    new_covers: Iterable[str] | None = None,
) -> dict:
    """Range delta between two GWP estimates (new − old). Used by F4 in M5."""
    old = estimate_gwp(old_profile, old_covers)
    new = estimate_gwp(new_profile, new_covers)
    return {
        "low_inr": int(new["low_inr"] - old["low_inr"]),
        "high_inr": int(new["high_inr"] - old["high_inr"]),
        "basis": f"delta: {new['basis']} − {old['basis']}",
        "data_quality": round(min(old["data_quality"], new["data_quality"]), 3),
        "disclaimer": INDICATIVE_DISCLAIMER,
        "old": old,
        "new": new,
    }
