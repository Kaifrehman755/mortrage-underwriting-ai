"""Karnataka (KA) State Property Provider Adapter.

Enforces GEMINI.md Section 3 and Section 10 Step 5:
- Official Source: Kaveri 2.0 Guidance Value Services (https://kaveri.karnataka.gov.in/).
- Candidate Data Category: reference_rate (Kaveri 2.0 guidance value schedule). Provenance UNVERIFIED (F-03): source approval is pending_review and the local snapshot is a synthetic dev fixture.
- Native Area Unit: per_sqft (1:1 conversion).
- Transaction Deed Access: RESTRICTED/REJECTED. Kaveri 2.0 document services prohibit automated scraping.
"""

from typing import Any

from app.providers.base import BaseStateProvider, StateProviderMetadata


class KarnatakaProvider(BaseStateProvider):
    """Karnataka state provider for Kaveri 2.0 Guidance Values and jurisdiction rules."""

    def __init__(self) -> None:
        metadata = StateProviderMetadata(
            state_code="KA",
            state_name="Karnataka",
            reference_rate_local_name="Guidance Value",
            native_area_unit="per_sqft",
            official_portal_url="https://kaveri.karnataka.gov.in/",
            reference_rate_source_name="Kaveri 2.0 Guidance Value Services",
            transaction_source_name="Kaveri 2.0 Document & Encumbrance Services",
            reference_rate_approved=False,
            transaction_data_approved=False,
            transaction_restriction_reason=(
                "Automated access prohibited by portal terms and security controls. "
                "Bulk transaction export not publicly licensed."
            ),
            supported_districts=["Bengaluru Urban", "Bengaluru Rural"],
            raw_field_mappings={
                "zone_tehsil": "Registration Taluk / Sub-Registrar jurisdiction (e.g. Bengaluru East, South)",
                "rate_raw": "Per square foot guidance value in INR",
                "rate_unit_raw": "Unit of measurement (per_sqft)",
            },
        )
        super().__init__(metadata=metadata)

    def document_source_transformations(self) -> dict[str, Any]:
        return {
            "state_code": "KA",
            "reference_rate_type": "Kaveri 2.0 Guidance Value Schedule",
            "unit_conversion": "rate_inr_per_sqft = rate_raw (native unit is already per_sqft)",
            "area_basis": "Rates published by Department of Stamps and Registration, Karnataka per sq. foot super built-up/carpet",
            "transaction_status": "Restricted (Do not scrape; abstains on real market transaction retrieval)",
        }
