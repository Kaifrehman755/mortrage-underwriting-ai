"""Data cleaning and normalization pipeline for property appraisal records.

Implements Playbook Section 14.3, 14.5 (Clean and process pipeline for India/Lucknow pilot),
and Section 19.3 (Fingerprints and quality gates).
"""

import logging
import math
import re
from datetime import date, datetime
from typing import Any

from app.property.jurisdictions import JurisdictionPack

logger = logging.getLogger(__name__)

MULT_INR = {
    "cr": 1e7,
    "crore": 1e7,
    "l": 1e5,
    "lac": 1e5,
    "lakh": 1e5,
    "k": 1e3,
}

AREA_CONVERSIONS = {
    "sqft": 1.0,
    "sq.ft": 1.0,
    "sq ft": 1.0,
    "sqm": 10.7639,
    "sq.m": 10.7639,
    "sq m": 10.7639,
    "sqyd": 9.0,
    "sq.yd": 9.0,
    "sq yd": 9.0,
    "gaj": 9.0,
}

# Protected-class proxy terms strictly forbidden in valuation features (Invariant 5)
PROTECTED_CLASS_TERMS = {
    "caste", "brahmin", "dalit", "thakur", "yadav", "muslim", "hindu", "christian",
    "sikh", "jain", "colony of", "community", "basti", "mohalla", "religion",
    "ethnicity", "race", "minority"
}


def parse_price_inr(raw: Any) -> float | None:
    """Parse Indian Rupee price string into standard float INR.

    Handles '85 Lac', '1.2 Cr', '8,500,000', '₹75,00,000', '7500000'.
    Rejects <= 0.
    """
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        val = float(raw)
        return val if val > 0 else None

    s = str(raw).lower().replace(",", "").replace("₹", "").replace("rs.", "").replace("rs", "").strip()
    if "-" in s:
        return None

    match = re.search(r"([0-9]+[.]?[0-9]*)[ ]*(crore|cr|lakh|lac|l|k)?", s)
    if not match:
        return None

    try:
        base_num = float(match.group(1))
        unit = match.group(2)
        multiplier = MULT_INR.get(unit, 1.0)
        total = base_num * multiplier
        return round(total, 2) if total > 0 else None
    except (ValueError, TypeError):
        return None


def parse_area_sqft(raw: Any, default_unit: str = "sqft") -> float | None:
    """Parse raw area strings into square feet.

    Converts sq m, sq yd, gaj into sq ft based on standard multipliers.
    """
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        val = float(raw)
        return val if val > 0 else None

    s = str(raw).lower().replace(",", "").strip()
    if "-" in s:
        return None

    match = re.search(r"([0-9]+[.]?[0-9]*)[ ]*(sq[ .]*ft|sq[ .]*m|sq[ .]*yd|gaj)?", s)
    if not match:
        return None

    try:
        base_num = float(match.group(1))
        unit = match.group(2)
        if unit:
            cleaned_unit = re.sub(r"[ .]", "", unit)
            multiplier = AREA_CONVERSIONS.get(cleaned_unit, 1.0)
        else:
            multiplier = AREA_CONVERSIONS.get(default_unit, 1.0)
        sqft = base_num * multiplier
        return round(sqft, 2) if sqft > 0 else None
    except (ValueError, TypeError):
        return None


def parse_bhk(raw: Any) -> int | None:
    """Parse bedroom count from bedroom or title description (e.g., '3 BHK', '2bhk')."""
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        val = int(raw)
        return val if val > 0 else None
    s = str(raw).lower()
    match = re.search(r"([0-9]+)[ ]*bhk", s)
    if match:
        return int(match.group(1))
    return None


def parse_pincode(raw: Any) -> str | None:
    """Extract standard 6-digit Indian PIN code."""
    if not raw:
        return None
    s = str(raw).strip()
    match = re.search(r"(?<![0-9])([1-9][0-9]{5})(?![0-9])", s)
    return match.group(1) if match else None


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two coordinates in kilometers."""
    p = math.pi / 180.0
    dlat = (lat2 - lat1) * p
    dlon = (lon2 - lon1) * p
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(lat1 * p) * math.cos(lat2 * p) * (math.sin(dlon / 2.0) ** 2)
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(6371.0 * c, 3)


def check_protected_class_proxies(text: str) -> list[str]:
    """Invariant 5: Reject protected-class proxies or illegal discriminatory terms."""
    if not text:
        return []
    text_lower = text.lower()
    found: list[str] = []
    for term in PROTECTED_CLASS_TERMS:
        if re.search(rf"\b{re.escape(term)}\b", text_lower):
            found.append(term)
    return found


def clean_raw_record(
    record: dict[str, Any],
    jurisdiction: JurisdictionPack,
) -> tuple[dict[str, Any] | None, list[str]]:
    """Clean and normalize a single record with explicit rejection logging.

    Never silently fixes rows. Returns (cleaned_row, rejection_reasons).
    """
    reasons: list[str] = []

    # 1. Price validation
    price = parse_price_inr(record.get("price") or record.get("sale_price") or record.get("price_raw"))
    if price is None or price <= 0:
        reasons.append("invalid_or_missing_price")

    # 2. Area validation
    area = parse_area_sqft(record.get("area") or record.get("living_area_sqft") or record.get("area_raw"))
    if area is None or area <= 0:
        reasons.append("invalid_or_missing_area")

    # 3. Date validation
    date_val = record.get("sale_date") or record.get("date_raw")
    parsed_date_str: str | None = None
    if not date_val:
        reasons.append("missing_sale_date")
    else:
        try:
            if isinstance(date_val, datetime):
                d = date_val.date()
            elif isinstance(date_val, date):
                d = date_val
            else:
                s = str(date_val).strip()
                try:
                    d = datetime.strptime(s[:10], "%Y-%m-%d").date()
                except ValueError:
                    try:
                        d = datetime.strptime(s[:10], "%d/%m/%Y").date()
                    except ValueError:
                        d = datetime.strptime(s[:10], "%d-%m-%Y").date()
            if d > date.today():
                reasons.append(f"future_sale_date_{d.isoformat()}")
            else:
                parsed_date_str = d.isoformat()
        except (ValueError, TypeError):
            reasons.append(f"unparseable_sale_date_{date_val}")

    # 4. Geo bounding box check
    lat = float(record.get("lat") or 0.0)
    lon = float(record.get("lon") or 0.0)
    if not (jurisdiction.lat_min <= lat <= jurisdiction.lat_max and jurisdiction.lon_min <= lon <= jurisdiction.lon_max):
        reasons.append(
            f"coordinates_outside_boundary_box_{jurisdiction.state_code}_(lat={lat},lon={lon})"
        )

    # 5. Protected class check (Invariant 5)
    raw_desc = str(record.get("description") or record.get("notes") or "")
    proxies = check_protected_class_proxies(raw_desc)
    if proxies:
        reasons.append(f"contains_protected_class_proxy_{','.join(proxies)}")

    if reasons:
        return None, reasons

    # Compute price per sqft
    ppsf = round(price / area, 2)  # type: ignore

    cleaned: dict[str, Any] = {
        **record,
        "sale_price": price,
        "living_area_sqft": area,
        "sale_date": parsed_date_str,
        "lat": lat,
        "lon": lon,
        "price_per_sqft": ppsf,
        "state_code": jurisdiction.state_code,
        "clean_flags": list(record.get("clean_flags") or []),
    }
    return cleaned, []


def flag_outliers_mad(records: list[dict[str, Any]], threshold: float = 3.5) -> list[dict[str, Any]]:
    """Flag price per sqft outliers using Median Absolute Deviation (MAD).

    Playbook Section 14.5: Flag with clean_flags=['outlier'], DO NOT delete rows.
    """
    if len(records) < 4:
        return records

    ppsfs = [r["price_per_sqft"] for r in records if "price_per_sqft" in r]
    if not ppsfs:
        return records

    # Calculate median
    sorted_p = sorted(ppsfs)
    n = len(sorted_p)
    median_val = sorted_p[n // 2] if n % 2 != 0 else (sorted_p[n // 2 - 1] + sorted_p[n // 2]) / 2.0

    # Calculate MAD
    abs_devs = sorted(abs(x - median_val) for x in ppsfs)
    mad = abs_devs[n // 2] if n % 2 != 0 else (abs_devs[n // 2 - 1] + abs_devs[n // 2]) / 2.0

    if mad == 0:
        return records

    for r in records:
        score = abs(r["price_per_sqft"] - median_val) / (1.4826 * mad)
        if score > threshold:
            flags = list(r.get("clean_flags") or [])
            if "outlier" not in flags:
                flags.append("outlier")
            r["clean_flags"] = flags

    return records
