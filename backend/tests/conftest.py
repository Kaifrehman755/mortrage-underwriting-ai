"""Pytest test fixtures and configuration."""

import os
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

# Set test environment
os.environ["APP_ENV"] = "test"
os.environ["DEBUG"] = "true"

from app.database.connection import engine
from app.main import app


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client fixture for testing API endpoints."""
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client
    finally:
        # asyncpg connection finalizers can segfault the interpreter if the
        # global test engine is left to be destroyed after the event loop closes.
        await engine.dispose()
