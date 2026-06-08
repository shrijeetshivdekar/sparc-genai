from __future__ import annotations

import json
import math
import os
import re
import zipfile
import csv
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from statistics import mean
from typing import Any, Dict, Iterable, List, Optional, Tuple
from xml.etree import ElementTree as ET


DEFAULT_BOOK_PATH = Path(r"C:\Users\shrij\Downloads\Book5.xlsx")
DEFAULT_DICTIONARY_PATH = Path(r"C:\Users\shrij\Downloads\E.LIABILITY Data Dictionary FY2024-25 (1).xlsx")

NS_MAIN = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
NS_REL = {"r": "http://schemas.openxmlformats.org/package/2006/relationships"}

_CACHE: Dict[Tuple[str, float, str, float], dict] = {}


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).replace("\xa0", " ").strip()
    return re.sub(r"\s+", " ", text)


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", _clean_text(value).lower()).strip("_")


def _col_to_index(ref: str) -> int:
    letters = "".join(ch for ch in ref if ch.isalpha()).upper()
    out = 0
    for ch in letters:
        out = out * 26 + (ord(ch) - 64)
    return max(out - 1, 0)


def _parse_shared_string(si: ET.Element) -> str:
    direct = si.find("a:t", NS_MAIN)
    if direct is not None and direct.text:
        return direct.text
    parts = [node.text or "" for node in si.findall(".//a:r/a:t", NS_MAIN)]
    return "".join(parts)


def _xlsx_sheets(path: Path) -> List[dict]:
    with zipfile.ZipFile(path) as zf:
        shared_strings: List[str] = []
        if "xl/sharedStrings.xml" in zf.namelist():
            shared_root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            shared_strings = [_parse_shared_string(si) for si in shared_root.findall("a:si", NS_MAIN)]

        workbook_root = ET.fromstring(zf.read("xl/workbook.xml"))
        rel_root = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
        rel_map = {
            rel.attrib.get("Id"): rel.attrib.get("Target", "")
            for rel in rel_root.findall("r:Relationship", NS_REL)
        }

        out: List[dict] = []
        for sheet in workbook_root.findall("a:sheets/a:sheet", NS_MAIN):
            rid = sheet.attrib.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
            target = rel_map.get(rid, "")
            if not target:
                continue
            target = target.lstrip("/")
            if not target.startswith("xl/"):
                target = f"xl/{target}"
            if target not in zf.namelist():
                continue
            sheet_root = ET.fromstring(zf.read(target))
            rows: List[List[str]] = []
            max_cols = 0
            for row in sheet_root.findall("a:sheetData/a:row", NS_MAIN):
                cells: Dict[int, str] = {}
                for cell in row.findall("a:c", NS_MAIN):
                    ref = cell.attrib.get("r", "")
                    idx = _col_to_index(ref)
                    value = ""
                    cell_type = cell.attrib.get("t")
                    if cell_type == "s":
                        v = cell.find("a:v", NS_MAIN)
                        if v is not None and v.text and v.text.isdigit():
                            sidx = int(v.text)
                            if 0 <= sidx < len(shared_strings):
                                value = shared_strings[sidx]
                    elif cell_type == "inlineStr":
                        value = "".join((node.text or "") for node in cell.findall(".//a:t", NS_MAIN))
                    else:
                        v = cell.find("a:v", NS_MAIN)
                        if v is not None and v.text is not None:
                            value = v.text
                    cells[idx] = _clean_text(value)
                    max_cols = max(max_cols, idx + 1)
                if not cells:
                    rows.append([])
                    continue
                row_values = [""] * max_cols
                for idx, value in cells.items():
                    if idx >= len(row_values):
                        row_values.extend([""] * (idx + 1 - len(row_values)))
                    row_values[idx] = value
                rows.append(row_values)
            out.append({"name": sheet.attrib.get("name", "Sheet"), "rows": rows})
        return out


def _csv_sheet(path: Path) -> List[dict]:
    encodings = ("utf-8-sig", "utf-8", "cp1252", "latin-1")
    last_exc = None
    for encoding in encodings:
        try:
            with path.open("r", encoding=encoding, newline="") as fh:
                reader = csv.reader(fh)
                rows = [[_clean_text(cell) for cell in row] for row in reader]
            return [{"name": path.stem, "rows": rows}]
        except Exception as exc:
            last_exc = exc
    raise last_exc or ValueError(f"Could not read CSV file: {path}")


def _load_tabular_sheets(path: Path) -> List[dict]:
    if path.suffix.lower() == ".csv":
        return _csv_sheet(path)
    return _xlsx_sheets(path)


def _detect_header_row(rows: List[List[str]], limit: int = 12) -> int:
    best_idx = 0
    best_score = -1
    for idx, row in enumerate(rows[:limit]):
        non_empty = [_clean_text(cell) for cell in row if _clean_text(cell)]
        if not non_empty:
            continue
        uniq = len(set(non_empty))
        textish = sum(1 for cell in non_empty if not re.fullmatch(r"[-+]?\d+(\.\d+)?", cell))
        score = len(non_empty) * 3 + uniq + textish
        if score > best_score:
            best_score = score
            best_idx = idx
    return best_idx


def _sheet_records(sheet: dict) -> Tuple[List[str], List[dict], int]:
    rows = sheet.get("rows") or []
    if not rows:
        return [], [], 0
    header_idx = _detect_header_row(rows)
    headers = [_clean_text(cell) or f"Column_{i+1}" for i, cell in enumerate(rows[header_idx])]
    records = []
    for row in rows[header_idx + 1 :]:
        if not any(_clean_text(cell) for cell in row):
            continue
        record = {}
        for i, header in enumerate(headers):
            record[header] = _clean_text(row[i]) if i < len(row) else ""
        records.append(record)
    return headers, records, header_idx


def _parse_date(value: str) -> Optional[datetime]:
    text = _clean_text(value)
    if not text:
        return None
    for fmt in ("%d-%b-%Y", "%d-%b-%Y %H:%M:%S", "%d-%b-%y", "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def _parse_float(value: str) -> Optional[float]:
    text = _clean_text(value)
    if not text:
        return None
    text = text.replace(",", "")
    if text.upper() in {"NA", "N/A", "NULL"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _fmt_inr(value: Optional[float]) -> str:
    if value is None:
        return "Not available"
    abs_value = abs(value)
    sign = "-" if value < 0 else ""
    if abs_value >= 10_000_000:
        return f"{sign}₹ {abs_value / 10_000_000:.2f} Cr"
    if abs_value >= 100_000:
        return f"{sign}₹ {abs_value / 100_000:.2f} L"
    return f"{sign}₹ {abs_value:,.0f}"


def _fmt_pct(value: Optional[float]) -> str:
    if value is None:
        return "Not available"
    return f"{value:.1f}%"


def _policy_display_name(record: dict) -> str:
    for key in ("Risk_Location_Building_Name", "Risk_Location_Address_Line1", "Policy_Number"):
        val = _clean_text(record.get(key))
        if val and val != "System.Xml.XmlElement":
            return val[:88]
    return "Unnamed risk location"


def _infer_book_type(record: dict) -> str:
    endt = _clean_text(record.get("Boo_Endorsement"))
    reason = _clean_text(record.get("Endt_Reason_Description"))
    if endt == "Y" or reason:
        return "Endorsement book"
    return "Policy book"


def _cross_sell_products(record: dict) -> List[str]:
    products: List[str] = []
    occ = _clean_text(record.get("Occupancy_Description")).lower()
    state = _clean_text(record.get("Risk_Location_State")).lower()
    policy_si = _parse_float(record.get("Policy_SI", "")) or 0
    locations = int((_parse_float(record.get("Number_of_Locations", "")) or 0))
    if "data processing" in occ or "call center" in occ or "business pro" in occ:
        products.extend(["Cyber", "D&O", "Crime / Fidelity"])
    if "hazardous" in occ:
        products.extend(["Public Liability", "Business Interruption", "Burglary"])
    elif "storage" in occ or "shops" in occ or "dwellings" in occ or "amusement" in occ:
        products.extend(["Burglary", "Public Liability"])
    if policy_si >= 20_000_000:
        products.append("Business Interruption")
    if locations > 1:
        products.append("Group Safeguard Insurance Policy")
    if state in {"maharashtra", "karnataka", "gujarat"} and "Cyber" not in products and "data processing" not in occ:
        products.append("Crime / Fidelity")
    deduped = []
    seen = set()
    for item in products:
        if item not in seen:
            deduped.append(item)
            seen.add(item)
    return deduped[:4]


def _cross_sell_value(record: dict, suggestions: List[str]) -> float:
    base = max((_parse_float(record.get("Policy_Premium", "")) or 0.0), 0.0)
    if not suggestions:
        return 0.0
    if "Cyber" in suggestions and "D&O" in suggestions:
        return max(base * 0.45, 60_000.0)
    if "Business Interruption" in suggestions:
        return max(base * 0.28, 40_000.0)
    return max(base * 0.18, 20_000.0)


def _classify_action(record: dict, as_of: datetime) -> dict:
    premium = _parse_float(record.get("Policy_Premium", "")) or 0.0
    policy_si = _parse_float(record.get("Policy_SI", "")) or 0.0
    pml = _parse_float(record.get("PML_Amount", "")) or 0.0
    end_date = _parse_date(record.get("Policy_End_Date", ""))
    days_to_renewal = (end_date - as_of).days if end_date else None
    occ = _clean_text(record.get("Occupancy_Description")).lower()
    cancellation = "cancel" in _clean_text(record.get("Endt_Reason_Description")).lower() or premium < 0
    hazardous = "hazardous" in occ
    high_sum_insured = policy_si >= 20_000_000 or pml >= 20_000_000
    upcoming = days_to_renewal is not None and 0 <= days_to_renewal <= 90
    near = days_to_renewal is not None and 0 <= days_to_renewal <= 45
    large_premium = premium >= 50_000
    suggestions = _cross_sell_products(record)

    if cancellation:
        return {
            "label": "Refer to underwriting",
            "priority": 100,
            "rationale": "Cancellation or negative premium endorsement requires immediate book review.",
            "tone": "critical",
            "cross_sell": suggestions,
        }
    if hazardous and upcoming:
        return {
            "label": "Increase premium",
            "priority": 92,
            "rationale": "Hazardous occupancy with a near-term renewal should be repriced and reviewed.",
            "tone": "high",
            "cross_sell": suggestions or ["Public Liability", "Business Interruption"],
        }
    if hazardous or high_sum_insured:
        return {
            "label": "Monitor closely",
            "priority": 82,
            "rationale": "Large or hazardous risk needs underwriting discipline and bundle review.",
            "tone": "warning",
            "cross_sell": suggestions,
        }
    if near and large_premium:
        return {
            "label": "Renew confidently",
            "priority": 78,
            "rationale": "High-value renewal is approaching; engage early to secure retention.",
            "tone": "positive",
            "cross_sell": suggestions,
        }
    if upcoming and suggestions:
        return {
            "label": "Cross-sell bundle",
            "priority": 74,
            "rationale": "Upcoming renewal is the cleanest point to attach adjacent covers.",
            "tone": "accent",
            "cross_sell": suggestions,
        }
    if suggestions:
        return {
            "label": "Cross-sell bundle",
            "priority": 60,
            "rationale": "Profile signals adjacent cover gaps even without claims leakage data.",
            "tone": "accent",
            "cross_sell": suggestions,
        }
    return {
        "label": "Monitor closely",
        "priority": 40,
        "rationale": "Base property book data is available, but claims performance is missing.",
        "tone": "neutral",
        "cross_sell": suggestions,
    }


def _policy_rows(records: List[dict], as_of: datetime) -> List[dict]:
    rows = []
    for record in records:
        premium = _parse_float(record.get("Policy_Premium", "")) or 0.0
        end_date = _parse_date(record.get("Policy_End_Date", ""))
        start_date = _parse_date(record.get("Policy_Start_Date", ""))
        action = _classify_action(record, as_of)
        cross_sell = action.get("cross_sell") or []
        rows.append(
            {
                "account_name": _policy_display_name(record),
                "policy_number": _clean_text(record.get("Policy_Number")),
                "product": _clean_text(record.get("Name_of_the_Product")) or "Unknown product",
                "book_type": _infer_book_type(record),
                "premium": premium,
                "sum_insured": _parse_float(record.get("Policy_SI", "")) or 0.0,
                "pml_amount": _parse_float(record.get("PML_Amount", "")) or 0.0,
                "start_date": start_date.strftime("%Y-%m-%d") if start_date else None,
                "end_date": end_date.strftime("%Y-%m-%d") if end_date else None,
                "days_to_renewal": (end_date - as_of).days if end_date else None,
                "state": _clean_text(record.get("Risk_Location_State")) or "Unknown",
                "district": _clean_text(record.get("Risk_Location_District")) or "Unknown",
                "pincode": _clean_text(record.get("Risk_Location_Pincode")),
                "industry_code": _clean_text(record.get("Industry_code")),
                "occupancy": _clean_text(record.get("Occupancy_Description")) or "Unknown occupancy",
                "locations": int((_parse_float(record.get("Number_of_Locations", "")) or 0)),
                "voluntary_deductible": _clean_text(record.get("Voluntary_Deductible_Opted")),
                "endorsement_reason": _clean_text(record.get("Endt_Reason_Description")),
                "action": action["label"],
                "priority": action["priority"],
                "tone": action["tone"],
                "rationale": action["rationale"],
                "cross_sell": cross_sell,
                "cross_sell_value": _cross_sell_value(record, cross_sell),
            }
        )
    rows.sort(key=lambda item: (-item["priority"], -abs(item["premium"]), item["account_name"]))
    return rows


def _exact_vs_inferred(records: List[dict]) -> dict:
    headers = set()
    for record in records[:3]:
        headers.update(record.keys())
    exact = [
        "Total premium",
        "Policy count",
        "Renewal dates",
        "Geography mix",
        "Product mix",
        "Occupancy / industry descriptors",
        "Sum insured and PML",
        "Endorsement signals",
    ]
    inferred = [
        "RM action priorities",
        "Cross-sell opportunities",
        "Potential premium upside",
        "Book type segmentation",
    ]
    unavailable = [
        "Loss ratio",
        "Incurred loss ratio",
        "Claim frequency",
        "Average claim severity",
        "Combined ratio",
        "Claims leakage and litigation",
    ]
    if "Claim_Number" in headers or "Incurred_Amount" in headers:
        unavailable = [item for item in unavailable if item not in {"Loss ratio", "Claim frequency"}]
    return {"exact": exact, "inferred": inferred, "unavailable": unavailable}


def _parse_dictionary(path: Path) -> dict:
    sheets = _xlsx_sheets(path)
    summary = {"workbook": path.name, "sheets": [], "policy_fields": [], "claims_fields": []}
    for sheet in sheets:
        headers, records, header_idx = _sheet_records(sheet)
        field_rows = []
        for record in records[:250]:
            field_name = _clean_text(record.get("Field Name") or record.get("Field_Name") or record.get("Field name"))
            if not field_name:
                continue
            field_rows.append(
                {
                    "field_name": field_name,
                    "type": _clean_text(record.get("Type")),
                    "mandatory": _clean_text(record.get("Mandatory(m)/Nonmandatory(n)") or record.get("Mandatory(m)/ Nonmandatory(n)")),
                    "description": _clean_text(record.get("Description")),
                }
            )
        summary["sheets"].append(
            {
                "name": sheet["name"],
                "header_row": header_idx + 1,
                "field_count": len(field_rows),
                "sample_fields": field_rows[:8],
            }
        )
        lower = sheet["name"].lower()
        if lower == "policy":
            summary["policy_fields"] = field_rows
        elif lower == "claims":
            summary["claims_fields"] = field_rows
    return summary


def _rollup_products(rows: List[dict]) -> List[dict]:
    grouped: Dict[str, List[dict]] = defaultdict(list)
    for row in rows:
        grouped[row["product"]].append(row)
    out = []
    for product, items in grouped.items():
        premiums = [item["premium"] for item in items]
        cross_sell = sum(item["cross_sell_value"] for item in items)
        due_90 = sum(1 for item in items if item["days_to_renewal"] is not None and 0 <= item["days_to_renewal"] <= 90)
        out.append(
            {
                "product": product,
                "policy_count": len(items),
                "premium": sum(premiums),
                "avg_premium": mean(premiums) if premiums else 0,
                "renewals_90d": due_90,
                "cross_sell_potential": cross_sell,
                "loss_ratio": None,
                "status": "Claims data needed",
            }
        )
    return sorted(out, key=lambda item: item["premium"], reverse=True)


def _rollup_geography(rows: List[dict]) -> List[dict]:
    grouped: Dict[str, List[dict]] = defaultdict(list)
    for row in rows:
        grouped[row["state"]].append(row)
    out = []
    for state, items in grouped.items():
        out.append(
            {
                "state": state,
                "policy_count": len(items),
                "premium": sum(item["premium"] for item in items),
                "renewals_90d": sum(1 for item in items if item["days_to_renewal"] is not None and 0 <= item["days_to_renewal"] <= 90),
                "cross_sell_potential": sum(item["cross_sell_value"] for item in items),
            }
        )
    return sorted(out, key=lambda item: item["premium"], reverse=True)


def _rollup_occupancy(rows: List[dict]) -> List[dict]:
    grouped: Dict[str, List[dict]] = defaultdict(list)
    for row in rows:
        grouped[row["occupancy"]].append(row)
    out = []
    for name, items in grouped.items():
        out.append(
            {
                "occupancy": name,
                "policy_count": len(items),
                "premium": sum(item["premium"] for item in items),
                "high_priority": sum(1 for item in items if item["priority"] >= 80),
            }
        )
    return sorted(out, key=lambda item: item["premium"], reverse=True)[:8]


def _renewal_table(rows: List[dict]) -> List[dict]:
    renewals = [row for row in rows if row["days_to_renewal"] is not None and row["days_to_renewal"] >= 0]
    renewals.sort(key=lambda item: (item["days_to_renewal"], -item["premium"]))
    return renewals[:12]


def _focus_strip(rows: List[dict]) -> List[dict]:
    renewals = [row for row in rows if row["days_to_renewal"] is not None and 0 <= row["days_to_renewal"] <= 90]
    high_premium_renewals = [row for row in renewals if row["premium"] >= 20_000]
    uw = [row for row in rows if row["action"] == "Refer to underwriting"]
    cross_sell = [row for row in rows if row["cross_sell"]]
    multi_loc = [row for row in rows if row["locations"] > 1]
    high_si = [row for row in rows if row["sum_insured"] >= 20_000_000]
    return [
        {
            "rank": 1,
            "title": f"Renew {len(high_premium_renewals)} high-value accounts",
            "metric": _fmt_inr(sum(row["premium"] for row in high_premium_renewals)),
            "detail": "Premium exposed in the next 90 days.",
            "tone": "blue",
        },
        {
            "rank": 2,
            "title": f"Escalate {len(uw)} accounts to underwriting",
            "metric": _fmt_inr(sum(abs(row["premium"]) for row in uw)),
            "detail": "Cancellation, negative premium, or term correction signal.",
            "tone": "red",
        },
        {
            "rank": 3,
            "title": f"Cross-sell {len(cross_sell)} accounts",
            "metric": _fmt_inr(sum(row["cross_sell_value"] for row in cross_sell)),
            "detail": "Indicative adjacent-cover opportunity inferred from occupancy and scale.",
            "tone": "amber",
        },
        {
            "rank": 4,
            "title": f"Review {len(high_si)} large SI risks",
            "metric": _fmt_inr(sum(row["sum_insured"] for row in high_si)),
            "detail": "High sum-insured property risks may need tighter structuring.",
            "tone": "slate",
        },
        {
            "rank": 5,
            "title": f"Monitor {len(multi_loc)} multi-location risks",
            "metric": _fmt_inr(sum(row["premium"] for row in multi_loc)),
            "detail": "Broader footprint can justify bundle expansion and service attention.",
            "tone": "green",
        },
    ]


def _kpis(rows: List[dict], as_of: datetime) -> List[dict]:
    net_premium = sum(row["premium"] for row in rows)
    active_rows = [row for row in rows if row["premium"] > 0]
    renewals_90 = [row for row in rows if row["days_to_renewal"] is not None and 0 <= row["days_to_renewal"] <= 90]
    cross_sell = [row for row in rows if row["cross_sell"]]
    escalations = [row for row in rows if row["action"] == "Refer to underwriting"]
    return [
        {
            "label": "Net Written Premium",
            "value": _fmt_inr(net_premium),
            "subtext": f"{len(rows)} policies in sample workbook",
            "note": "Exact from Policy_Premium.",
            "tone": "neutral",
        },
        {
            "label": "Renewals Next 90 Days",
            "value": str(len(renewals_90)),
            "subtext": _fmt_inr(sum(row["premium"] for row in renewals_90)),
            "note": f"Window anchored to sample as-of {as_of.strftime('%d %b %Y')}.",
            "tone": "blue",
        },
        {
            "label": "Accounts to Escalate",
            "value": str(len(escalations)),
            "subtext": _fmt_inr(sum(abs(row["premium"]) for row in escalations)),
            "note": "Rule-driven from cancellation / adverse endorsement markers.",
            "tone": "red",
        },
        {
            "label": "Cross-sell Opportunities",
            "value": str(len(cross_sell)),
            "subtext": _fmt_inr(sum(row["cross_sell_value"] for row in cross_sell)),
            "note": "Indicative potential, inferred from occupancy and scale.",
            "tone": "amber",
        },
        {
            "label": "Overall Loss Ratio",
            "value": "Not available",
            "subtext": "Claims dataset missing",
            "note": "Needs claims-level incurred data from IIB / liability claims table.",
            "tone": "muted",
        },
        {
            "label": "Claim Frequency",
            "value": "Not available",
            "subtext": "Claims dataset missing",
            "note": "Cannot derive without claim rows or claim counts.",
            "tone": "muted",
        },
    ]


def _insight_banner(rows: List[dict], as_of: datetime) -> str:
    renewals = [row for row in rows if row["days_to_renewal"] is not None and 0 <= row["days_to_renewal"] <= 90]
    cross_sell = [row for row in rows if row["cross_sell"]]
    escalations = [row for row in rows if row["action"] == "Refer to underwriting"]
    top_state = _rollup_geography(rows)[:1]
    top_state_text = f" {top_state[0]['state']} carries the biggest premium concentration." if top_state else ""
    return (
        f"This sample book is currently strongest as a renewal and portfolio-shaping dashboard rather than a claims profitability view. "
        f"{len(renewals)} renewals fall inside the next 90 days, {len(cross_sell)} accounts show adjacent-cover potential worth "
        f"{_fmt_inr(sum(row['cross_sell_value'] for row in cross_sell))}, and {len(escalations)} accounts need underwriting attention based on endorsement signals."
        f"{top_state_text}"
    )


def _footer_actions(rows: List[dict]) -> List[dict]:
    renewals = [row for row in rows if row["days_to_renewal"] is not None and 0 <= row["days_to_renewal"] <= 90]
    cross_sell = [row for row in rows if row["cross_sell"]]
    escalations = [row for row in rows if row["action"] == "Refer to underwriting"]
    storage = [row for row in rows if "storage" in row["occupancy"].lower() or "hazardous" in row["occupancy"].lower()]
    data_ops = [row for row in rows if "data processing" in row["occupancy"].lower() or "call center" in row["occupancy"].lower()]
    return [
        {
            "title": "Lock in near-term renewals",
            "impact": _fmt_inr(sum(row["premium"] for row in renewals)),
            "detail": f"Engage the {len(renewals)} accounts expiring inside 90 days before they drift to market.",
        },
        {
            "title": "Escalate cancellations and adverse endorsements",
            "impact": _fmt_inr(sum(abs(row["premium"]) for row in escalations)),
            "detail": f"{len(escalations)} accounts show cancellation or corrective endorsement signals.",
        },
        {
            "title": "Pitch adjacent covers on storage / hazardous occupancies",
            "impact": _fmt_inr(sum(row["cross_sell_value"] for row in storage)),
            "detail": "Lead with liability, burglary, and business interruption extensions.",
        },
        {
            "title": "Convert data-processing risks into cyber conversations",
            "impact": _fmt_inr(sum(row["cross_sell_value"] for row in data_ops)),
            "detail": "Use cyber, D&O, and crime protection where the occupancy hints at digital operations.",
        },
        {
            "title": "Bundle multi-location accounts earlier",
            "impact": _fmt_inr(sum(row["premium"] for row in rows if row["locations"] > 1)),
            "detail": "Multi-location risks justify broader service and people cover discussions.",
        },
    ]


def _workbook_summary(path: Path, sheets: List[dict], headers: List[str], records: List[dict], header_idx: int) -> dict:
    return {
        "workbook": path.name,
        "sheet_count": len(sheets),
        "sheet_names": [sheet["name"] for sheet in sheets],
        "active_sheet": sheets[0]["name"] if sheets else None,
        "header_row": header_idx + 1,
        "row_count": len(records),
        "column_count": len(headers),
        "headers": headers,
        "dimensions": [
            item
            for item in [
                "Policy_Number" if "Policy_Number" in headers else None,
                "Policy_Start_Date" if "Policy_Start_Date" in headers else None,
                "Policy_End_Date" if "Policy_End_Date" in headers else None,
                "Name_of_the_Product" if "Name_of_the_Product" in headers else None,
                "Risk_Location_State" if "Risk_Location_State" in headers else None,
                "Risk_Location_District" if "Risk_Location_District" in headers else None,
                "Occupancy_Description" if "Occupancy_Description" in headers else None,
            ]
            if item
        ],
        "measures": [
            item
            for item in [
                "Policy_Premium" if "Policy_Premium" in headers else None,
                "Policy_SI" if "Policy_SI" in headers else None,
                "PML_Amount" if "PML_Amount" in headers else None,
                "Premium_FLEXA" if "Premium_FLEXA" in headers else None,
                "Premium_STFI" if "Premium_STFI" in headers else None,
            ]
            if item
        ],
    }


def load_dashboard(book_path: Optional[str] = None, dictionary_path: Optional[str] = None) -> dict:
    book = Path(book_path or DEFAULT_BOOK_PATH)
    dictionary = Path(dictionary_path or DEFAULT_DICTIONARY_PATH)
    if not book.exists():
        raise FileNotFoundError(f"Sample workbook not found: {book}")
    if not dictionary.exists():
        raise FileNotFoundError(f"Dictionary workbook not found: {dictionary}")

    cache_key = (str(book), book.stat().st_mtime, str(dictionary), dictionary.stat().st_mtime)
    if cache_key in _CACHE:
        return _CACHE[cache_key]

    sample_sheets = _load_tabular_sheets(book)
    if not sample_sheets:
        raise ValueError(f"No readable sheets found in {book}")
    headers, records, header_idx = _sheet_records(sample_sheets[0])
    if not records:
        raise ValueError(f"No data rows found in {book}")

    all_dates = [
        dt
        for record in records
        for dt in (
            _parse_date(record.get("Transaction_Date", "")),
            _parse_date(record.get("Policy_End_Date", "")),
            _parse_date(record.get("Policy_Start_Date", "")),
        )
        if dt
    ]
    as_of = max(all_dates) if all_dates else datetime.today()
    rows = _policy_rows(records, as_of)

    payload = {
        "meta": {
            "as_of": as_of.strftime("%Y-%m-%d"),
            "book_path": str(book),
            "dictionary_path": str(dictionary),
            "book_type_default": "Full book",
            "currency": "INR",
        },
        "sample_workbook": _workbook_summary(book, sample_sheets, headers, records, header_idx),
        "dictionary_workbook": _parse_dictionary(dictionary),
        "readiness": _exact_vs_inferred(records),
        "insight_banner": _insight_banner(rows, as_of),
        "focus_strip": _focus_strip(rows),
        "kpis": _kpis(rows, as_of),
        "accounts": rows,
        "accounts_top": rows[:18],
        "renewals": _renewal_table(rows),
        "products": _rollup_products(rows),
        "geography": _rollup_geography(rows),
        "occupancy_mix": _rollup_occupancy(rows),
        "claims_section": {
            "available": False,
            "message": "Claims leakage, loss ratio, case reserve, IBNR, and severity metrics need claim rows. The current sample workbook is policy-book heavy; the liability dictionary indicates that a future claims table can be mapped in once claim extracts are available.",
        },
        "cross_sell": [
            {
                "account_name": row["account_name"],
                "policy_number": row["policy_number"],
                "product": row["product"],
                "state": row["state"],
                "recommendations": row["cross_sell"],
                "potential": row["cross_sell_value"],
                "why": row["rationale"],
            }
            for row in rows
            if row["cross_sell"]
        ][:12],
        "footer_actions": _footer_actions(rows),
        "metrics_meta": {
            "exact_metrics": _exact_vs_inferred(records)["exact"],
            "inferred_metrics": _exact_vs_inferred(records)["inferred"],
            "unavailable_metrics": _exact_vs_inferred(records)["unavailable"],
        },
    }
    _CACHE[cache_key] = payload
    return payload
