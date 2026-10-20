"""Valuation Estimation and Abstention Engine.

Enforces GEMINI.md Section 4.7, Section 6, Section 8, and Section 10 Step 6:
- Transparent, robust estimation using weighted median price-per-square-foot.
- Explicit reason-coded abstention and human review triggers:
  * INSUFFICIENT_COMPARABLES (< min_comps)
  * MISSING_COORDINATES
  * AREA_BASIS_INCOMPATIBLE
  * STATE_NOT_SUPPORTED
  * EXCESSIVE_DISPERSION
  * STALE_EVIDENCE
  * OUTLIERS_DETECTED
- Every estimate is traceable to the eligible evidence used.
"""

from __future__ import annotations

import math
from datetime import date
from typing import Any, Sequence
from uuid import UUID, uuid4

from app.providers.registry import state_provider_registry
from app.schemas.property import AreaType
from app.schemas.valuation import (
    ValuationComparableRead,
    ValuationRunCreate,
    ValuationStatus,
)
from app.valuation.comps import ComparableSelector, EligibleComparable, SubjectPropertyInput
from app.valuation.confidence import compute_confidence_and_bounds
from app.valuation.outliers import evaluate_robust_outliers

METHOD_VERSION = "robust_weighted_median_v1"


def calculate_weighted_median(values: Sequence[float], weights: Sequence[float]) -> float:
    """Calculate the 50th percentile weighted median."""
    if not values or not weights:
        raise ValueError("Cannot compute weighted median on empty data.")
    if len(values) != len(weights):
        raise ValueError("Values and weights must have identical length.")

    sorted_pairs = sorted(zip(values, weights, strict=True), key=lambda x: x[0])
    sorted_v = [p[0] for p in sorted_pairs]
    sorted_w = [p[1] for p in sorted_pairs]

    total_weight = sum(sorted_w)
    if total_weight <= 0:
        return sorted_v[len(sorted_v) // 2]

    target = total_weight / 2.0
    cum_w = 0.0

    for v, w in zip(sorted_v, sorted_w, strict=True):
        cum_w += w
        if cum_w >= target:
            return v
    return sorted_v[-1]


class ValuationEngine:
    """Deterministic, auditable valuation and abstention engine."""

    def __init__(
        self,
        selector: ComparableSelector | None = None,
        min_comps: int = 3,
        min_comps_for_bounds: int = 5,
        max_dispersion_cv: float = 0.35,
        max_stale_days: int = 450,
    ) -> None:
        self.selector = selector or ComparableSelector(min_comps=min_comps)
        self.min_comps = min_comps
        self.min_comps_for_bounds = min_comps_for_bounds
        self.max_dispersion_cv = max_dispersion_cv
        self.max_stale_days = max_stale_days

    def evaluate(
        self,
        subject: SubjectPropertyInput,
        candidate_pool: list[dict[str, Any]],
        dataset_cutoff: date,
        valuation_id: UUID | None = None,
    ) -> tuple[ValuationRunCreate, list[ValuationComparableRead]]:
        """Run candidate filtering, outlier detection, robust estimation, and abstention checks.

        Returns (valuation_run_create, comparables_read).
        """
        val_id = valuation_id or uuid4()
        reason_codes: list[str] = []

        subject_dict = {
            "state_code": subject.state_code,
            "district": subject.district,
            "locality": subject.locality,
            "latitude": subject.latitude,
            "longitude": subject.longitude,
            "area_sqft": subject.area_sqft,
            "area_type": subject.area_type.value if hasattr(subject.area_type, "value") else str(subject.area_type),
            "property_type": subject.property_type.value if hasattr(subject.property_type, "value") else str(subject.property_type),
            "pincode": subject.pincode,
        }

        # 1. Check State Support (GEMINI.md Rule: Unsupported states return explicit error, no fabrication)
        if not state_provider_registry.is_state_supported(subject.state_code):
            reason_codes.append("STATE_NOT_SUPPORTED")
            run = ValuationRunCreate(
                subject_property_input=subject_dict,
                estimate_inr=None,
                lower_bound_inr=None,
                upper_bound_inr=None,
                status=ValuationStatus.ABSTAINED,
                reason_codes=reason_codes,
                method_version=METHOD_VERSION,
                dataset_cutoff=dataset_cutoff,
            )
            return run, []

        # 2. Check Geographic Coordinates
        if subject.latitude is None or subject.longitude is None:
            reason_codes.append("MISSING_COORDINATES")
            run = ValuationRunCreate(
                subject_property_input=subject_dict,
                estimate_inr=None,
                lower_bound_inr=None,
                upper_bound_inr=None,
                status=ValuationStatus.ABSTAINED,
                reason_codes=reason_codes,
                method_version=METHOD_VERSION,
                dataset_cutoff=dataset_cutoff,
            )
            return run, []

        # 3. Check Area Type Basis
        if subject.area_type == AreaType.UNKNOWN:
            reason_codes.append("AREA_BASIS_INCOMPATIBLE")
            run = ValuationRunCreate(
                subject_property_input=subject_dict,
                estimate_inr=None,
                lower_bound_inr=None,
                upper_bound_inr=None,
                status=ValuationStatus.ABSTAINED,
                reason_codes=reason_codes,
                method_version=METHOD_VERSION,
                dataset_cutoff=dataset_cutoff,
            )
            return run, []

        # 4. Filter Candidate Pool against Strict Eligibility Rules
        eligible_comps, filter_logs = self.selector.filter_candidate_pool(
            subject=subject,
            candidates=candidate_pool,
            dataset_cutoff=dataset_cutoff,
        )

        # 5. Check Minimum Number of Comparables
        if len(eligible_comps) < self.min_comps:
            reason_codes.append("INSUFFICIENT_COMPARABLES")
            run = ValuationRunCreate(
                subject_property_input=subject_dict,
                estimate_inr=None,
                lower_bound_inr=None,
                upper_bound_inr=None,
                status=ValuationStatus.ABSTAINED,
                reason_codes=reason_codes,
                method_version=METHOD_VERSION,
                dataset_cutoff=dataset_cutoff,
            )
            return run, []

        # 6. Check Recency / Staleness
        ages_days = [(dataset_cutoff - c.transaction_date).days for c in eligible_comps]
        median_age = sorted(ages_days)[len(ages_days) // 2]
        is_stale = median_age > self.max_stale_days
        if is_stale:
            reason_codes.append("STALE_EVIDENCE")

        # 7. Robust Outlier Evaluation (Locality MAD)
        comps_evaluated, outlier_logs = evaluate_robust_outliers(eligible_comps)
        outliers_detected = any(c.is_outlier for c in comps_evaluated)
        if outliers_detected:
            reason_codes.append("OUTLIERS_DETECTED")

        # 8. Weight Calculation (Distance decay + Recency decay)
        # Higher weights for geographically closer and more recent sales
        weights: list[float] = []
        prices: list[float] = []

        for c in comps_evaluated:
            w_dist = 1.0 / (1.0 + (c.distance_m / 1000.0))
            age_d = max((dataset_cutoff - c.transaction_date).days, 0)
            w_time = math.exp(-0.001 * age_d)
            # Give flagged outliers half weight rather than dropping them silently
            w_outlier = 0.5 if c.is_outlier else 1.0
            weights.append(round(w_dist * w_time * w_outlier, 4))
            prices.append(c.price_per_sqft)

        # 9. Compute Weighted Median Point Estimate
        est_ppsf = calculate_weighted_median(prices, weights)
        estimate_inr = round(est_ppsf * subject.area_sqft, 2)

        # 10. Confidence & Uncertainty Intervals
        confidence_meta = compute_confidence_and_bounds(
            comps=comps_evaluated,
            subject_area_sqft=subject.area_sqft,
            estimate_inr=estimate_inr,
            min_comps_for_bounds=self.min_comps_for_bounds,
            max_allowable_dispersion=self.max_dispersion_cv,
        )

        if confidence_meta.dispersion_cv > self.max_dispersion_cv:
            reason_codes.append("EXCESSIVE_DISPERSION")

        if confidence_meta.confidence_label == "low":
            reason_codes.append("LOW_EVIDENCE_CONFIDENCE")

        # 11. Determine Final Valuation Status
        # If any risk flags were raised, route to human review rather than claiming false certainty
        if reason_codes:
            status = ValuationStatus.NEEDS_HUMAN_REVIEW
        else:
            status = ValuationStatus.COMPLETED

        run_create = ValuationRunCreate(
            subject_property_input=subject_dict,
            estimate_inr=estimate_inr,
            lower_bound_inr=confidence_meta.lower_bound_inr,
            upper_bound_inr=confidence_meta.upper_bound_inr,
            status=status,
            reason_codes=reason_codes,
            method_version=METHOD_VERSION,
            dataset_cutoff=dataset_cutoff,
        )

        # 12. Build Traceable Valuation Comparables
        comparables_read: list[ValuationComparableRead] = []
        for c, w in zip(comps_evaluated, weights, strict=True):
            sim_score = min(max(round(w, 3), 0.0), 1.0)
            comparables_read.append(
                ValuationComparableRead(
                    valuation_id=val_id,
                    transaction_id=c.transaction_id,
                    distance_m=c.distance_m,
                    similarity_score=sim_score,
                    adjusted_price_per_sqft=round(c.price_per_sqft, 2),
                    selection_reason=c.selection_reason,
                )
            )

        return run_create, comparables_read
