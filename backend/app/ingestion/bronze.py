"""Bronze-layer helpers for untouched source records and dedupe fingerprints.

Playbook sections 14.5 and 19.3:

* collectors save exactly what they fetched, plus the file hash;
* rows with no stable provider ID are de-duplicated with a documented fingerprint;
* the fingerprint never includes buyer, seller, or other personal data.

The fingerprint recipe is intentionally explicit. Changing it requires a schema
or ingestion migration, because it is part of the uniqueness key.
"""

from __future__ import annotations

import hashlib
from datetime import date
from typing import Any, Literal
from uuid import UUID

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.raw_record import RawRecord as RawRecordModel

RecordType = Literal[
    "registered_transaction", "guideline_value", "land_record", "listing", "survey"
]

ALLOWED_RECORD_TYPES: frozenset[str] = frozenset(
    {
        "registered_transaction",
        "guideline_value",
        "land_record",
        "listing",
        "survey",
    }
)


def build_record_fingerprint(
    *,
    source_id: UUID,
    record_type: RecordType,
    document_or_registration_number: str | None = None,
    sub_registrar_office: str | None = None,
    registration_date: date | str | None = None,
    recorded_consideration_inr: float | str | None = None,
    area_sqft: float | str | None = None,
) -> str:
    """Return the SHA-256 fingerprint of documented stable source fields.

    At least one of document number or the registration/consideration/area tuple
    must be present. Empty values are rejected so two unrelated incomplete rows
    cannot collapse into the same fingerprint.

    Buyer and seller names are intentionally not parameters. Do not add them.
    """
    if record_type not in ALLOWED_RECORD_TYPES:
        raise ValueError(f"unsupported record_type: {record_type}")

    normalized = {
        "source_id": str(source_id),
        "record_type": record_type,
        "document_or_registration_number": _clean(
            document_or_registration_number
        ),
        "sub_registrar_office": _clean(sub_registrar_office),
        "registration_date": _clean(registration_date),
        "recorded_consideration_inr": _clean(recorded_consideration_inr),
        "area_sqft": _clean(area_sqft),
    }
    if not normalized["document_or_registration_number"] and not any(
        normalized[key]
        for key in (
            "registration_date",
            "recorded_consideration_inr",
            "area_sqft",
        )
    ):
        raise ValueError(
            "cannot fingerprint a record with no stable identifier or "
            "registration/consideration/area fields"
        )

    canonical = "\x1f".join(
        f"{key}={normalized[key]}"
        for key in (
            "source_id",
            "record_type",
            "document_or_registration_number",
            "sub_registrar_office",
            "registration_date",
            "recorded_consideration_inr",
            "area_sqft",
        )
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class RawRecordRepository:
    """Persist bronze rows idempotently by ``(source, type, fingerprint)``."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_raw_record(
        self,
        *,
        source_id: UUID,
        payload: dict[str, Any],
        record_type: RecordType,
        record_fingerprint: str,
        file_sha256: str | None = None,
        status: str = "new",
    ) -> bool:
        """Insert the raw record or leave an existing duplicate untouched.

        Returns ``True`` when a new row was inserted.
        """
        if not _is_sha256(record_fingerprint):
            raise ValueError("record_fingerprint must be a 64-character SHA-256 hex")
        if file_sha256 is not None and not _is_sha256(file_sha256):
            raise ValueError("file_sha256 must be a 64-character SHA-256 hex")
        if not payload:
            raise ValueError("raw payload must not be empty")
        if record_type not in ALLOWED_RECORD_TYPES:
            raise ValueError(f"unsupported record_type: {record_type}")

        statement = (
            pg_insert(RawRecordModel)
            .values(
                source_id=source_id,
                payload=payload,
                file_sha256=file_sha256,
                status=status,
                record_type=record_type,
                record_fingerprint=record_fingerprint,
            )
            .on_conflict_do_nothing(constraint="raw_record_dedupe")
        )
        result = await self.session.execute(statement)
        await self.session.flush()
        return bool(getattr(result, "rowcount", 0))


def _clean(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, date):
        return value.isoformat()
    return str(value).strip().lower()


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(char in "0123456789abcdef" for char in value)
