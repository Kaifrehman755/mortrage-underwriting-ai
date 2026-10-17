"""Assessor and registration department CSV provider.

Implements Playbook Section 3a, 5, 14.5 (CSV loader, reject logging, and normalization).
"""

import csv
import io
import logging
from typing import Any
from uuid import NAMESPACE_DNS, uuid5

from app.property.jurisdictions import get_jurisdiction
from app.property.normalize import clean_raw_record, haversine_km
from app.property.provider import CompProvider, ProviderUnavailable
from app.property.schemas import ComparableRecord, SubjectProperty

logger = logging.getLogger(__name__)


class AssessorCsvProvider(CompProvider):
    """Loads and filters verified property transaction records from CSV files."""

    def __init__(self, csv_data: str | list[dict[str, Any]], provider_name: str = "assessor_csv"):
        self.provider_name = provider_name
        self.raw_rows: list[dict[str, Any]] = []
        self.rejected_records: list[dict[str, Any]] = []

        if isinstance(csv_data, str):
            reader = csv.DictReader(io.StringIO(csv_data))
            self.raw_rows = [dict(row) for row in reader]
        else:
            self.raw_rows = list(csv_data)

    def fetch_comps(
        self,
        subject: SubjectProperty,
        radius_km: float = 3.0,
        months: int = 12,
        filters: dict[str, Any] | None = None,
    ) -> list[ComparableRecord]:
        """Fetch matching comps from CSV records with quality filtering.

        Rejects invalid rows and logs reasons.
        """
        if not self.raw_rows:
            return []

        try:
            jurisdiction = get_jurisdiction(subject.state_code)
        except ValueError as e:
            raise ProviderUnavailable(self.provider_name, str(e)) from e

        valid_comps: list[ComparableRecord] = []

        for row in self.raw_rows:
            # Enforce state isolation
            row_state = str(row.get("state_code", "")).strip().upper()
            if row_state != subject.state_code:
                continue

            cleaned, reasons = clean_raw_record(row, jurisdiction)
            if not cleaned:
                self.rejected_records.append({"row": row, "reasons": reasons})
                logger.warning(f"Rejected assessor row {row.get('record_id', 'unknown')}: {reasons}")
                continue

            # Check distance
            dist = haversine_km(subject.lat, subject.lon, cleaned["lat"], cleaned["lon"])
            if dist > radius_km:
                continue

            rec_id = str(cleaned.get("record_id") or cleaned.get("provider_record_id") or f"CSV-{len(valid_comps)}")
            comp_uuid = str(uuid5(NAMESPACE_DNS, rec_id))

            record = ComparableRecord(
                comp_id=comp_uuid,
                source_id=2,
                source_name=self.provider_name,
                provider_record_id=rec_id,
                address=cleaned.get("address", "Unknown Address"),
                locality=cleaned.get("locality", "Unknown Locality"),
                city=cleaned.get("city", subject.city),
                state_code=subject.state_code,
                property_type=cleaned.get("property_type", "apartment"),
                sale_price=cleaned["sale_price"],
                currency="INR",
                sale_date=cleaned["sale_date"],
                living_area_sqft=cleaned["living_area_sqft"],
                price_per_sqft=cleaned["price_per_sqft"],
                price_type=cleaned.get("price_type", "registered_deed"),
                area_basis=cleaned.get("area_basis", "carpet"),
                license_scope="public_records",
                clean_flags=cleaned.get("clean_flags", []),
                distance_km=dist,
                is_synthetic=False,
                raw=cleaned,
            )
            valid_comps.append(record)

        valid_comps.sort(key=lambda c: (c.distance_km if c.distance_km is not None else 999.0))
        return valid_comps
