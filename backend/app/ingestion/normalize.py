"""Canonical Unit Conversion and Normalization Helpers.

Enforces GEMINI.md Section 5:
- Preserves raw values and units alongside normalized quantities.
- Explicit conversion factors:
  * 1 Lakh = 100,000 INR
  * 1 Crore = 10,000,000 INR
  * 1 sq.m = 10.7639104167 sqft
  * 1 sq.yd = 9.0 sqft
- Never infers units from numeric values alone.
- Preserves area types (carpet, built_up, super_built_up, plot, unknown).
"""

import math
import re
from typing import Any

from app.schemas.property import AreaType

NORMALIZATION_VERSION = "1.0.0"

SQM_TO_SQFT = 10.7639104167
SQYD_TO_SQFT = 9.0

KNOWN_AREA_UNITS = {
    "sqft": 1.0,
    "sq.ft": 1.0,
    "sq ft": 1.0,
    "square feet": 1.0,
    "square foot": 1.0,
    "sqm": SQM_TO_SQFT,
    "sq.m": SQM_TO_SQFT,
    "sq m": SQM_TO_SQFT,
    "square metre": SQM_TO_SQFT,
    "square meter": SQM_TO_SQFT,
    "sqyd": SQYD_TO_SQFT,
    "sq.yd": SQYD_TO_SQFT,
    "sq yd": SQYD_TO_SQFT,
    "square yard": SQYD_TO_SQFT,
    "gaj": SQYD_TO_SQFT,
}


def normalize_inr_price(raw_value: Any, raw_unit: str | None = None) -> float | None:
    """Normalize raw Indian price consideration or asking price to numeric INR.

    Handles explicit units like 'lakh', 'lac', 'crore', 'cr', or comma-separated Indian numbers.
    Rejects negative numbers, zero, or unparseable strings.
    """
    if raw_value is None:
        return None

    if isinstance(raw_value, (int, float)):
        val = float(raw_value)
        if math.isnan(val) or math.isinf(val) or val <= 0:
            return None
        if raw_unit:
            unit_clean = raw_unit.strip().lower()
            if unit_clean in ("crore", "cr"):
                return val * 10_000_000.0
            if unit_clean in ("lakh", "lac", "l"):
                return val * 100_000.0
            if unit_clean in ("k", "thousand"):
                return val * 1_000.0
        return val

    s = str(raw_value).lower().replace(",", "").replace("₹", "").replace("rs.", "").replace("rs", "").strip()
    if not s or s == "nan" or s == "none":
        return None

    # Check for unit keyword embedded in string
    mult = 1.0
    if "cr" in s or "crore" in s:
        mult = 10_000_000.0
        s = re.sub(r"[a-z]", "", s).strip()
    elif "lac" in s or "lakh" in s:
        mult = 100_000.0
        s = re.sub(r"[a-z]", "", s).strip()
    elif raw_unit:
        unit_clean = raw_unit.strip().lower()
        if unit_clean in ("crore", "cr"):
            mult = 10_000_000.0
        elif unit_clean in ("lakh", "lac", "l"):
            mult = 100_000.0
        elif unit_clean in ("k", "thousand"):
            mult = 1_000.0

    try:
        num = float(s)
        if math.isnan(num) or math.isinf(num) or num <= 0:
            return None
        return round(num * mult, 2)
    except ValueError:
        return None


def normalize_area_sqft(raw_value: Any, raw_unit: str | None) -> float | None:
    """Normalize area to square feet using strictly validated unit conversions.

    Rule 1: Never infer an unknown unit from the numeric value alone.
    """
    if raw_value is None or raw_unit is None:
        return None

    unit_clean = str(raw_unit).strip().lower()
    if unit_clean not in KNOWN_AREA_UNITS:
        return None

    conversion_factor = KNOWN_AREA_UNITS[unit_clean]

    if isinstance(raw_value, (int, float)):
        val = float(raw_value)
    else:
        s = str(raw_value).replace(",", "").strip()
        try:
            val = float(s)
        except ValueError:
            return None

    if math.isnan(val) or math.isinf(val) or val <= 0:
        return None

    return round(val * conversion_factor, 4)


def calculate_price_per_sqft(
    price_inr: float | None,
    area_sqft: float | None,
    subject_area_type: AreaType,
    comp_area_type: AreaType,
) -> float | None:
    """Calculate price per square foot with strict area-type compatibility check.

    Rule 2: Do not equate carpet, built-up, super built-up, and plot area.
    Rule 3: Do not calculate if price or compatible area basis is missing or invalid.
    """
    if price_inr is None or area_sqft is None:
        return None
    if price_inr <= 0 or area_sqft <= 0:
        return None

    # Check compatibility: carpet must match carpet, plot must match plot, etc.
    if subject_area_type == AreaType.UNKNOWN or comp_area_type == AreaType.UNKNOWN:
        return None
    if subject_area_type != comp_area_type:
        return None

    return round(price_inr / area_sqft, 2)
