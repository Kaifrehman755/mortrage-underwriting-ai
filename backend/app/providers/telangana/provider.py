"""Telangana (TS) State Property Provider Adapter.

Enforces GEMINI.md Section 3 and Section 10 Step 5:
- Official Source: IGRS Telangana Market Value & Unit Rates (https://registration.telangana.gov.in/).
- Candidate Data Category: reference_rate (IGRS TS market value schedule). Provenance UNVERIFIED (F-03): source approval is pending_review and the local snapshot is a synthetic dev fixture.
- Native Area Unit: per_sqyd (converted to per_sqft via 9.0 factor).
- Transaction Deed Access: RESTRICTED/REJECTED. IGRS registered deed portal terms prohibit scraping.
"""

from typing import Any

from app.providers.base import BaseStateProvider, StateProviderMetadata


class TelanganaProvider(BaseStateProvider):
    """Telangana state provider for IGRS Basic Market Values and jurisdiction rules."""

    def __init__(self) -> None:
        metadata = StateProviderMetadata(
            state_code="TS",
            state_name="Telangana",
            reference_rate_local_name="Market Value / Unit Rate",
            native_area_unit="per_sqyd",
            official_portal_url="https://registration.telangana.gov.in/",
            reference_rate_source_name="IGRS Telangana Market Value & Unit Rates",
            transaction_source_name="IGRS Telangana Registered Transaction Services",
            reference_rate_approved=False,
            transaction_data_approved=False,
            transaction_restriction_reason=(
                "Bulk transaction deed access is restricted under portal terms; "
                "evaluating authorized commercial open data aggregator contracts."
            ),
            supported_districts=["Hyderabad", "Rangareddy", "Medchal-Malkajgiri"],
            raw_field_mappings={
                "zone_tehsil": "Mandal / Registration Sub-District (e.g. Shaikpet, Serilingampally)",
                "rate_raw": "Per square yard basic market value in INR",
                "rate_unit_raw": "Unit of measurement (per_sqyd / per square yard)",
            },
        )
        super().__init__(metadata=metadata)

    def document_source_transformations(self) -> dict[str, Any]:
        return {
            "state_code": "TS",
            "reference_rate_type": "IGRS Basic Value / Unit Rate Schedule",
            "unit_conversion": "rate_inr_per_sqft = rate_raw / 9.0",
            "area_basis": "Rates published by Registration and Stamps Department, Telangana per square yard (gaj)",
            "transaction_status": "Restricted (Do not scrape; abstains on real market transaction retrieval)",
        }
