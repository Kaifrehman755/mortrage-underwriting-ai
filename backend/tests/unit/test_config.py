"""Unit tests for configuration loading and validation."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_default_configuration():
    """Verify default configuration values."""
    settings = Settings()
    assert settings.APP_NAME == "Mortgage Underwriting AI"
    assert settings.API_PORT == 8000
    assert isinstance(settings.CORS_ORIGINS, list)
    assert settings.STORAGE_BASE_PATH == "./storage"


def test_cors_origins_parsing_json_string():
    """Verify CORS origins string parsing into list."""
    settings = Settings(CORS_ORIGINS='["http://localhost:3000","http://example.com"]')
    assert "http://localhost:3000" in settings.CORS_ORIGINS
    assert "http://example.com" in settings.CORS_ORIGINS


def test_cors_origins_parsing_comma_separated():
    """Verify comma-separated CORS string parsing."""
    settings = Settings(CORS_ORIGINS="http://localhost:3000,http://example.com")
    assert "http://localhost:3000" in settings.CORS_ORIGINS
    assert "http://example.com" in settings.CORS_ORIGINS


def test_invalid_port_type_fails():
    """Verify invalid configuration type raises ValidationError."""
    with pytest.raises(ValidationError):
        Settings(API_PORT="not-an-integer-port")
