"""F-07 regression tests: no insecure secrets/database defaults outside development.

Verifies (Phase 2, Priority 4 — F-07, hard-rule R19):
1. ``SECRET_KEY`` and ``DATABASE_URL`` must be set explicitly outside development.
2. The development throwaway values are rejected outside development.
3. A too-short production ``SECRET_KEY`` is rejected.
4. Development environments still get convenient throwaway defaults.
5. Version-controlled templates contain no working credentials.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.config import DEV_DATABASE_URL, DEV_SECRET_KEY, Settings

REPO_ROOT = Path(__file__).resolve().parents[3]

SECURE_DB_URL = "postgresql+asyncpg://app_user:strong-password@db.internal:5432/mortgage_underwriting"
SECURE_SECRET = "a" * 40


def _production(**overrides) -> Settings:
    base = {
        "APP_ENV": "production",
        "SECRET_KEY": SECURE_SECRET,
        "DATABASE_URL": SECURE_DB_URL,
    }
    base.update(overrides)
    return Settings(_env_file=None, **base)


def test_production_without_secret_key_raises() -> None:
    with pytest.raises(ValidationError):
        _production(SECRET_KEY="")


def test_production_without_database_url_raises() -> None:
    with pytest.raises(ValidationError):
        _production(DATABASE_URL="")


def test_production_rejects_development_secret_key() -> None:
    with pytest.raises(ValidationError):
        _production(SECRET_KEY=DEV_SECRET_KEY)


def test_production_rejects_development_database_url() -> None:
    with pytest.raises(ValidationError):
        _production(DATABASE_URL=DEV_DATABASE_URL)


def test_production_rejects_short_secret_key() -> None:
    with pytest.raises(ValidationError):
        _production(SECRET_KEY="too-short")


def test_production_accepts_explicit_secure_values() -> None:
    settings = _production()
    assert settings.SECRET_KEY == SECURE_SECRET
    assert settings.DATABASE_URL == SECURE_DB_URL
    assert DEV_DATABASE_URL != settings.DATABASE_URL


def test_development_keeps_throwaway_defaults() -> None:
    settings = Settings(APP_ENV="development", _env_file=None)
    assert settings.SECRET_KEY == DEV_SECRET_KEY
    assert settings.DATABASE_URL == DEV_DATABASE_URL


def test_default_environment_is_development(monkeypatch: pytest.MonkeyPatch) -> None:
    # The test conftest sets APP_ENV=test; remove it so the class default applies.
    monkeypatch.delenv("APP_ENV", raising=False)
    settings = Settings(_env_file=None)
    assert settings.APP_ENV == "development"
    assert settings.SECRET_KEY == DEV_SECRET_KEY


def test_alembic_ini_has_no_committed_credentials() -> None:
    text = (REPO_ROOT / "alembic.ini").read_text(encoding="utf-8")
    assert "postgres:postgres@" not in text


def test_env_example_contains_only_placeholders() -> None:
    text = (REPO_ROOT / ".env.example").read_text(encoding="utf-8")
    assert DEV_SECRET_KEY not in text
    assert "default-insecure-dev-secret-key" not in text
    assert "postgres:postgres@" not in text
