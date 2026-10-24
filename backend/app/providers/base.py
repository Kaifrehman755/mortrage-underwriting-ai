"""Base State Provider Interface and Abstractions.

Enforces GEMINI.md Section 3, Section 5, and Section 10 Step 5:
- Preserves raw values, units, and source-specific transformations.
- Enforces the Source Approval Gate prior to any data access.
- Clearly flags transaction data unavailability when bulk transaction access is restricted.
- Guarantees that unsupported states return explicit errors rather than fabricated records.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

from app.ingestion.provider import ReferenceRateFileProvider
from app.ingestion.quarantine import IngestionRunAccounting, QuarantineRecord
from app.ingestion.registry import default_registry
from app.schemas.source import DataSourceRead
from app.schemas.transaction import ReferenceRateCreate


class StateReadinessStatus(StrEnum):
    """Readiness classification for state data providers."""

    PILOT_REFERENCE_RATE_ONLY = "pilot_reference_rate_only"
    PENDING_PERMISSION = "pending_permission"
    RESTRICTED = "restricted"
    UNSUPPORTED = "unsupported"


class UnsupportedStateError(Exception):
    """Raised when an operation is requested for an unsupported state."""


class TransactionDataUnavailableError(Exception):
    """Raised when real transaction-price evidence is requested from a state whose deed search is restricted."""


@dataclass(frozen=True)
class StateProviderMetadata:
    """Documented metadata for a state-specific valuation data adapter."""

    state_code: str
    state_name: str
    reference_rate_local_name: str  # e.g. "Circle Rate", "Ready Reckoner", "Guidance Value", "Market Value"
    native_area_unit: str  # e.g. "per_sqm", "per_sqft", "per_sqyd"
    official_portal_url: str
    reference_rate_source_name: str
    transaction_source_name: str
    reference_rate_approved: bool
    transaction_data_approved: bool
    transaction_restriction_reason: str
    supported_districts: list[str] = field(default_factory=list)
    raw_field_mappings: dict[str, str] = field(default_factory=dict)


class BaseStateProvider(ABC):
    """Abstract base provider for state-level property data adapters."""

    def __init__(self, metadata: StateProviderMetadata) -> None:
        self._metadata = metadata

    @property
    def metadata(self) -> StateProviderMetadata:
        """State provider metadata."""
        return self._metadata

    @property
    def state_code(self) -> str:
        """State code (e.g. 'UP', 'MH', 'KA', 'TS')."""
        return self._metadata.state_code

    def get_reference_rate_source_metadata(self) -> DataSourceRead:
        """Retrieve and verify registered data source for administrative reference rates."""
        source = default_registry.get_source(
            self.state_code, self._metadata.reference_rate_source_name
        )
        if not source:
            raise UnsupportedStateError(
                f"Reference rate source '{self._metadata.reference_rate_source_name}' "
                f"for state '{self.state_code}' is not registered."
            )
        return source

    def ingest_reference_rates(
        self, file_path: Path | str, quarantine_dir: Path | str | None = None
    ) -> tuple[list[ReferenceRateCreate], IngestionRunAccounting, list[QuarantineRecord]]:
        """Ingest official reference rate schedule file via the approved canonical pipeline."""
        source = self.get_reference_rate_source_metadata()
        provider = ReferenceRateFileProvider(source=source, quarantine_dir=quarantine_dir)
        return provider.ingest_file(file_path)

    def get_transaction_access_status(self) -> dict[str, Any]:
        """Return the current permission and access readiness status for real transaction deeds."""
        return {
            "state_code": self.state_code,
            "transaction_source_name": self._metadata.transaction_source_name,
            "transaction_data_approved": self._metadata.transaction_data_approved,
            "restriction_reason": self._metadata.transaction_restriction_reason,
            "next_action": "Do not scrape. Await official bulk open data API or authorized data aggregator contract.",
        }

    def require_transaction_data(self) -> None:
        """Enforces GEMINI.md Rules 2, 5, 6, 7: Blocks transaction queries if access is restricted."""
        if not self._metadata.transaction_data_approved:
            raise TransactionDataUnavailableError(
                f"Real transaction deed data is unavailable for state '{self.state_code}'. "
                f"Reason: {self._metadata.transaction_restriction_reason}. "
                "Per GEMINI.md safety principles, circle rates must never be used as sale prices, "
                "and unverified portals must not be scraped."
            )

    @abstractmethod
    def document_source_transformations(self) -> dict[str, Any]:
        """Return documented transformation logic and raw field mappings."""
