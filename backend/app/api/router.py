"""Main API router combining all sub-routers.

Access policy (F-05 — full detail in ``docs/security/access_policy.md``):

* **Public** (no authentication): ``/health`` and ``/circle-rates/lookup``. The lookup returns
  government reference data only; it is rate-limited and validated.
* **Protected by default**: every other router is constructed with the ``require_api_key``
  dependency, so a newly added endpoint is authenticated unless it is *deliberately* added to
  the public set and documented here.
"""

from fastapi import APIRouter

from app.api.applications import router as applications_router
from app.api.auth import router as auth_router
from app.api.circle_rates import router as circle_rates_router
from app.api.compliance import router as compliance_router
from app.api.documents import router as documents_router
from app.api.health import router as health_router
from app.api.reports import router as reports_router
from app.api.underwriting import router as underwriting_router

api_router = APIRouter()

# --- Public routers (documented access-policy exceptions) ---
# /health: liveness/readiness probe.
api_router.include_router(health_router)
# /circle-rates/lookup: public government reference data (rate-limited, no personal data).
api_router.include_router(circle_rates_router)

# --- Protected routers (require_api_key attached on each router; F-05) ---
api_router.include_router(auth_router)
api_router.include_router(applications_router)
api_router.include_router(documents_router)
api_router.include_router(underwriting_router)
api_router.include_router(compliance_router)
api_router.include_router(reports_router)
