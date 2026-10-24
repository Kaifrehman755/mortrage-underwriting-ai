"""Deduplication and Idempotency Handling.

Enforces GEMINI.md Section 6:
- Deduplication using stable source IDs and natural unique constraints.
- Idempotency: Repeating an import of the same snapshot must not duplicate records.
- Clearly distinguishes duplicate rows from accepted, rejected, and quarantined rows.
"""

from __future__ import annotations

import hashlib

from app.schemas.property import PropertyRecordCreate
from app.schemas.transaction import PropertyTransactionCreate, ReferenceRateCreate


def generate_reference_rate_key(rate: ReferenceRateCreate) -> str:
    """Natural key for reference rates: (state, district, locality, category, effective_from)."""
    raw_key = (
        f"{rate.state_code.upper()}:{rate.district.lower()}:{rate.locality.lower()}:"
        f"{rate.property_category.lower()}:{rate.effective_from.isoformat()}"
    )
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def generate_transaction_key(tx: PropertyTransactionCreate) -> str:
    """Stable key for transactions: (source_id, source_transaction_id)."""
    raw_key = f"{tx.source_id}:{tx.source_transaction_id}"
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def generate_property_key(prop: PropertyRecordCreate) -> str:
    """Stable key for properties: (source_id, source_record_id)."""
    raw_key = f"{prop.source_id}:{prop.source_record_id}"
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


class DeduplicationIndex:
    """In-memory or persistent fingerprint index for idempotent ingestion runs."""

    def __init__(self, initial_keys: set[str] | None = None) -> None:
        self._seen_keys: set[str] = set(initial_keys) if initial_keys else set()

    def is_duplicate(self, record: ReferenceRateCreate | PropertyTransactionCreate | PropertyRecordCreate) -> bool:
        """Check if record has already been ingested or processed in this or prior runs."""
        key = self.compute_key(record)
        return key in self._seen_keys

    def register(self, record: ReferenceRateCreate | PropertyTransactionCreate | PropertyRecordCreate) -> None:
        """Register record key as seen."""
        key = self.compute_key(record)
        self._seen_keys.add(key)

    def check_and_register(self, record: ReferenceRateCreate | PropertyTransactionCreate | PropertyRecordCreate) -> bool:
        """Atomically test and register. Returns True if was duplicate, False if newly registered."""
        key = self.compute_key(record)
        if key in self._seen_keys:
            return True
        self._seen_keys.add(key)
        return False

    @staticmethod
    def compute_key(record: ReferenceRateCreate | PropertyTransactionCreate | PropertyRecordCreate) -> str:
        if isinstance(record, ReferenceRateCreate):
            return generate_reference_rate_key(record)
        if isinstance(record, PropertyTransactionCreate):
            return generate_transaction_key(record)
        if isinstance(record, PropertyRecordCreate):
            return generate_property_key(record)
        raise TypeError(f"Unsupported record type for deduplication: {type(record)}")

    def __len__(self) -> int:
        return len(self._seen_keys)
