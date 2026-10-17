"""F-06 regression tests: CORS configuration must fail closed.

Verifies (Phase 2, Priority 4 — F-06):
1. An unparseable ``CORS_ORIGINS`` value raises instead of silently widening to ``["*"]``.
2. A non-string/non-list value raises.
3. A wildcard origin is rejected while credentials are enabled.
4. A wildcard origin is permitted only when credentials are disabled.
5. The API's CORS middleware uses the validated settings (never a wildcard when
   credentials are enabled).
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings


def _settings(**overrides) -> Settings:
    return Settings(APP_ENV="test", _env_file=None, **overrides)


def test_malformed_json_cors_origins_raises() -> None:
    with pytest.raises(ValidationError):
        _settings(CORS_ORIGINS='["http://localhost:3000",')


def test_unexpected_type_cors_origins_raises() -> None:
    with pytest.raises(ValidationError):
        _settings(CORS_ORIGINS=1234)


def test_empty_cors_origins_raises() -> None:
    with pytest.raises(ValidationError):
        _settings(CORS_ORIGINS="")


def test_wildcard_origins_rejected_with_credentials() -> None:
    with pytest.raises(ValidationError):
        _settings(CORS_ORIGINS=["*"], CORS_ALLOW_CREDENTIALS=True)


def test_wildcard_origins_allowed_without_credentials() -> None:
    settings = _settings(CORS_ORIGINS="*", CORS_ALLOW_CREDENTIALS=False)
    assert settings.CORS_ORIGINS == ["*"]
    assert settings.CORS_ALLOW_CREDENTIALS is False


def test_comma_separated_origins_still_parse() -> None:
    settings = _settings(CORS_ORIGINS="http://a.example,http://b.example")
    assert settings.CORS_ORIGINS == ["http://a.example", "http://b.example"]


def test_cors_middleware_never_widens_to_wildcard_with_credentials() -> None:
    from app.main import create_application

    app = create_application()
    cors = next(
        middleware
        for middleware in app.user_middleware
        if getattr(middleware.cls, "__name__", "") == "CORSMiddleware"
    )
    configured = get_settings()
    assert cors.kwargs["allow_origins"] == list(configured.CORS_ORIGINS)
    assert cors.kwargs["allow_credentials"] is configured.CORS_ALLOW_CREDENTIALS
    if cors.kwargs["allow_credentials"]:
        assert "*" not in cors.kwargs["allow_origins"]
