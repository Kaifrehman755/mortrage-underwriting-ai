"""Unit tests for the health check and service status endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint_success(async_client: AsyncClient):
    """Test that the health endpoint returns 200 OK and expected status fields."""
    response = await async_client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "mortgage-underwriting-api"
    assert "version" in data
    assert "environment" in data
    assert "database" in data


@pytest.mark.asyncio
async def test_root_status_endpoint(async_client: AsyncClient):
    """Test that the root landing endpoint returns basic API descriptor metadata."""
    response = await async_client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "docs" in data
    assert "health" in data


@pytest.mark.asyncio
async def test_openapi_docs_accessible(async_client: AsyncClient):
    """Test that OpenAPI schema JSON is generated without error."""
    response = await async_client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "Mortgage Underwriting AI"
