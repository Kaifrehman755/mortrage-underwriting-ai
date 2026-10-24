"""Base Ingestion Provider and Concrete Permitted Importers.

Enforces GEMINI.md Section 4, Section 6, and Section 10 Step 3:
- Enforces source approval gate before running ingestion.
- Computes and preserves SHA-256 snapshot hash for provenance.
- Routes invalid records to quarantine with reason codes.
- Idempotent deduplication handling.
- Strict row accounting invariant: rows_received == rows_accepted + rows_quarantined + rows_duplicate + rows_rejected.
"""

from __future__ import annotations

import csv
import hashlib
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.ingestion.deduplicate import DeduplicationIndex
from app.ingestion.quarantine import (
    IngestionRunAccounting,
    QuarantineRecord,
)
from app.ingestion.registry import SourceApprovalError
from app.ingestion.validate import validate_reference_rate_row
from app.schemas.source import ApprovalStatus, DataSourceRead
from app.schemas.transaction import ReferenceRateCreate

BUILD_VERSION = "1.0.0"


def compute_sha256(content: bytes | str) -> str:
    """Compute SHA-256 hex digest of file bytes or text string."""
    data = content.encode("utf-8") if isinstance(content, str) else content
    return hashlib.sha256(data).hexdigest()


class BaseIngestionProvider(ABC):
    """Abstract base provider for authorized ingestion pipelines."""

    def __init__(
        self,
        source: DataSourceRead,
        dedup_index: DeduplicationIndex | None = None,
        quarantine_dir: Path | str | None = None,
    ) -> None:
        self.source = source
        self.dedup_index = dedup_index or DeduplicationIndex()
        self.quarantine_dir = Path(quarantine_dir) if quarantine_dir else (
            Path(__file__).resolve().parents[3] / "data" / "quarantine"
        )
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)

    def check_approval_gate(self) -> None:
        """Verify that source is approved prior to data collection or import."""
        if self.source.approval_status != ApprovalStatus.APPROVED:
            raise SourceApprovalError(
                f"Source '{self.source.source_name}' ({self.source.state_code}) is not approved. "
                f"Current status: '{self.source.approval_status.value}'. Ingestion blocked by Source Approval Gate."
            )

    @abstractmethod
    def ingest_file(
        self, file_path: Path | str
    ) -> tuple[list[Any], IngestionRunAccounting, list[QuarantineRecord]]:
        """Ingest a file snapshot. Returns (accepted_records, accounting, quarantine_records)."""


class ReferenceRateFileProvider(BaseIngestionProvider):
    """Permitted file importer for official reference rate schedules (e.g. UP circle rates)."""

    def ingest_file(
        self, file_path: Path | str
    ) -> tuple[list[ReferenceRateCreate], IngestionRunAccounting, list[QuarantineRecord]]:
        # 1. Gate check
        self.check_approval_gate()

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Source snapshot file not found: {path}")

        # 2. Compute SHA-256 snapshot hash
        raw_bytes = path.read_bytes()
        snapshot_hash = compute_sha256(raw_bytes)

        run_id = uuid4()
        started_at = datetime.now(UTC)

        accepted_records: list[ReferenceRateCreate] = []
        quarantine_records: list[QuarantineRecord] = []
        rows_received = 0
        rows_accepted = 0
        rows_quarantined = 0
        rows_duplicate = 0
        rows_rejected = 0

        # 3. Read and process rows
        with open(path, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows_received += 1

                # Clean header keys
                cleaned_row = {
                    str(k).strip(): v for k, v in row.items() if k is not None
                }

                # Validate and normalize
                model, quarantine_rec = validate_reference_rate_row(
                    raw_row=cleaned_row,
                    source_id=self.source.source_id,
                    run_id=run_id,
                    source_snapshot_hash=snapshot_hash,
                )

                if quarantine_rec is not None:
                    rows_quarantined += 1
                    quarantine_records.append(quarantine_rec)
                    continue

                # F-15: validators only ever return (model, None) or (None, quarantine),
                # so rows_rejected stays a reserved accounting field. Fail loudly if that
                # contract is ever broken rather than silently mis-counting the row.
                if model is None:  # pragma: no cover - defensive, unreachable today
                    raise RuntimeError(
                        "Validator contract violated: returned neither a model nor a quarantine record."
                    )

                # Deduplication and idempotency check
                if self.dedup_index.check_and_register(model):
                    rows_duplicate += 1
                    continue

                # Successfully accepted
                rows_accepted += 1
                accepted_records.append(model)

        # 4. Finalize Ingestion Run Accounting
        finished_at = datetime.now(UTC)
        accounting = IngestionRunAccounting(
            run_id=run_id,
            source_id=self.source.source_id,
            started_at=started_at,
            finished_at=finished_at,
            build_version=BUILD_VERSION,
            source_snapshot_hash=snapshot_hash,
            rows_received=rows_received,
            rows_accepted=rows_accepted,
            rows_quarantined=rows_quarantined,
            rows_duplicate=rows_duplicate,
            rows_rejected=rows_rejected,
        )

        # 5. Persist quarantine log if any rows were quarantined
        if quarantine_records:
            quarantine_file = self.quarantine_dir / f"quarantine_{run_id}.jsonl"
            with open(quarantine_file, mode="w", encoding="utf-8") as qf:
                for qr in quarantine_records:
                    qf.write(qr.model_dump_json() + "\n")

        return accepted_records, accounting, quarantine_records
