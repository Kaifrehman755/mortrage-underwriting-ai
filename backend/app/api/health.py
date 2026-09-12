"""Health check endpoint router."""

from fastapi import APIRouter, status

from app.core.config import get_settings
from app.database.connection import check_db_health
from app.schemas.health import HealthResponse

router = APIRouter(tags=["Health"])
settings = get_settings()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Service Health Check",
    description="Returns the operational status of the Mortgage Underwriting API service and database connectivity.",
)
async def health_check() -> HealthResponse:
    """Check API and database health status."""
    is_db_healthy = await check_db_health()
    db_status = "connected" if is_db_healthy else "disconnected"

    return HealthResponse(
        status="healthy",
        service="mortgage-underwriting-api",
        version="0.1.0",
        environment=settings.APP_ENV,
        database=db_status,
    )
