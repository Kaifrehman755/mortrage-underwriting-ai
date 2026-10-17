"""Uttar Pradesh (UP) State Property Provider Adapter.

Enforces GEMINI.md Section 3 and Section 10 Step 5:
- Official Source: IGRSUP Circle Rate Services (https://igrsup.gov.in/).
- Candidate Data Category: reference_rate (circle rate schedule). Provenance UNVERIFIED (F-03): source approval is pending_review and the local snapshot is a synthetic dev fixture.
- Native Area Unit: per_sqm (converted to per_sqft via 10.7639104167 factor).
- Transaction Deed Access: RESTRICTED/REJECTED. No automated bulk deed scraping permitted.
"""

from typing import Any

from app.providers.base import BaseStateProvider, StateProviderMetadata


class UttarPradeshProvider(BaseStateProvider):
    """Uttar Pradesh state provider for administrative circle rates and jurisdiction rules."""

    def __init__(self) -> None:
        metadata = StateProviderMetadata(
            state_code="UP",
            state_name="Uttar Pradesh",
            reference_rate_local_name="Circle Rate",
            native_area_unit="per_sqm",
            official_portal_url="https://igrsup.gov.in/",
            reference_rate_source_name="IGRSUP Circle Rate Services",
            transaction_source_name="IGRSUP Deed Search & Property Search",
            reference_rate_approved=False,
            transaction_data_approved=False,
            transaction_restriction_reason=(
                "Portal terms prohibit automated extraction; interactive CAPTCHA and OTP controls exist. "
                "Bulk transaction API is unconfirmed."
            ),
            supported_districts=["Lucknow"],
            raw_field_mappings={
                "zone_tehsil": "tehsil / administrative sub-division (e.g. Lucknow Sadar)",
                "rate_raw": "Per square metre circle rate in INR",
                "rate_unit_raw": "Unit of measurement (per_sqm)",
            },
        )
        super().__init__(metadata=metadata)

    def document_source_transformations(self) -> dict[str, Any]:
        return {
            "state_code": "UP",
            "reference_rate_type": "Administrative Circle Rate",
            "unit_conversion": "rate_inr_per_sqft = rate_raw / 10.7639104167",
            "area_basis": "Rates apply per sq. metre of carpet/built-up flat area as published by District Magistrate",
            "transaction_status": "Restricted (Do not scrape; abstains on real market transaction retrieval)",
        }
