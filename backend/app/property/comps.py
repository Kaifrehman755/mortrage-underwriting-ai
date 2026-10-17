"""Comparable sales analysis module.

Implements Playbook Section 7 (Valuation method - step 1 select comps, step 4 similarity weighting)
and Section 14.5, 14.7.
"""

import logging
import math
from datetime import date
from typing import Any

from app.property.normalize import haversine_km
from app.property.schemas import ComparableRecord, SubjectProperty

logger = logging.getLogger(__name__)


class ComparableSalesAnalyzer:
    """Analyzes, filters, steps widens, and computes similarity weights for comps."""

    def __init__(
        self,
        initial_radius_km: float = 2.0,
        max_radius_km: float = 5.0,
        initial_area_tolerance: float = 0.20,
        max_area_tolerance: float = 0.40,
        reference_date: date | None = None,
        allow_synthetic: bool = False,
    ):
        self.initial_radius_km = initial_radius_km
        self.max_radius_km = max_radius_km
        self.initial_area_tolerance = initial_area_tolerance
        self.max_area_tolerance = max_area_tolerance
        self.reference_date = reference_date or date(2026, 10, 10)
        # F-01: synthetic comparables are never eligible unless an explicit,
        # test-only opt-in is supplied by the caller.
        self.allow_synthetic = allow_synthetic

    def select_comps(
        self,
        subject: SubjectProperty,
        all_comps: list[ComparableRecord],
    ) -> tuple[list[ComparableRecord], dict[str, Any]]:
        """Select best comps with recorded step-widening.

        Invariant 8: Must be identical state_code.
        Invariant 5: Protected-class proxies excluded.
        Rule: Asking prices excluded from estimate comps (only registered/valuer/survey).
        """
        # Exclude asking prices for valuation estimate.
        # F-01: synthetic comparables (is_synthetic=True) are excluded from the
        # eligible pool unless an explicit test-only opt-in (allow_synthetic=True)
        # was supplied, so fabricated rows can never reach a production estimate.
        excluded_synthetic = [
            c for c in all_comps if c.is_synthetic and not self.allow_synthetic
        ]
        usable_pool = [
            c for c in all_comps
            if c.price_type in ("registered_deed", "valuer_report", "survey")
            and c.state_code == subject.state_code
            and c.property_type == subject.property_type
            and (self.allow_synthetic or not c.is_synthetic)
        ]

        steps: list[dict[str, Any]] = []
        selected: list[ComparableRecord] = []

        widening_ladder = [
            {"step": 1, "radius_km": self.initial_radius_km, "area_tol": self.initial_area_tolerance},
            {"step": 2, "radius_km": 3.5, "area_tol": 0.30},
            {"step": 3, "radius_km": self.max_radius_km, "area_tol": self.max_area_tolerance},
        ]

        for ladder in widening_ladder:
            rad = ladder["radius_km"]
            tol = ladder["area_tol"]

            candidates: list[ComparableRecord] = []
            for c in usable_pool:
                dist = c.distance_km
                if dist is None:
                    dist = haversine_km(subject.lat, subject.lon, c.raw.get("lat", 0), c.raw.get("lon", 0)) if c.raw else 999.0

                if dist > rad:
                    continue

                # Living area gap check
                area_ratio = abs(c.living_area_sqft - subject.living_area_sqft) / subject.living_area_sqft
                if area_ratio > tol:
                    continue

                candidates.append(c)

            steps.append({
                "step": ladder["step"],
                "radius_km": rad,
                "area_tolerance": tol,
                "comps_found": len(candidates),
            })

            if len(candidates) >= 3:
                selected = candidates
                break

        if not selected and candidates:
            selected = candidates

        meta = {
            "steps_recorded": steps,
            "final_radius_km": steps[-1]["radius_km"] if steps else self.initial_radius_km,
            "total_candidates": len(selected),
            "synthetic_excluded": len(excluded_synthetic),
        }
        return selected, meta

    def compute_similarity_weights(
        self,
        subject: SubjectProperty,
        comps: list[ComparableRecord],
    ) -> list[float]:
        """Compute exponential similarity weights based on distance, recency, and area gap.

        Closer distance, more recent, and smaller size gap get more weight.
        """
        if not comps:
            return []

        raw_weights: list[float] = []
        today = self.reference_date

        for c in comps:
            # 1. Distance decay: half weight at ~1.5 km
            dist = c.distance_km if c.distance_km is not None else 1.0
            w_dist = math.exp(-dist / 1.5)

            # 2. Recency decay: half weight at ~6 months (180 days)
            try:
                comp_d = date.fromisoformat(c.sale_date[:10])
                days_diff = max(0, (today - comp_d).days)
                months_diff = days_diff / 30.4
            except (ValueError, TypeError):
                # F-14: catch only the realistic parse failures and make the neutral
                # fallback observable instead of silently inventing a recency value.
                logger.warning(
                    "Unparseable sale_date %r for comp %s; using neutral 6.0-month recency",
                    c.sale_date,
                    c.comp_id,
                )
                months_diff = 6.0
            w_rec = math.exp(-months_diff / 6.0)

            # 3. Area difference decay
            area_ratio = abs(c.living_area_sqft - subject.living_area_sqft) / subject.living_area_sqft
            w_area = math.exp(-area_ratio / 0.15)

            w_total = w_dist * w_rec * w_area
            raw_weights.append(max(w_total, 1e-4))

        sum_w = sum(raw_weights)
        if sum_w == 0:
            return [1.0 / len(comps)] * len(comps)

        return [round(w / sum_w, 6) for w in raw_weights]
