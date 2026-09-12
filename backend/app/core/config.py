"""Application configuration using Pydantic Settings."""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    SECRET_KEY: str = "default-insecure-dev-secret-key-replace-in-production"

    # --- API Server ---
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list[str] | str = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # --- PostgreSQL Database ---
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/mortgage_underwriting"

    # --- Storage Paths ---
    STORAGE_BASE_PATH: str = "./storage"
    STORAGE_UPLOADS_PATH: str = "./storage/uploads"
    STORAGE_PROCESSED_PATH: str = "./storage/processed"
    STORAGE_REPORTS_PATH: str = "./storage/reports"

    # --- Future AI Placeholders (Phase 1+) ---
    LLM_PROVIDER: str = "local"
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    EMBEDDINGS_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    VECTOR_DB_TYPE: str = "chromadb"
    VECTOR_DB_PATH: str = "./storage/vector_store"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json

                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["*"]


@lru_cache
def get_settings() -> Settings:
    """Return a cached instance of the application settings."""
    return Settings()
