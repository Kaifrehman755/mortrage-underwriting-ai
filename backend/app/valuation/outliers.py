"""Locality-aware robust outlier detection.

Enforces GEMINI.md Section 6:
- Uses robust score: robust_z = 0.67449 * (value - median) / MAD
  where MAD is the median absolute deviation: median(|value - median|).
- Handles zero MAD and small groups explicitly.
- Flags outliers for review rather than automatically deleting them.
- Keeps the original value and records the rule and version that generated the flag.
- Does not treat every expensive or inexpensive property as erroneous.
"""

from __future__ import annotations

import statistics
from collections.abc import Sequence

from app.valuation.comps import EligibleComparable

ROBUST_OUTLIER_VERSION = "robust_mad_v1"
DEFAULT_OUTLIER_THRESHOLD = 3.5  # Standard Iglewicz & Hoaglin threshold for robust z
MIN_GROUP_SIZE_FOR_OUTLIERS = 4  # Explicit small group threshold


def calculate_median_and_mad(values: Sequence[float]) -> tuple[float, float]:
    """Calculate the median and Median Absolute Deviation (MAD).

    Returns (median, mad).
    """
    if not values:
        return 0.0, 0.0
    med = float(statistics.median(values))
    deviations = [abs(x - med) for x in values]
    mad = float(statistics.median(deviations))
    return med, mad


def evaluate_robust_outliers(
    comps: list[EligibleComparable],
    threshold: float = DEFAULT_OUTLIER_THRESHOLD,
    min_group_size: int = MIN_GROUP_SIZE_FOR_OUTLIERS,
) -> tuple[list[EligibleComparable], list[str]]:
    """Evaluate price-per-square-foot values for robust outliers using Median Absolute Deviation.

    Returns (updated_comps, log_messages).
    Note: Outliers are flagged with is_outlier=True and robust_z recorded;
    they are retained for audit and transparent review rather than silently dropped.
    """
    logs: list[str] = []
    if len(comps) < min_group_size:
        logs.append(
            f"Group size ({len(comps)}) < {min_group_size}; robust outlier detection bypassed to prevent small-sample bias."
        )
        return comps, logs

    values = [c.price_per_sqft for c in comps]
    median_val, mad_val = calculate_median_and_mad(values)

    if mad_val == 0.0:
        logs.append(
            f"Zero MAD detected across {len(comps)} comparables (median={median_val:.2f}); outlier scoring bypassed."
        )
        # All comps have essentially identical price-per-sqft; robust_z is 0
        updated = [
            EligibleComparable(
                transaction_id=c.transaction_id,
                property_id=c.property_id,
                distance_m=c.distance_m,
                transaction_date=c.transaction_date,
                price_inr=c.price_inr,
                area_sqft=c.area_sqft,
                area_type=c.area_type,
                price_per_sqft=c.price_per_sqft,
                selection_reason=c.selection_reason,
                is_outlier=False,
                robust_z=0.0,
            )
            for c in comps
        ]
        return updated, logs

    updated_comps: list[EligibleComparable] = []
    outlier_count = 0

    for c in comps:
        diff = c.price_per_sqft - median_val
        robust_z = round(0.67449 * diff / mad_val, 3)
        is_outlier = abs(robust_z) >= threshold

        reason = c.selection_reason
        if is_outlier:
            outlier_count += 1
            reason += f" [FLAGGED_OUTLIER: robust_z={robust_z} >= {threshold} via {ROBUST_OUTLIER_VERSION}]"

        updated_comps.append(
            EligibleComparable(
                transaction_id=c.transaction_id,
                property_id=c.property_id,
                distance_m=c.distance_m,
                transaction_date=c.transaction_date,
                price_inr=c.price_inr,
                area_sqft=c.area_sqft,
                area_type=c.area_type,
                price_per_sqft=c.price_per_sqft,
                selection_reason=reason,
                is_outlier=is_outlier,
                robust_z=robust_z,
            )
        )

    if outlier_count > 0:
        logs.append(
            f"Robust outlier check flagged {outlier_count} comps exceeding |robust_z| >= {threshold} (median={median_val:.2f}, MAD={mad_val:.2f})."
        )
    else:
        logs.append(
            f"Robust outlier check passed: all {len(comps)} comps within normal dispersion (median={median_val:.2f}, MAD={mad_val:.2f})."
        )

    return updated_comps, logs
