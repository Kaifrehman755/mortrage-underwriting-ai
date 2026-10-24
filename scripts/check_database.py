#!/usr/bin/env python3
"""PostGIS connectivity and schema-readiness checker (R21 deliverable, F-18; relates to F-12).

By default this is **static**: it reports the configured database target (with credentials
redacted) and the tables the canonical ORM expects, and it does **not** connect to anything.

Pass ``--connect`` to perform a live, read-only probe (``SELECT 1`` plus a check that every
expected table exists). It never writes, never migrates, and never resets anything.

Exit codes: 0 on success, 1 on a failed check, 2 when ``--connect`` was requested but no
usable database URL is configured.

Usage::

    python scripts/check_database.py                 # static (no connection)
    python scripts/check_database.py --connect       # live read-only probe
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND = REPO_ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine

CONNECT_TIMEOUT_SECONDS = 10.0


def _expected_tables() -> list[str]:
    """Return the canonical ORM table names (imports the models to populate metadata)."""
    from app.database import models as _models  # noqa: F401
    from app.database.base import Base

    return sorted(Base.metadata.tables.keys())


def _configured_url() -> str | None:
    try:
        from app.core.config import get_settings

        return get_settings().DATABASE_URL
    except Exception as exc:  # noqa: BLE001 - surface config problems, do not crash
        print(f"[FAIL] could not load settings: {type(exc).__name__}")
        return None


def redact(url: str) -> str:
    """Render a URL with any password removed."""
    try:
        return make_url(url).render_as_string(hide_password=True)
    except Exception:  # noqa: BLE001 - fall back to a coarse redaction
        return url.split("@")[-1] if "@" in url else url


async def _probe(url: str, expected: list[str]) -> tuple[bool, list[str], list[str]]:
    """Return (connected, missing_tables, present_tables)."""
    engine = create_async_engine(url)
    try:
        async with engine.connect() as conn:
            await asyncio.wait_for(conn.execute(text("SELECT 1")), timeout=CONNECT_TIMEOUT_SECONDS)
            result = await conn.execute(
                text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
            )
            present = {row[0] for row in result.fetchall()}
    finally:
        await engine.dispose()
    missing = [table for table in expected if table not in present]
    return True, missing, sorted(present)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check PostGIS connectivity and schema readiness.")
    parser.add_argument(
        "--connect",
        action="store_true",
        help="Perform a live read-only probe (default: static config check only)",
    )
    args = parser.parse_args(argv)

    expected = _expected_tables()
    url = _configured_url()

    print("Database readiness check (R21 / F-18)")
    print(f"  expected tables: {len(expected)}")
    for table in expected:
        print(f"    - {table}")

    if url is None:
        print("  database url:   NOT CONFIGURED")
        return 2 if args.connect else 1

    print(f"  database url:   {redact(url)}")

    if not args.connect:
        print("Static mode: no connection attempted (pass --connect for a live probe).")
        return 0

    try:
        connected, missing, present = asyncio.run(_probe(url, expected))
    except Exception as exc:  # noqa: BLE001 - any connection failure is a failed probe
        print(f"[FAIL] could not connect: {type(exc).__name__}: {exc}")
        return 1

    if not connected:  # pragma: no cover - defensive
        return 1
    print(f"  live tables:    {len(present)} present in schema 'public'")
    if missing:
        print(f"[FAIL] missing {len(missing)} expected table(s): {', '.join(missing)}")
        print("       (run `alembic upgrade head` to build the schema from the initial revision)")
        return 1
    print("[OK] connection succeeded and all expected tables are present.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
