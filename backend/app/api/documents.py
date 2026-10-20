"""Document ingestion and processing API endpoints (Reserved for Phase 1+).

Protected by default (F-05): every route added here inherits the ``require_api_key``
dependency. See ``docs/security/access_policy.md``.
"""

from fastapi import APIRouter, Depends

from app.security.auth import require_api_key

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
    dependencies=[Depends(require_api_key)],
)

# Endpoint definitions will be implemented in future phases.
