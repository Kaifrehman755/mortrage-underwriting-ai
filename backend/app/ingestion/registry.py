"""Source Registry and Approval Gatekeeper.

Enforces GEMINI.md Section 3 and Section 10 Step 3:
- Tracks provider identity, permissions, and reliability.
- Gatekeeper: Prevents ingestion from unapproved or restricted sources.
- Reads candidate source statuses from data/source_readiness.csv.
"""

from __future__ import annotations

import csv
from datetime import UTC, datetime
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid5

from app.schemas.source import ApprovalStatus, DataSourceRead, SourceType

SOURCE_REGISTRY_CSV = Path(__file__).resolve().parents[3] / "data" / "source_readiness.csv"


class SourceApprovalError(Exception):
    """Raised when an unapproved, restricted, or unknown source is accessed for ingestion."""


def generate_source_id(state_code: str, source_name: str) -> UUID:
    """Deterministic UUID for a source based on its state and name."""
    identifier = f"data-source:{state_code.strip().upper()}:{source_name.strip()}"
    return uuid5(NAMESPACE_URL, identifier)


class SourceRegistry:
    """Registry managing data sources and approval status checks."""

    def __init__(self, csv_path: Path | str | None = None) -> None:
        self.csv_path = Path(csv_path) if csv_path else SOURCE_REGISTRY_CSV
        self._sources: dict[tuple[str, str], DataSourceRead] = {}
        self.reload()

    def reload(self) -> None:
        """Reload sources from the source_readiness.csv file."""
        self._sources.clear()
        if not self.csv_path.exists():
            return

        with open(self.csv_path, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                state = str(row.get("state_code", "")).strip().upper()
                name = str(row.get("source_name", "")).strip()
                if not state or not name:
                    continue

                decision = str(row.get("decision", "pending_review")).strip().lower()
                approval_enum = (
                    ApprovalStatus.APPROVED if decision == "approved"
                    else ApprovalStatus.REJECTED if decision == "rejected"
                    else ApprovalStatus.PENDING_REVIEW
                )

                acc_method = str(row.get("access_method", "manual authorized export")).strip()
                cat = str(row.get("data_category", "")).strip()
                source_type = (
                    SourceType.SYNTHETIC_TEST if "synthetic" in name.lower() or state == "ALL"
                    else SourceType.GOVERNMENT if "igrs" in name.lower() or "kaveri" in name.lower() or "easr" in name.lower()
                    else SourceType.MANUAL_AUTHORIZED_IMPORT
                )

                source_id = generate_source_id(state, name)
                source_record = DataSourceRead(
                    source_id=source_id,
                    source_name=name,
                    state_code=state,
                    source_type=source_type,
                    official_url=str(row.get("source_url", "")).strip(),
                    access_method=acc_method,
                    license_scope=f"Category: {cat}; Commercial allowed: {row.get('commercial_use_allowed', 'unknown')}",
                    approval_status=approval_enum,
                    last_checked_at=datetime.now(UTC),
                )
                self._sources[(state, name)] = source_record

    def get_source(self, state_code: str, source_name: str) -> DataSourceRead | None:
        """Lookup a registered data source."""
        return self._sources.get((state_code.strip().upper(), source_name.strip()))

    def list_sources(self) -> list[DataSourceRead]:
        """Return all registered data sources."""
        return list(self._sources.values())

    def verify_approval(self, state_code: str, source_name: str) -> DataSourceRead:
        """Verify that a source is registered and formally approved.

        Raises SourceApprovalError if the source is not approved.
        """
        source = self.get_source(state_code, source_name)
        if not source:
            raise SourceApprovalError(
                f"Source '{source_name}' for state '{state_code}' is not registered in source register."
            )
        if source.approval_status != ApprovalStatus.APPROVED:
            raise SourceApprovalError(
                f"Source '{source_name}' ({state_code}) has status '{source.approval_status.value}'. "
                "Ingestion requires formal approval decision."
            )
        return source


# Global default registry instance
default_registry = SourceRegistry()
