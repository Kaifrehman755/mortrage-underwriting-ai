"""F-09 regression tests: `.env.example` ↔ Settings sync and embedding-model unification.

Verifies (Phase 2, Priority 5 — F-09, hard-rule R19):
1. Every `Settings` field is documented in `.env.example` (so operators can discover
   and override every supported configuration knob).
2. `.env.example` contains no working secret values (placeholders only).
3. The configured embedding-model identifier matches the identifier the embedding
   service actually uses — no silent embedding-model drift.
4. That identifier is the one named by the governing playbook (bge-small-en-v1.5).
"""

from __future__ import annotations

import re
from pathlib import Path

from app.core.config import Settings, get_settings
from app.rag.embeddings import EmbeddingService

REPO_ROOT = Path(__file__).resolve().parents[3]
ENV_EXAMPLE = REPO_ROOT / ".env.example"
PLAYBOOK = REPO_ROOT / "backend" / "app" / "property" / "playbook.md"

# Names in `.env.example` that intentionally do not map to a `Settings` field
# (consumed by docker-compose / the frontend instead).
NON_SETTINGS_ENV_VARS = {
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "POSTGRES_DB",
    "POSTGRES_HOST",
    "POSTGRES_PORT",
    "FRONTEND_PORT",
    "NEXT_PUBLIC_API_URL",
}


def _settings() -> Settings:
    return Settings(APP_ENV="test", _env_file=None)


def _documented_keys() -> set[str]:
    text = ENV_EXAMPLE.read_text(encoding="utf-8")
    keys = set()
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        keys.add(line.split("=", 1)[0].strip())
    return keys


def test_every_settings_field_is_documented_in_env_example() -> None:
    documented = _documented_keys()
    missing = sorted(set(Settings.model_fields) - documented - NON_SETTINGS_ENV_VARS)
    assert not missing, f"Settings fields missing from .env.example: {missing}"


def test_env_example_does_not_introduce_unknown_settings() -> None:
    documented = _documented_keys()
    settings_fields = set(Settings.model_fields)
    unknown = sorted(
        key
        for key in documented
        if key not in settings_fields and key not in NON_SETTINGS_ENV_VARS
    )
    assert not unknown, f".env.example documents unknown settings: {unknown}"


def test_env_example_has_no_working_secret_values() -> None:
    text = ENV_EXAMPLE.read_text(encoding="utf-8")
    for secret in ("dev-only-insecure-secret-key-change-me", "postgres:postgres@"):
        assert secret not in text, f".env.example leaks a working value: {secret}"
    # Placeholder-only assignments for the secret-bearing keys.
    assert re.search(r"^SECRET_KEY=\s*$", text, re.MULTILINE)
    assert re.search(r"^DATABASE_URL=\s*$", text, re.MULTILINE)
    assert re.search(r"^API_KEY=\s*$", text, re.MULTILINE)


def test_embedding_model_matches_embedding_service() -> None:
    configured = _settings().EMBEDDINGS_MODEL
    service = EmbeddingService()
    assert configured == service.model_name, (
        "Settings.EMBEDDINGS_MODEL and EmbeddingService disagree — this is exactly the "
        "silent embedding-model drift F-09 flags"
    )


def test_embedding_model_matches_playbook() -> None:
    configured = get_settings().EMBEDDINGS_MODEL
    playbook = PLAYBOOK.read_text(encoding="utf-8")
    assert "bge-small-en-v1.5" in playbook, "playbook no longer names the embedding model"
    assert "bge-small-en-v1.5" in configured
