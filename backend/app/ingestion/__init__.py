"""Ingestion pipeline package.

Enforces GEMINI.md Section 4, Section 5, Section 6, and Section 10 Step 3.
"""

from app.ingestion.circle_rates import (
    CircleRateIngestionResult,
    CircleRateIngestor,
    CircleRateRejection,
    IngestionError,
    ParseOutcome,
    resolve_intake_path,
    validate_ingestion_url,
)
from app.ingestion.deduplicate import DeduplicationIndex, generate_reference_rate_key
from app.ingestion.normalize import (
    SQM_TO_SQFT,
    SQYD_TO_SQFT,
    calculate_price_per_sqft,
    normalize_area_sqft,
    normalize_inr_price,
)
from app.ingestion.provider import (
    BaseIngestionProvider,
    ReferenceRateFileProvider,
    compute_sha256,
)
from app.ingestion.quarantine import (
    IngestionRunAccounting,
    QuarantineReason,
    QuarantineRecord,
)
from app.ingestion.registry import (
    SourceApprovalError,
    SourceRegistry,
    default_registry,
    generate_source_id,
)
from app.ingestion.schemas import CircleRateRecord
from app.ingestion.validate import (
    validate_reference_rate_row,
    validate_transaction_row,
)

__all__ = [
    "CircleRateIngestor",
    "IngestionError",
    "CircleRateRecord",
    "CircleRateIngestionResult",
    "CircleRateRejection",
    "ParseOutcome",
    "resolve_intake_path",
    "validate_ingestion_url",
    "BaseIngestionProvider",
    "ReferenceRateFileProvider",
    "compute_sha256",
    "SourceRegistry",
    "default_registry",
    "SourceApprovalError",
    "generate_source_id",
    "DeduplicationIndex",
    "generate_reference_rate_key",
    "validate_reference_rate_row",
    "validate_transaction_row",
    "QuarantineReason",
    "QuarantineRecord",
    "IngestionRunAccounting",
    "normalize_inr_price",
    "normalize_area_sqft",
    "calculate_price_per_sqft",
    "SQM_TO_SQFT",
    "SQYD_TO_SQFT",
]
