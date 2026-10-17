"""Maharashtra (MH) State Property Provider Adapter.

Enforces GEMINI.md Section 3 and Section 10 Step 5:
- Official Source: IGR Maharashtra eASR (Ready Reckoner Rates) (https://easr.igrmaharashtra.gov.in/).
- Candidate Data Category: reference_rate (eASR annual schedule). Provenance UNVERIFIED (F-03): source approval is pending_review and the local snapshot is a synthetic dev fixture.
- Native Area Unit: per_sqm (converted to per_sqft via 10.7639104167 factor).
- Transaction Deed Access: RESTRICTED/REJECTED. eSearch portal prohibits automated scraping.
"""

from typing import Any

from app.providers.base import BaseStateProvider, StateProviderMetadata


class MaharashtraProvider(BaseStateProvider):
    """Maharashtra state provider for Ready Reckoner benchmark rates and jurisdiction rules."""

    def __init__(self) -> None:
        metadata = StateProviderMetadata(
            state_code="MH",
            state_name="Maharashtra",
            reference_rate_local_name="Ready Reckoner Rate",
            native_area_unit="per_sqm",
            official_portal_url="https://easr.igrmaharashtra.gov.in/",
            reference_rate_source_name="IGR Maharashtra eASR (Ready Reckoner Rates)",
            transaction_source_name="IGR Maharashtra eSearch Portal",
            reference_rate_approved=False,
            transaction_data_approved=False,
            transaction_restriction_reason=(
                "Bulk transaction access without official API authorization is prohibited by portal terms. "
                "Interactive eSearch requires manual verification."
            ),
            supported_districts=["Mumbai Suburban", "Mumbai City", "Pune"],
            raw_field_mappings={
                "zone_tehsil": "eASR Zone / Tehsil (e.g. Andheri, Bandra)",
                "rate_raw": "Per square metre ready reckoner rate in INR",
                "rate_unit_raw": "Unit of measurement (per_sqm)",
            },
        )
        super().__init__(metadata=metadata)

    def document_source_transformations(self) -> dict[str, Any]:
        return {
            "state_code": "MH",
            "reference_rate_type": "Annual Statement of Rates (ASR / Ready Reckoner)",
            "unit_conversion": "rate_inr_per_sqft = rate_raw / 10.7639104167",
            "area_basis": "Rates published by Town Planning and Valuation Department, Maharashtra per sq. metre built-up",
            "transaction_status": "Restricted (Do not scrape; abstains on real market transaction retrieval)",
        }
