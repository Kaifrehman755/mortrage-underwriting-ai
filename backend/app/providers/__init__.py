"""Multi-state provider module for Indian residential property valuation.

Enforces GEMINI.md Section 3, Section 5, and Section 10 Step 5:
- Provider interface and schema applied consistently across states.
- Initial candidate states: Uttar Pradesh (UP), Maharashtra (MH), Karnataka (KA), Telangana (TS).
- Strict Source Approval Gate: No automated scraping or live adapter without explicit approval.
- Unsupported states return an explicit data-unavailable result rather than fabricated records.
"""

from app.providers.base import (
    BaseStateProvider,
    StateProviderMetadata,
    StateReadinessStatus,
    TransactionDataUnavailableError,
    UnsupportedStateError,
)
from app.providers.registry import StateProviderRegistry, state_provider_registry

__all__ = [
    "BaseStateProvider",
    "StateProviderMetadata",
    "StateReadinessStatus",
    "UnsupportedStateError",
    "TransactionDataUnavailableError",
    "StateProviderRegistry",
    "state_provider_registry",
]
