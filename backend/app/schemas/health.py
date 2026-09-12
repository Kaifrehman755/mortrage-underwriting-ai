"""Health check response schema."""


from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Schema for health status endpoint."""

    status: str = Field(default="healthy", description="Operational status of the API service")
    service: str = Field(default="mortgage-underwriting-api", description="Service identifier")
    version: str = Field(default="0.1.0", description="API version")
    environment: str = Field(default="development", description="Current deployment environment")
    database: str | None = Field(default="unknown", description="Database connectivity status")
