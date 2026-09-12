"""Integration tests for database connection and health check mechanism."""

import pytest

from app.database.connection import check_db_health


@pytest.mark.asyncio
async def test_check_db_health_resilience():
    """Verify check_db_health returns a boolean without raising uncaught exceptions."""
    result = await check_db_health()
    assert isinstance(result, bool)
