"""Automated Valuation Model (AVM) and appraisal reconciliation engine.

Implements Playbook Section 7 (Valuation method), Section 14.6 (Market indicators),
Section 18.4, and Section 19.4.
"""

import math
from pathlib import Path
from typing import Any, Literal

import numpy as np

from app.property.comps import ComparableSalesAnalyzer
from app.property.jurisdictions import get_jurisdiction
from app.property.market_index import (
    MarketIndexSnapshot,
    load_market_index,
    period_for_date,
    prior_year_period,
)
from app.property.schemas import ComparableRecord, SubjectProperty, ValuationOutput


def get_hpi_for_date(
    sale_date_str: str,
    snapshot: MarketIndexSnapshot | None = None,
) -> float | None:
    """Return the HPI level for a given date, or None when the index cannot supply it.

    F-02: there is deliberately **no fallback constant**. A missing, stale or
    unverified index value must never be replaced by an invented number; callers
    abstain from the affected time adjustment instead.
    """
    if snapshot is None:
        return None
    return snapshot.value_for_period(period_for_date(sale_date_str))


def calculate_weighted_median(values: list[float], weights: list[float]) -> float:
    """Calculate the 50th percentile weighted median."""
    if not values or not weights:
        raise ValueError("Cannot compute weighted median on empty data.")

    sorted_pairs = sorted(zip(values, weights, strict=True), key=lambda x: x[0])
    sorted_v = [p[0] for p in sorted_pairs]
    sorted_w = [p[1] for p in sorted_pairs]

    total_weight = sum(sorted_w)
    target = total_weight / 2.0
    cum_w = 0.0

    for v, w in zip(sorted_v, sorted_w, strict=True):
        cum_w += w
        if cum_w >= target:
            return v
    return sorted_v[-1]


class PropertyValuationEngine:
    """Reconciles comparable sales into a rigorous valuation estimate with confidence intervals."""

    def __init__(
        self,
        analyzer: ComparableSalesAnalyzer | None = None,
        model_version: str = "1.0.0",
        random_seed: int = 42,
        allow_synthetic: bool = False,
        market_index: MarketIndexSnapshot | None = None,
        market_index_path: str | Path | None = None,
    ):
        self.analyzer = analyzer or ComparableSalesAnalyzer(allow_synthetic=allow_synthetic)
        self.model_version = model_version
        self.random_seed = random_seed
        # F-01: default is to refuse synthetic evidence; opt in only for tests.
        self.allow_synthetic = allow_synthetic
        # F-02: the HPI series is loaded from a versioned file carrying provenance
        # and a verification status; an unverified/absent series is never invented.
        self.market_index = (
            market_index if market_index is not None else load_market_index(market_index_path)
        )

    def valuate(
        self,
        case_id: str,
        subject: SubjectProperty,
        available_comps: list[ComparableRecord],
    ) -> ValuationOutput:
        """Run comparable selection, time adjustment, weighted median estimation, and bootstrap intervals.

        Enforces all Playbook invariants:
        - Invariant 1: No fabrication, abstains on thin data.
        - Invariant 2: Market facts & model estimates separated.
        - Invariant 4: Low confidence or abstain sets human_review_required.
        - Invariant 5: No protected-class proxies.
        - Invariant 8: Comp state isolation.
        """
        # 1. Check state support
        try:
            jurisdiction = get_jurisdiction(subject.state_code)
        except ValueError:
            return ValuationOutput(
                case_id=case_id,
                subject_id=subject.property_id,
                abstain_reason=f"unsupported_state_{subject.state_code}",
                confidence_label="low",
                confidence_level=0.0,
                model_version=self.model_version,
            )

        # 2. Check property type support (Section 19.4)
        if subject.property_type not in jurisdiction.supported_property_types:
            return ValuationOutput(
                case_id=case_id,
                subject_id=subject.property_id,
                abstain_reason=f"unsupported_property_type_{subject.property_type}",
                confidence_label="low",
                confidence_level=0.0,
                model_version=self.model_version,
            )

        # 3. Check subject completeness
        if subject.living_area_sqft <= 0 or subject.lat == 0 or subject.lon == 0:
            return ValuationOutput(
                case_id=case_id,
                subject_id=subject.property_id,
                abstain_reason="missing_subject_attributes",
                confidence_label="low",
                confidence_level=0.0,
                model_version=self.model_version,
            )

        # 4. Select comps with step widening
        selected_comps, select_meta = self.analyzer.select_comps(subject, available_comps)
        n_comps = len(selected_comps)
        synthetic_excluded = int(select_meta.get("synthetic_excluded", 0))

        # Calculate market indicators (Invariant 2: kept strictly separate)
        indicators = self._compute_market_indicators(subject, available_comps)

        # Abstain rule: fewer than 3 usable comps
        if n_comps < jurisdiction.min_comps_estimate:
            # F-01: distinguish "no evidence" from "eligible evidence exists but
            # is synthetic-only and therefore not permitted in production".
            abstain_reason = (
                "synthetic_evidence_not_permitted"
                if synthetic_excluded > 0 and not self.allow_synthetic
                else "insufficient_comparables"
            )
            return ValuationOutput(
                case_id=case_id,
                subject_id=subject.property_id,
                n_comps=n_comps,
                comp_ids=[c.comp_id for c in selected_comps],
                abstain_reason=abstain_reason,
                confidence_label="low",
                confidence_level=round(n_comps / 5.0, 2),
                market_indicators=indicators,
                model_version=self.model_version,
            )

        # 5. Time-adjust comps via the versioned HPI series (F-02).
        #    If the series is absent, unverified, or does not cover a comp's quarter,
        #    the affected time adjustment is abstained from rather than invented.
        index_usable, index_status = self._market_index_usable()
        snapshot = self.market_index
        current_hpi = (
            snapshot.value_for_period(snapshot.latest_period)
            if index_usable and snapshot is not None
            else None
        )
        adj_ppsfs: list[float] = []
        missing_index_periods: list[str] = []
        for c in selected_comps:
            raw_ppsf = c.sale_price / c.living_area_sqft
            period = period_for_date(c.sale_date)
            comp_hpi = (
                snapshot.value_for_period(period) if (index_usable and snapshot is not None) else None
            )
            if current_hpi and comp_hpi and comp_hpi > 0:
                adj_ppsfs.append(round(raw_ppsf * (current_hpi / comp_hpi), 2))
            else:
                adj_ppsfs.append(round(raw_ppsf, 2))
                if index_usable:
                    missing_index_periods.append(period or str(c.sale_date))

        time_adjustment_applied = bool(
            index_usable and current_hpi is not None and not missing_index_periods
        )
        index_block = indicators.setdefault("market_index", {})
        index_block["time_adjustment_applied"] = time_adjustment_applied
        index_block["time_adjustment_abstained_reason"] = (
            None
            if time_adjustment_applied
            else (index_status if not index_usable else "incomplete_index_coverage")
        )
        index_block["missing_index_periods"] = sorted(set(missing_index_periods))

        # 6. Similarity weighting
        weights = self.analyzer.compute_similarity_weights(subject, selected_comps)

        # 7. Compute weighted median PPSF & point estimate
        weighted_median_ppsf = calculate_weighted_median(adj_ppsfs, weights)
        estimate = round(subject.living_area_sqft * weighted_median_ppsf, 2)

        # 8. Dispersion (weighted CV)
        weighted_mean = sum(p * w for p, w in zip(adj_ppsfs, weights, strict=True))
        weighted_var = sum(w * ((p - weighted_mean) ** 2) for p, w in zip(adj_ppsfs, weights, strict=True))
        weighted_std = math.sqrt(max(0.0, weighted_var))
        dispersion_cv = round(weighted_std / weighted_mean, 4) if weighted_mean > 0 else 0.0

        # Abstain rule: high dispersion
        if dispersion_cv > jurisdiction.max_dispersion_cv:
            return ValuationOutput(
                case_id=case_id,
                subject_id=subject.property_id,
                n_comps=n_comps,
                comp_ids=[c.comp_id for c in selected_comps],
                dispersion=dispersion_cv,
                abstain_reason="high_dispersion",
                confidence_label="low",
                confidence_level=0.2,
                market_indicators=indicators,
                model_version=self.model_version,
            )

        # 9. Bootstrap 80% confidence interval (1,000 resamples)
        interval_low: float | None = None
        interval_high: float | None = None

        if n_comps >= jurisdiction.min_comps_interval:
            rng = np.random.default_rng(self.random_seed)
            ppsfs_arr = np.array(adj_ppsfs)
            weights_arr = np.array(weights) / sum(weights)

            # Draw 1000 resamples of size n_comps
            sample_indices = rng.choice(n_comps, size=(1000, n_comps), p=weights_arr, replace=True)
            resampled_medians = np.median(ppsfs_arr[sample_indices], axis=1)

            # 80% interval: 10th and 90th percentiles
            p10 = float(np.percentile(resampled_medians, 10))
            p90 = float(np.percentile(resampled_medians, 90))

            interval_low = round(subject.living_area_sqft * p10, 2)
            interval_high = round(subject.living_area_sqft * p90, 2)

        # 10. Confidence assessment
        max_dist = max([c.distance_km or 0.0 for c in selected_comps])
        confidence_label: Literal["low", "medium", "high"]
        if n_comps >= 7 and dispersion_cv <= 0.15 and max_dist <= 2.0:
            confidence_label = "high"
            confidence_score = 0.90
        elif n_comps >= 4 and dispersion_cv <= 0.25:
            confidence_label = "medium"
            confidence_score = 0.75
        else:
            confidence_label = "low"
            confidence_score = 0.50

        return ValuationOutput(
            case_id=case_id,
            subject_id=subject.property_id,
            estimate=estimate,
            interval_low=interval_low,
            interval_high=interval_high,
            confidence_level=confidence_score,
            confidence_label=confidence_label,
            method="weighted_median_ppsf",
            n_comps=n_comps,
            comp_ids=[c.comp_id for c in selected_comps],
            dispersion=dispersion_cv,
            abstain_reason=None,
            model_version=self.model_version,
            market_indicators=indicators,
            evidence_is_synthetic=any(c.is_synthetic for c in selected_comps),
            human_review_required=(confidence_label == "low") or (not time_adjustment_applied),
        )

    def _market_index_usable(self) -> tuple[bool, str]:
        """Decide whether the loaded series may drive a time adjustment (F-02).

        Returns ``(usable, reason)`` where ``reason`` is one of ``verified``,
        ``synthetic_dev_fixture``, ``market_index_unverified`` or
        ``market_index_unavailable``.
        """
        snapshot = self.market_index
        if snapshot is None:
            return False, "market_index_unavailable"
        if snapshot.is_verified:
            return True, "verified"
        # An explicitly-labelled synthetic dev fixture may be used for tests only.
        if self.allow_synthetic:
            return True, "synthetic_dev_fixture"
        return False, "market_index_unverified"

    def _market_index_indicators(self) -> dict[str, Any]:
        """Build the market-index provenance block kept separate from the estimate.

        F-02: ``rbi_hpi_current`` and ``rbi_hpi_yoy_growth_percent`` are reported only
        when a usable series actually supplies them; otherwise they are None rather
        than an invented number.
        """
        snapshot = self.market_index
        usable, reason = self._market_index_usable()
        latest = snapshot.latest_period if snapshot is not None else None
        current = snapshot.value_for_period(latest) if (usable and snapshot is not None) else None

        yoy: float | None = None
        if usable and snapshot is not None and latest is not None:
            previous = snapshot.value_for_period(prior_year_period(latest) or "")
            if current and previous and previous > 0:
                yoy = round(((current / previous) - 1.0) * 100.0, 2)

        return {
            "rbi_hpi_current": current,
            "rbi_hpi_yoy_growth_percent": yoy,
            "market_index": {
                "series_id": snapshot.series_id if snapshot is not None else None,
                "source_name": snapshot.source_name if snapshot is not None else None,
                "source_url": snapshot.source_url if snapshot is not None else None,
                "publication_date": snapshot.publication_date if snapshot is not None else None,
                "base_year": snapshot.base_year if snapshot is not None else None,
                "units": snapshot.units if snapshot is not None else None,
                "verification_status": (
                    snapshot.verification_status if snapshot is not None else "absent"
                ),
                "usable_for_time_adjustment": usable,
                "usable_reason": reason,
                "time_adjustment_applied": False,
                "time_adjustment_abstained_reason": None if usable else reason,
                "missing_index_periods": [],
            },
        }

    def _compute_market_indicators(
        self,
        subject: SubjectProperty,
        comps: list[ComparableRecord],
    ) -> dict[str, Any]:
        """Aggregate market indicators stored separately from model estimates.

        Playbook Section 14.6: locality median, asking vs registered gap, HPI trend.
        """
        eligible = [c for c in comps if self.allow_synthetic or not c.is_synthetic]
        loc_comps = [c for c in eligible if c.locality == subject.locality and c.state_code == subject.state_code]
        if not loc_comps:
            loc_comps = [c for c in eligible if c.state_code == subject.state_code]

        registered = [c.price_per_sqft for c in loc_comps if c.price_type == "registered_deed"]
        asking = [c.price_per_sqft for c in loc_comps if c.price_type == "asking"]

        median_reg = float(np.median(registered)) if registered else None
        median_ask = float(np.median(asking)) if asking else None

        gap_pct = None
        if median_reg and median_ask:
            gap_pct = round(((median_ask - median_reg) / median_reg) * 100.0, 2)

        return {
            "locality": subject.locality,
            "sample_size": len(loc_comps),
            "median_registered_ppsf": median_reg,
            "median_asking_ppsf": median_ask,
            "asking_vs_registered_gap_percent": gap_pct,
            **self._market_index_indicators(),
        }

    def run_backtest(
        self,
        comps: list[ComparableRecord],
    ) -> dict[str, Any]:
        """Backtest valuation engine on held-out comps (Leave-One-Out Cross Validation).

        Playbook Section 7 & 10: Reports MAPE (Median Absolute Percentage Error) and interval coverage.
        """
        usable = [c for c in comps if c.price_type in ("registered_deed", "valuer_report")]
        if len(usable) < 6:
            return {"error": "Need at least 6 usable comps for meaningful backtest."}

        errors_pct: list[float] = []
        covered_count = 0
        total_eval = 0

        for i, target in enumerate(usable):
            # Hold out target comp
            training_pool = [c for j, c in enumerate(usable) if j != i]

            # Form fake subject from target comp
            subj = SubjectProperty(
                original_address=target.address,
                address_norm=target.address,
                locality=target.locality,
                city=target.city,
                state_code=target.state_code,
                living_area_sqft=target.living_area_sqft,
                lat=target.raw.get("lat", 26.85) if target.raw else 26.85,
                lon=target.raw.get("lon", 80.99) if target.raw else 80.99,
            )

            res = self.valuate(case_id=f"backtest_{i}", subject=subj, available_comps=training_pool)
            if res.estimate is not None:
                total_eval += 1
                ape = abs(res.estimate - target.sale_price) / target.sale_price * 100.0
                errors_pct.append(ape)

                if res.interval_low and res.interval_high:
                    if res.interval_low <= target.sale_price <= res.interval_high:
                        covered_count += 1

        mape = round(float(np.median(errors_pct)), 2) if errors_pct else 0.0
        coverage = round((covered_count / total_eval) * 100.0, 2) if total_eval > 0 else 0.0

        return {
            "total_samples": len(usable),
            "evaluated": total_eval,
            "mape_percent": mape,
            "interval_coverage_80_percent": coverage,
        }
