"""Valuation and Evaluation Module for Indian Residential Property Valuation.

**Canonical status (F-10):** this is the stricter GEMINI engine and the *migration target*, but it
is **not** the currently-wired canonical path. The live AVM is ``app.property`` (it holds the F-01
synthetic gate and F-02 market-index gating). Before promoting this engine, port those controls
here and move ``PropertyAgent`` over — see ``docs/architecture/canonical_pipeline.md``.

Enforces GEMINI.md Section 4.7, Section 6, Section 7, Section 8, and Section 10 Step 6:
- Robust comparable selection and stepwise proximity expansion.
- Locality-aware MAD outlier detection.
- Transparent weighted median estimation.
- Empirical uncertainty bounds and evidence confidence scoring.
- Leakage-free evaluation holdout framework (temporal and locality holdouts with split manifests).
"""

from app.valuation.comps import (
    ComparableSelector,
    EligibleComparable,
    SubjectPropertyInput,
    coerce_to_uuid,
)
from app.valuation.confidence import (
    ConfidenceAssessment,
    calculate_weighted_percentile,
    compute_confidence_and_bounds,
)
from app.valuation.estimate import (
    METHOD_VERSION,
    ValuationEngine,
    calculate_weighted_median,
)
from app.valuation.evaluation import (
    EvaluationMetrics,
    SplitManifest,
    create_locality_holdout_split,
    create_temporal_split,
    run_benchmark_evaluation,
)
from app.valuation.outliers import (
    DEFAULT_OUTLIER_THRESHOLD,
    MIN_GROUP_SIZE_FOR_OUTLIERS,
    ROBUST_OUTLIER_VERSION,
    calculate_median_and_mad,
    evaluate_robust_outliers,
)

__all__ = [
    "ComparableSelector",
    "EligibleComparable",
    "SubjectPropertyInput",
    "coerce_to_uuid",
    "ConfidenceAssessment",
    "calculate_weighted_percentile",
    "compute_confidence_and_bounds",
    "ValuationEngine",
    "calculate_weighted_median",
    "METHOD_VERSION",
    "evaluate_robust_outliers",
    "calculate_median_and_mad",
    "ROBUST_OUTLIER_VERSION",
    "DEFAULT_OUTLIER_THRESHOLD",
    "MIN_GROUP_SIZE_FOR_OUTLIERS",
    "create_temporal_split",
    "create_locality_holdout_split",
    "run_benchmark_evaluation",
    "SplitManifest",
    "EvaluationMetrics",
]
