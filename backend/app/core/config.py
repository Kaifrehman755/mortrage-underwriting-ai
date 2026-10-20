"""Application configuration using Pydantic Settings.

Security-relevant behaviour (Phase-2 remediation F-05..F-08):

* **F-07 — no insecure defaults outside development.** ``SECRET_KEY`` and ``DATABASE_URL``
  have no usable default. Development environments get safe *throwaway* defaults; any other
  environment must set them explicitly and must not use the development values.
* **F-06 — CORS fails closed.** An unparseable ``CORS_ORIGINS`` raises instead of silently
  widening to ``["*"]``, and a wildcard origin is rejected when credentials are enabled.
* **F-05 — authentication is opt-in and fail-closed.** ``API_KEY`` is empty by default; the
  ``require_api_key`` dependency refuses non-public access while it is unset.
* **F-08 — ingestion is allowlist-driven.** ``CIRCLE_RATE_ALLOWED_HOSTS`` gates outbound
  fetches and ``CIRCLE_RATE_INTAKE_DIR`` confines local file ingestion.
"""

import json
from functools import lru_cache

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Environments that explicitly permit throwaway development defaults.
DEV_ENVIRONMENTS: frozenset[str] = frozenset({"development", "dev", "local", "test", "testing", "ci"})

# Throwaway defaults. These are intentionally recognisable so they can be detected and
# rejected outside development (F-07). They are not secrets and must never reach production.
DEV_SECRET_KEY = "dev-only-insecure-secret-key-change-me"
DEV_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/mortgage_underwriting"

MIN_PRODUCTION_SECRET_KEY_LENGTH = 32


def _split_csv_list(value: str) -> list[str]:
    """Parse a comma-separated list, tolerating a JSON array as well."""
    text = value.strip()
    if not text:
        return []
    if text.startswith("["):
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Value looks like JSON but could not be parsed: {exc}") from exc
        if not isinstance(parsed, list):
            raise ValueError("JSON value must be a list")
        return [str(item).strip() for item in parsed if str(item).strip()]
    return [item.strip() for item in text.split(",") if item.strip()]


class Settings(BaseSettings):
    """Core application settings loaded from environment variables or .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application Core ---
    APP_NAME: str = "Mortgage Underwriting AI"
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    # F-07: no usable default. Filled with a throwaway value only in a development
    # environment (see `_enforce_secure_defaults`).
    SECRET_KEY: str = ""

    # --- API Server ---
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list[str] | str = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    # F-06: credentials are only safe with an explicit origin allowlist (never "*").
    CORS_ALLOW_CREDENTIALS: bool = True

    # --- API Authentication (F-05) ---
    # Empty by default: non-public routers fail closed until an operator provisions a key.
    API_KEY: str = ""
    # Best-effort in-process limit for public endpoints; 0 disables it.
    RATE_LIMIT_PER_MINUTE: int = 120

    # --- PostgreSQL Database ---
    # F-07: no usable default outside development.
    DATABASE_URL: str = ""

    # --- Storage Paths ---
    STORAGE_BASE_PATH: str = "./storage"
    STORAGE_UPLOADS_PATH: str = "./storage/uploads"
    STORAGE_PROCESSED_PATH: str = "./storage/processed"
    STORAGE_REPORTS_PATH: str = "./storage/reports"

    # --- Circle rate ingestion (Phase 1) ---
    CIRCLE_RATE_SOURCE_URL: str = ""
    CIRCLE_RATE_STATE: str = "UP"
    CIRCLE_RATE_PILOT_CITY: str = "Lucknow"
    CIRCLE_RATE_PILOT_DISTRICT: str = "Lucknow"
    INGESTION_SCHEDULE_CRON: str = "0 9 1 * *"
    # F-08: approved outbound hosts. Empty means "refuse to fetch" (fail closed); no
    # official host is assumed because provenance is not yet verified (see F-03).
    CIRCLE_RATE_ALLOWED_HOSTS: list[str] | str = []
    # F-08: local file ingestion is confined to this directory.
    CIRCLE_RATE_INTAKE_DIR: str = "./data/raw/circle_rates"

    # --- Future AI Placeholders (Phase 1+) ---
    LLM_PROVIDER: str = "local"
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    # F-09: must match the identifier used by the embedding service
    # (``backend/app/rag/embeddings.py``) and the playbook (§ stack: bge-small-en-v1.5,
    # 384 dims). Kept identical to avoid silent semantic/embedding drift.
    EMBEDDINGS_MODEL: str = "BAAI/bge-small-en-v1.5"
    VECTOR_DB_TYPE: str = "chromadb"
    VECTOR_DB_PATH: str = "./storage/vector_store"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Parse CORS origins, failing closed on anything unparseable (F-06)."""
        if isinstance(v, str):
            origins = _split_csv_list(v)
        elif isinstance(v, list):
            origins = [str(item).strip() for item in v if str(item).strip()]
        else:
            raise ValueError(
                f"CORS_ORIGINS must be a list or a comma/JSON string, got {type(v).__name__}"
            )
        if not origins:
            raise ValueError("CORS_ORIGINS must not be empty")
        return origins

    @field_validator("CIRCLE_RATE_ALLOWED_HOSTS", mode="before")
    @classmethod
    def assemble_allowed_hosts(cls, v: str | list[str]) -> list[str]:
        """Parse the ingestion host allowlist (F-08)."""
        if isinstance(v, str):
            return [host.lower() for host in _split_csv_list(v)]
        if isinstance(v, list):
            return [str(host).strip().lower() for host in v if str(host).strip()]
        raise ValueError(
            "CIRCLE_RATE_ALLOWED_HOSTS must be a list or a comma/JSON string, "
            f"got {type(v).__name__}"
        )

    @model_validator(mode="after")
    def _enforce_secure_defaults(self) -> "Settings":
        """Apply development-only defaults and reject insecure production config (F-06/F-07)."""
        is_dev = self.APP_ENV.strip().lower() in DEV_ENVIRONMENTS

        if not self.SECRET_KEY:
            if not is_dev:
                raise ValueError(
                    "SECRET_KEY must be set explicitly when APP_ENV "
                    f"({self.APP_ENV!r}) is not a development environment"
                )
            self.SECRET_KEY = DEV_SECRET_KEY

        if not self.DATABASE_URL:
            if not is_dev:
                raise ValueError(
                    "DATABASE_URL must be set explicitly when APP_ENV "
                    f"({self.APP_ENV!r}) is not a development environment"
                )
            self.DATABASE_URL = DEV_DATABASE_URL

        if not is_dev:
            if self.SECRET_KEY == DEV_SECRET_KEY:
                raise ValueError(
                    "The development SECRET_KEY must never be used outside a development environment"
                )
            if self.DATABASE_URL == DEV_DATABASE_URL:
                raise ValueError(
                    "The development DATABASE_URL must never be used outside a development environment"
                )
            if len(self.SECRET_KEY) < MIN_PRODUCTION_SECRET_KEY_LENGTH:
                raise ValueError(
                    "SECRET_KEY must be at least "
                    f"{MIN_PRODUCTION_SECRET_KEY_LENGTH} characters outside a development environment"
                )

        # F-06: a wildcard origin combined with credentials is a misconfiguration hazard.
        if "*" in self.CORS_ORIGINS and self.CORS_ALLOW_CREDENTIALS:
            raise ValueError(
                "CORS_ORIGINS must not contain '*' when CORS_ALLOW_CREDENTIALS is enabled"
            )

        return self


@lru_cache
def get_settings() -> Settings:
    """Return a cached instance of the application settings."""
    return Settings()


def clear_settings_cache() -> None:
    """Clear the cached settings (used by configuration regression tests)."""
    get_settings.cache_clear()
