"""Geographic and Temporal Leakage Prevention and Evaluation Framework.

Enforces GEMINI.md Section 7, Section 10 Step 6, and Section 11:
- Group isolation: Keeps records belonging to the same known property in one partition.
- Temporal holdout: Evaluates on out-of-time transactions strictly subsequent to cutoff.
- Locality holdout: Evaluates geographic transferability without locality leakage.
- Split manifest recording: seed, algorithm version, cutoff dates, and groups.
- Comprehensive metrics: MdAPE, MAPE, coverage, abstention, large errors (>20%),
  and stratified reporting by state/locality.
- Explicitly flags sample size limitations when records are insufficient for generalizability claims.
"""

from __future__ import annotations

import hashlib
import statistics
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from app.schemas.property import AreaType, PropertyType
from app.schemas.valuation import ValuationStatus
from app.valuation.comps import SubjectPropertyInput
from app.valuation.estimate import ValuationEngine

SPLIT_ALGORITHM_VERSION = "leakage_free_split_v1"


@dataclass(frozen=True)
class SplitManifest:
    """Immutable audit record of train/test data splitting."""

    seed: int
    algorithm_version: str
    strategy: str  # "temporal", "locality_holdout", "property_grouped"
    split_date: str | None
    total_records: int
    train_count: int
    test_count: int
    held_out_localities: list[str] = field(default_factory=list)
    manifest_hash: str = ""


@dataclass(frozen=True)
class EvaluationMetrics:
    """Comprehensive performance and coverage metrics for valuation evaluation."""

    sample_size: int
    completed_count: int
    abstained_count: int
    human_review_count: int
    coverage_rate: float  # completed / sample_size
    abstention_rate: float  # abstained / sample_size
    human_review_rate: float  # (abstained + human_review) / sample_size
    mdape: float | None  # Median Absolute Percentage Error (%)
    mape: float | None  # Mean Absolute Percentage Error (%)
    large_error_rate_20pct: float | None  # % of completed with error > 20%
    stratified_by_state: dict[str, dict[str, Any]]
    sample_size_limitation_warning: str | None


def create_temporal_split(
    records: list[dict[str, Any]],
    split_date: date,
    seed: int = 42,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], SplitManifest]:
    """Split records temporally with property group isolation to prevent evaluation leakage.

    All transactions or listings belonging to the same known property_id remain
    strictly in one partition.
    """
    # 1. Group records by property_id
    property_groups: dict[str, list[dict[str, Any]]] = {}
    for r in records:
        pid = str(r.get("property_id") or r.get("source_record_id") or r.get("transaction_id") or "UNLINKED")
        property_groups.setdefault(pid, []).append(r)

    train_records: list[dict[str, Any]] = []
    test_records: list[dict[str, Any]] = []

    for group in property_groups.values():
        # Check max date in this property group
        dates: list[date] = []
        for r in group:
            raw_d = r.get("transaction_date") or r.get("date")
            if raw_d:
                dt = raw_d if isinstance(raw_d, date) else date.fromisoformat(str(raw_d)[:10])
                dates.append(dt)

        if not dates:
            train_records.extend(group)
            continue

        min_d = min(dates)
        # Property group assignment: If initial transaction occurred prior to or on split date,
        # assign historical transactions to train; if entire group is subsequent, assign to test
        if min_d <= split_date:
            # Assign strictly prior transactions to train
            for r in group:
                raw_d = r.get("transaction_date") or r.get("date")
                txn_date: date | None = (
                    raw_d
                    if isinstance(raw_d, date)
                    else date.fromisoformat(str(raw_d)[:10])
                    if raw_d
                    else None
                )
                if txn_date and txn_date <= split_date:
                    train_records.append(r)
        else:
            test_records.extend(group)

    manifest_content = f"{seed}:{SPLIT_ALGORITHM_VERSION}:temporal:{split_date}:{len(train_records)}:{len(test_records)}"
    manifest_hash = hashlib.sha256(manifest_content.encode("utf-8")).hexdigest()

    manifest = SplitManifest(
        seed=seed,
        algorithm_version=SPLIT_ALGORITHM_VERSION,
        strategy="temporal",
        split_date=split_date.isoformat(),
        total_records=len(records),
        train_count=len(train_records),
        test_count=len(test_records),
        manifest_hash=manifest_hash,
    )

    return train_records, test_records, manifest


def create_locality_holdout_split(
    records: list[dict[str, Any]],
    held_out_localities: list[str],
    seed: int = 42,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], SplitManifest]:
    """Hold out entire localities to measure out-of-market geographic generalization without leakage."""
    norm_held = {loc.strip().lower() for loc in held_out_localities}
    train_records: list[dict[str, Any]] = []
    test_records: list[dict[str, Any]] = []

    for r in records:
        loc = str(r.get("locality", "")).strip().lower()
        if loc in norm_held:
            test_records.append(r)
        else:
            train_records.append(r)

    manifest_content = f"{seed}:{SPLIT_ALGORITHM_VERSION}:locality:{sorted(norm_held)}:{len(train_records)}:{len(test_records)}"
    manifest_hash = hashlib.sha256(manifest_content.encode("utf-8")).hexdigest()

    manifest = SplitManifest(
        seed=seed,
        algorithm_version=SPLIT_ALGORITHM_VERSION,
        strategy="locality_holdout",
        split_date=None,
        total_records=len(records),
        train_count=len(train_records),
        test_count=len(test_records),
        held_out_localities=sorted(norm_held),
        manifest_hash=manifest_hash,
    )

    return train_records, test_records, manifest


def run_benchmark_evaluation(
    engine: ValuationEngine,
    eval_records: list[dict[str, Any]],
    training_candidates: list[dict[str, Any]],
    dataset_cutoff: date,
) -> EvaluationMetrics:
    """Evaluate valuation engine against holdout test records strictly using training evidence.

    Computes MdAPE, MAPE, Coverage, Abstention, Large Errors (>20%), and Stratified Metrics.
    """
    total = len(eval_records)
    if total == 0:
        return EvaluationMetrics(
            sample_size=0,
            completed_count=0,
            abstained_count=0,
            human_review_count=0,
            coverage_rate=0.0,
            abstention_rate=0.0,
            human_review_rate=0.0,
            mdape=None,
            mape=None,
            large_error_rate_20pct=None,
            stratified_by_state={},
            sample_size_limitation_warning="Empty evaluation set provided.",
        )

    completed = 0
    abstained = 0
    needs_review = 0
    errors_pct: list[float] = []

    state_stats: dict[str, dict[str, Any]] = {}

    for rec in eval_records:
        state_code = str(rec.get("state_code", "")).upper()
        if state_code not in state_stats:
            state_stats[state_code] = {"total": 0, "completed": 0, "abstained": 0, "errors_pct": []}
        state_stats[state_code]["total"] += 1

        actual_price = float(rec.get("price_inr") or rec.get("transaction_price_inr") or 0)
        area_sqft = float(rec.get("area_sqft") or rec.get("living_area_sqft") or 1000)

        area_type_str = str(rec.get("area_type", "carpet")).lower()
        try:
            area_type = AreaType(area_type_str)
        except ValueError:
            area_type = AreaType.CARPET

        subject = SubjectPropertyInput(
            state_code=state_code,
            district=str(rec.get("district", "Unknown")),
            locality=str(rec.get("locality", "Unknown")),
            latitude=rec.get("latitude") or rec.get("lat"),
            longitude=rec.get("longitude") or rec.get("lon"),
            area_sqft=area_sqft,
            area_type=area_type,
            property_type=PropertyType.APARTMENT,
        )

        val_run, comps = engine.evaluate(
            subject=subject,
            candidate_pool=training_candidates,
            dataset_cutoff=dataset_cutoff,
        )

        if val_run.status == ValuationStatus.ABSTAINED:
            abstained += 1
            state_stats[state_code]["abstained"] += 1
        elif val_run.status == ValuationStatus.NEEDS_HUMAN_REVIEW:
            needs_review += 1
            if val_run.estimate_inr and actual_price > 0:
                err = abs(val_run.estimate_inr - actual_price) / actual_price * 100.0
                errors_pct.append(err)
                state_stats[state_code]["errors_pct"].append(err)
        elif val_run.status == ValuationStatus.COMPLETED:
            completed += 1
            state_stats[state_code]["completed"] += 1
            if val_run.estimate_inr and actual_price > 0:
                err = abs(val_run.estimate_inr - actual_price) / actual_price * 100.0
                errors_pct.append(err)
                state_stats[state_code]["errors_pct"].append(err)

    cov_rate = round(completed / total, 3)
    abs_rate = round(abstained / total, 3)
    rev_rate = round((abstained + needs_review) / total, 3)

    mdape = round(statistics.median(errors_pct), 2) if errors_pct else None
    mape = round(sum(errors_pct) / len(errors_pct), 2) if errors_pct else None
    large_errors = (
        round(sum(1 for e in errors_pct if e > 20.0) / len(errors_pct) * 100.0, 1)
        if errors_pct
        else None
    )

    stratified: dict[str, dict[str, Any]] = {}
    for sc, sdata in state_stats.items():
        s_errs = sdata["errors_pct"]
        stratified[sc] = {
            "total": sdata["total"],
            "completed": sdata["completed"],
            "abstained": sdata["abstained"],
            "mdape": round(statistics.median(s_errs), 2) if s_errs else None,
            "sample_size_adequate": sdata["total"] >= 20,
        }

    warning: str | None = None
    if total < 30:
        warning = (
            f"Evaluation sample size (n={total}) is limited. Per GEMINI.md Section 7, "
            "metrics must not be cited as strong real-world generalization claims without a larger independent evaluation set."
        )

    return EvaluationMetrics(
        sample_size=total,
        completed_count=completed,
        abstained_count=abstained,
        human_review_count=needs_review,
        coverage_rate=cov_rate,
        abstention_rate=abs_rate,
        human_review_rate=rev_rate,
        mdape=mdape,
        mape=mape,
        large_error_rate_20pct=large_errors,
        stratified_by_state=stratified,
        sample_size_limitation_warning=warning,
    )
