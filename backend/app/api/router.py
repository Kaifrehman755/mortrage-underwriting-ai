"""Main API router combining all sub-routers."""

from fastapi import APIRouter

from app.api.applications import router as applications_router
from app.api.auth import router as auth_router
from app.api.compliance import router as compliance_router
from app.api.documents import router as documents_router
from app.api.health import router as health_router
from app.api.reports import router as reports_router
from app.api.underwriting import router as underwriting_router

api_router = APIRouter()

# Include health router (active in Phase 0)
api_router.include_router(health_router)

# Include placeholder routers (inactive/empty in Phase 0)
api_router.include_router(auth_router)
api_router.include_router(applications_router)
api_router.include_router(documents_router)
api_router.include_router(underwriting_router)
api_router.include_router(compliance_router)
api_router.include_router(reports_router)
