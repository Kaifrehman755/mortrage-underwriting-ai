"""Confidence scoring and uncertainty interval calculations.

Enforces GEMINI.md Section 2, Section 8, and CLAUDE.md Non-Negotiable Rule 10:
- Confidence is NOT a probability; it is an evidence-backed confidence score in [0.0, 1.0].
- Calculate uncertainty bounds only when the number and consistency of comparables support them (>= 5 comps).
- Never claim an interval is a calibrated probability unless validated on an independent evaluation set.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

from app.valuation.comps import EligibleComparable


@dataclass(frozen=True)
class ConfidenceAssessment:
    """Assessment of evidence quality, confidence score, and empirical uncertainty bounds."""

    confidence_score: float  # [0.0, 1.0]
    confidence_label: str  # "high", "medium", "low", "very_low"
    lower_bound_inr: float | None
    upper_bound_inr: float | None
    bounds_calibrated: bool  # Strictly False unless verified against independent evaluation set
    dispersion_cv: float  # Coefficient of variation of adjusted ppsf
    assessment_notes: list[str]


def calculate_weighted_percentile(
    values: Sequence[float], weights: Sequence[float], percentile: float
) -> float:
    """Calculate a weighted percentile (0 <= percentile <= 1.0)."""
    if not values or not weights or len(values) != len(weights):
        raise ValueError("Values and weights must be non-empty and of identical length.")

    sorted_pairs = sorted(zip(values, weights, strict=True), key=lambda x: x[0])
    sorted_v = [p[0] for p in sorted_pairs]
    sorted_w = [p[1] for p in sorted_pairs]

    total_w = sum(sorted_w)
    if total_w <= 0:
        return sorted_v[len(sorted_v) // 2]

    target = total_w * percentile
    cum_w = 0.0

    for v, w in zip(sorted_v, sorted_w, strict=True):
        cum_w += w
        if cum_w >= target:
            return v
    return sorted_v[-1]


def compute_confidence_and_bounds(
    comps: list[EligibleComparable],
    subject_area_sqft: float,
    estimate_inr: float | None,
    min_comps_for_bounds: int = 5,
    max_allowable_dispersion: float = 0.35,
) -> ConfidenceAssessment:
    """Assess evidence strength, compute evidence confidence score and empirical uncertainty bounds.

    Bounds are ONLY generated when:
    - estimate_inr is present and positive
    - len(comps) >= min_comps_for_bounds (default 5)
    - comp dispersion does not exceed critical threshold
    """
    notes: list[str] = []

    if not comps or estimate_inr is None or estimate_inr <= 0:
        return ConfidenceAssessment(
            confidence_score=0.0,
            confidence_label="very_low",
            lower_bound_inr=None,
            upper_bound_inr=None,
            bounds_calibrated=False,
            dispersion_cv=0.0,
            assessment_notes=["Insufficient or invalid valuation estimate to assess confidence."],
        )

    prices_sqft = [c.price_per_sqft for c in comps]
    mean_ppsf = sum(prices_sqft) / len(prices_sqft)
    variance = sum((p - mean_ppsf) ** 2 for p in prices_sqft) / max(len(prices_sqft) - 1, 1)
    std_ppsf = math.sqrt(variance)
    cv = round(std_ppsf / mean_ppsf, 3) if mean_ppsf > 0 else 1.0

    # 1. Sample Size Component (Weight: 30%)
    n = len(comps)
    if n >= 8:
        score_n = 1.0
    elif n >= 5:
        score_n = 0.85
    elif n >= 3:
        score_n = 0.65
    else:
        score_n = 0.30

    # 2. Proximity Component (Weight: 25%)
    median_dist_km = sorted([c.distance_m / 1000.0 for c in comps])[n // 2]
    if median_dist_km <= 1.5:
        score_dist = 1.0
    elif median_dist_km <= 3.0:
        score_dist = 0.80
    elif median_dist_km <= 5.0:
        score_dist = 0.60
    else:
        score_dist = 0.30

    # 3. Consistency / Dispersion Component (Weight: 30%)
    if cv <= 0.10:
        score_disp = 1.0
    elif cv <= 0.20:
        score_disp = 0.85
    elif cv <= max_allowable_dispersion:
        score_disp = 0.60
    else:
        score_disp = 0.25
        notes.append(f"High price dispersion detected across comparables (CV={cv:.2f} > {max_allowable_dispersion}).")

    # 4. Outlier Penalty (Weight: 15%)
    outliers = [c for c in comps if c.is_outlier]
    if not outliers:
        score_outlier = 1.0
    elif len(outliers) == 1:
        score_outlier = 0.70
        notes.append("1 comparable flagged as robust statistical outlier.")
    else:
        score_outlier = 0.40
        notes.append(f"{len(outliers)} comparables flagged as robust statistical outliers.")

    composite_score = round(
        0.30 * score_n + 0.25 * score_dist + 0.30 * score_disp + 0.15 * score_outlier,
        2,
    )

    if composite_score >= 0.80:
        confidence_label = "high"
    elif composite_score >= 0.60:
        confidence_label = "medium"
    elif composite_score >= 0.40:
        confidence_label = "low"
    else:
        confidence_label = "very_low"

    # Uncertainty bounds calculation
    lower_bound: float | None = None
    upper_bound: float | None = None

    if n < min_comps_for_bounds:
        notes.append(
            f"Fewer than {min_comps_for_bounds} comps available ({n} found); uncertainty intervals withheld to prevent false precision."
        )
    elif cv > max_allowable_dispersion:
        notes.append("Excessive dispersion exceeds tolerance threshold; uncertainty bounds withheld.")
    else:
        # Distance & recency weights for percentiles
        weights = [1.0 / (1.0 + c.distance_m / 1000.0) for c in comps]
        p15_ppsf = calculate_weighted_percentile(prices_sqft, weights, 0.15)
        p85_ppsf = calculate_weighted_percentile(prices_sqft, weights, 0.85)

        raw_lower = round(p15_ppsf * subject_area_sqft, 2)
        raw_upper = round(p85_ppsf * subject_area_sqft, 2)

        # Enforce strict invariant: lower <= estimate <= upper
        lower_bound = min(raw_lower, estimate_inr)
        upper_bound = max(raw_upper, estimate_inr)

        notes.append(
            f"Derived empirical 15th-85th percentile evidence interval [{lower_bound:,.0f}, {upper_bound:,.0f}] INR "
            f"(uncalibrated heuristic bounds; not tested on independent holdout)."
        )

    return ConfidenceAssessment(
        confidence_score=composite_score,
        confidence_label=confidence_label,
        lower_bound_inr=lower_bound,
        upper_bound_inr=upper_bound,
        bounds_calibrated=False,  # Strictly uncalibrated per GEMINI.md Section 8
        dispersion_cv=cv,
        assessment_notes=notes,
    )
