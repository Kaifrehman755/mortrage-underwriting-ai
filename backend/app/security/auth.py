"""Authentication primitives for non-public endpoints (F-05).

Phase-0 access model (documented in ``docs/security/access_policy.md``):

* Public: ``GET /health`` and ``GET /circle-rates/lookup`` (reference data only).
* Everything else: authenticated, and **protected by default** via :func:`require_api_key`.

There is deliberately no user-management system here: a single operator-provisioned API key
(``Settings.API_KEY``) is compared in constant time. This exists so that future
borrower-adjacent endpoints cannot ship unauthenticated (the F-05 trust-boundary gap), and so
the behaviour is testable (503 when unconfigured, 401 when missing/invalid, 200 when valid).
Replace with a real identity provider before exposing personal or confidential data.
"""

from __future__ import annotations

import hmac
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from app.core.config import Settings, get_settings

AUTH_SCHEME = "Bearer"
API_KEY_HEADER = "X-API-Key"


@dataclass(frozen=True)
class AuthenticatedCaller:
    """Identity of an authenticated, non-public caller."""

    scheme: str
    subject: str = "api-key"


def _extract_presented_key(authorization: str | None, x_api_key: str | None) -> str | None:
    """Read the presented credential from ``Authorization: Bearer`` or ``X-API-Key``."""
    if x_api_key and x_api_key.strip():
        return x_api_key.strip()
    if authorization:
        parts = authorization.split(None, 1)
        if len(parts) == 2 and parts[0].lower() == AUTH_SCHEME.lower():
            token = parts[1].strip()
            return token or None
    return None


async def require_api_key(
    settings: Annotated[Settings, Depends(get_settings)],
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
    x_api_key: Annotated[str | None, Header(alias=API_KEY_HEADER)] = None,
) -> AuthenticatedCaller:
    """FastAPI dependency enforcing authentication, failing closed (F-05).

    * No ``API_KEY`` configured ⇒ ``503`` (never authorise by accident).
    * Missing/invalid credential ⇒ ``401``.
    * Valid credential ⇒ an :class:`AuthenticatedCaller`.
    """
    expected = (settings.API_KEY or "").strip()
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not configured (API_KEY is unset); refusing non-public access.",
        )

    presented = _extract_presented_key(authorization, x_api_key)
    if presented is None or not hmac.compare_digest(presented, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid credentials.",
            headers={"WWW-Authenticate": AUTH_SCHEME},
        )
    return AuthenticatedCaller(scheme="api-key")


class AuthService:
    """Credential verification helpers for internal/non-public callers (F-05).

    Phase 0 intentionally has no user store, session table, or password hashing. Extend this
    before exposing borrower-adjacent data.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    @property
    def is_configured(self) -> bool:
        """Whether an API key has been provisioned for non-public access."""
        return bool((self._settings.API_KEY or "").strip())

    def verify(self, presented: str | None) -> bool:
        """Constant-time check of a presented credential against the configured key."""
        expected = (self._settings.API_KEY or "").strip()
        if not expected or presented is None:
            return False
        return hmac.compare_digest(presented.strip(), expected)
