"""Validation and quarantine dispatch for raw ingestion rows.

Enforces GEMINI.md Section 4, Section 5, and Section 6:
- Reason-coded validation (MISSING_PRICE, MISSING_AREA, INVALID_UNIT, etc.).
- Never silently drops or imputes data.
- Constructs valid canonical models or QuarantineRecord instances.
"""

from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

from app.ingestion.normalize import (
    SQM_TO_SQFT,
    SQYD_TO_SQFT,
    normalize_inr_price,
)
from app.ingestion.quarantine import QuarantineReason, QuarantineRecord
from app.schemas.transaction import (
    PriceType,
    PropertyTransactionCreate,
    ReferenceRateCreate,
    TransactionVerificationStatus,
)


def validate_reference_rate_row(
    raw_row: dict[str, Any],
    source_id: UUID,
    run_id: UUID,
    source_snapshot_hash: str,
) -> tuple[ReferenceRateCreate | None, QuarantineRecord | None]:
    """Validate and normalize a raw circle rate / reference rate row.

    Returns (validated_model, None) on success or (None, quarantine_record) on failure.
    """
    raw_ref = f"{raw_row.get('locality', 'unknown')}:{raw_row.get('property_category', 'unknown')}"

    # 1. Locality & state check
    state_code = str(raw_row.get("state_code", "")).strip().upper()
    district = str(raw_row.get("district", "")).strip()
    locality = str(raw_row.get("locality", "")).strip()
    if not state_code or not district or not locality:
        return None, QuarantineRecord(
            run_id=run_id,
            source_id=source_id,
            reason_code=QuarantineReason.PROVENANCE_MISSING,
            reason_detail="Missing state_code, district, or locality name",
            raw_record_ref=raw_ref,
        )

    # 2. Rate validation
    raw_rate = raw_row.get("rate_raw") or raw_row.get("rate_per_sqm") or raw_row.get("rate")
    if raw_rate is None or str(raw_rate).strip() == "":
        return None, QuarantineRecord(
            run_id=run_id,
            source_id=source_id,
            reason_code=QuarantineReason.MISSING_PRICE,
            reason_detail="Circle rate value is missing or null",
            raw_record_ref=raw_ref,
        )

    try:
        rate_val = float(str(raw_rate).replace(",", "").replace("₹", "").strip())
        if rate_val <= 0:
            raise ValueError("Rate must be greater than zero")
    except (ValueError, TypeError) as exc:
        return None, QuarantineRecord(
            run_id=run_id,
            source_id=source_id,
            reason_code=QuarantineReason.MISSING_PRICE,
            reason_detail=f"Circle rate value is non-positive or unparseable: {exc}",
            raw_record_ref=raw_ref,
        )

    # 3. Unit validation & normalization
    raw_unit = str(raw_row.get("rate_unit_raw", "per_sqm")).strip().lower()
    if raw_unit in ("per_sqm", "per_sq_m", "sqm", "sq.m"):
        rate_normalized = round(rate_val / SQM_TO_SQFT, 2)
    elif raw_unit in ("per_sqft", "per_sq_ft", "sqft", "sq.ft"):
        rate_normalized = round(rate_val, 2)
    elif raw_unit in ("per_sqyd", "sqyd", "gaj"):
        rate_normalized = round(rate_val / SQYD_TO_SQFT, 2)
    else:
        return None, QuarantineRecord(
            run_id=run_id,
            source_id=source_id,
            reason_code=QuarantineReason.INVALID_UNIT,
            reason_detail=f"Unrecognized reference rate unit: '{raw_unit}'",
            raw_record_ref=raw_ref,
        )

    # 4. Effective date validation
    eff_from_raw = raw_row.get("effective_from") or raw_row.get("effective_year")
    if not eff_from_raw:
        return None, QuarantineRecord(
            run_id=run_id,
            source_id=source_id,
            reason_code=QuarantineReason.INVALID_DATE,
            reason_detail="Missing effective_from date or notification year",
            raw_record_ref=raw_ref,
        )

    eff_from: date
    if isinstance(eff_from_raw, date):
        eff_from = eff_from_raw
    elif isinstance(eff_from_raw, int) or (isinstance(eff_from_raw, str) and str(eff_from_raw).isdigit() and len(str(eff_from_raw)) == 4):
        year = int(eff_from_raw)
        if year < 1990 or year > 2035:
            return None, QuarantineRecord(
                run_id=run_id,
                source_id=source_id,
                reason_code=QuarantineReason.INVALID_DATE,
                reason_detail=f"Effective year {year} is out of allowable range [1990, 2035]",
                raw_record_ref=raw_ref,
            )
        eff_from = date(year, 4, 1)
    else:
        try:
            eff_from = date.fromisoformat(str(eff_from_raw)[:10])
        except ValueError:
            return None, QuarantineRecord(
                run_id=run_id,
                source_id=source_id,
                reason_code=QuarantineReason.INVALID_DATE,
                reason_detail=f"Unable to parse effective_from date '{eff_from_raw}'",
                raw_record_ref=raw_ref,
            )

    # 5. Property category
    prop_cat = str(raw_row.get("property_category", "residential_flat")).strip().lower()
    if not prop_cat:
        prop_cat = "residential_flat"

    # 6. Source URL
    source_url = str(raw_row.get("source_url", "")).strip()
    if not source_url:
        return None, QuarantineRecord(
            run_id=run_id,
            source_id=source_id,
            reason_code=QuarantineReason.PROVENANCE_MISSING,
            reason_detail="Missing source_url for provenance audit",
            raw_record_ref=raw_ref,
        )

    model = ReferenceRateCreate(
        source_id=source_id,
        state_code=state_code,
        district=district,
        locality=locality,
        property_category=prop_cat,
        rate_raw=rate_val,
        rate_unit_raw=raw_unit,
        rate_inr_per_sqft=rate_normalized,
        effective_from=eff_from,
        effective_to=date.fromisoformat(str(raw_row["effective_to"])[:10]) if raw_row.get("effective_to") else None,
        published_at=date.fromisoformat(str(raw_row["published_at"])[:10]) if raw_row.get("published_at") else None,
        source_url=source_url,
        source_record_hash=source_snapshot_hash[:32],
    )
    return model, None


def validate_transaction_row(
    raw_row: dict[str, Any],
    source_id: UUID,
    run_id: UUID,
    source_snapshot_hash: str,
) -> tuple[PropertyTransactionCreate | None, QuarantineRecord | None]:
    """Validate a property transaction row against safety principles."""
    tx_id_raw = str(raw_row.get("source_transaction_id", "")).strip()
    raw_ref = tx_id_raw or "TX_UNKNOWN"

    if not tx_id_raw:
        return None, QuarantineRecord(
            run_id=run_id,
            source_id=source_id,
            reason_code=QuarantineReason.PROVENANCE_MISSING,
            reason_detail="Missing stable source_transaction_id",
            raw_record_ref=raw_ref,
        )

    # Validate price
    price_val = normalize_inr_price(raw_row.get("transaction_price_raw"), raw_row.get("transaction_price_unit_raw"))
    if price_val is None or price_val <= 0:
        return None, QuarantineRecord(
            run_id=run_id,
            source_id=source_id,
            source_record_id=tx_id_raw,
            reason_code=QuarantineReason.MISSING_PRICE,
            reason_detail="Missing, zero, or unparseable transaction consideration",
            raw_record_ref=raw_ref,
        )

    # Validate date
    date_raw = raw_row.get("transaction_date")
    if not date_raw:
        return None, QuarantineRecord(
            run_id=run_id,
            source_id=source_id,
            source_record_id=tx_id_raw,
            reason_code=QuarantineReason.INVALID_DATE,
            reason_detail="Missing transaction_date",
            raw_record_ref=raw_ref,
        )
    try:
        tx_date = date.fromisoformat(str(date_raw)[:10]) if not isinstance(date_raw, date) else date_raw
    except ValueError:
        return None, QuarantineRecord(
            run_id=run_id,
            source_id=source_id,
            source_record_id=tx_id_raw,
            reason_code=QuarantineReason.INVALID_DATE,
            reason_detail=f"Malformed transaction date '{date_raw}'",
            raw_record_ref=raw_ref,
        )

    # Check price type: asking price cannot be ingested as sale consideration
    price_type_str = str(raw_row.get("price_type", "sale_consideration")).strip().lower()
    if price_type_str == "asking":
        return None, QuarantineRecord(
            run_id=run_id,
            source_id=source_id,
            source_record_id=tx_id_raw,
            reason_code=QuarantineReason.PRICE_TYPE_NOT_ELIGIBLE,
            reason_detail="Asking prices must never be ingested as sale transactions",
            raw_record_ref=raw_ref,
        )

    # Provenance: never fabricate a fallback source URL (F-16 / rules R1, R5).
    source_url = str(raw_row.get("source_url", "")).strip()
    if not source_url:
        return None, QuarantineRecord(
            run_id=run_id,
            source_id=source_id,
            source_record_id=tx_id_raw,
            reason_code=QuarantineReason.PROVENANCE_MISSING,
            reason_detail="Missing source_url for provenance audit",
            raw_record_ref=raw_ref,
        )

    model = PropertyTransactionCreate(
        source_id=source_id,
        source_transaction_id=tx_id_raw,
        transaction_date=tx_date,
        transaction_price_raw=price_val,
        transaction_price_unit_raw=str(raw_row.get("transaction_price_unit_raw", "INR")),
        transaction_price_inr=price_val,
        price_type=PriceType.SALE_CONSIDERATION if price_type_str == "sale_consideration" else PriceType.UNKNOWN,
        transaction_verification_status=TransactionVerificationStatus.VERIFIED if raw_row.get("verified") else TransactionVerificationStatus.UNVERIFIED,
        source_url=source_url,
        source_record_hash=source_snapshot_hash[:32],
    )
    return model, None
