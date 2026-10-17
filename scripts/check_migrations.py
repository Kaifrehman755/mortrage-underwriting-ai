#!/usr/bin/env python3
"""Migration-readiness checker (Phase-2 remediation F-12 / R21).

Static, side-effect-free: it inspects the Alembic configuration and revision files on disk
without importing the application, connecting to a database, or running migrations. Use it to
answer "is the migration tree usable yet, and if not, exactly what is missing?".

F-12 reported that ``migrations/`` contained only ``env.py`` and ``script.py.mako`` (no
``versions/`` and therefore no initial revision). Generating and testing the initial revision
requires a live PostGIS database, which is out of the authorised verification scope; this script
records that blocker explicitly instead of leaving it silent.

Usage::

    python scripts/check_migrations.py               # full readiness (exit 0 only if ready)
    python scripts/check_migrations.py --config-only  # config sanity only
    python scripts/check_migrations.py --json         # machine-readable output
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS_DIR = REPO_ROOT / "migrations"
VERSIONS_DIR = MIGRATIONS_DIR / "versions"
ENV_PY = MIGRATIONS_DIR / "env.py"
SCRIPT_MAKO = MIGRATIONS_DIR / "script.py.mako"
ALEMBIC_INI = REPO_ROOT / "alembic.ini"

# F-10: the canonical ORM tree that Alembic must target.
CANONICAL_METADATA_IMPORT = "app.database.models"
CANONICAL_TARGET_STATEMENT = "target_metadata = Base.metadata"

# Credentials embedded in a URL, e.g. postgresql://user:pass@host/db (F-07).
_CREDENTIALS_IN_URL = re.compile(r"://[^/\s:@]+:[^/\s:@]+@")
_REVISION_RE = re.compile(r"^revision:\s*str\s*=\s*[\"']([^\"']+)[\"']", re.MULTILINE)
_DOWN_REVISION_RE = re.compile(
    r"^down_revision:\s*[^=]*=\s*(?:None|[\"']([^\"']*)[\"'])", re.MULTILINE
)


@dataclass
class MigrationReport:
    """Structured result of a migration-tree inspection."""

    env_py: bool = False
    script_mako: bool = False
    alembic_ini: bool = False
    canonical_target: bool = False
    url_has_no_credentials: bool = False
    versions_dir: bool = False
    revision_files: list[str] = field(default_factory=list)
    heads: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def config_ok(self) -> bool:
        """Whether the Alembic configuration is present, canonical and credential-free."""
        return (
            self.env_py
            and self.script_mako
            and self.alembic_ini
            and self.canonical_target
            and self.url_has_no_credentials
        )

    @property
    def ready(self) -> bool:
        """Whether the migration tree is complete enough to create a clean schema."""
        return self.config_ok and bool(self.revision_files) and len(self.heads) == 1


def _parse_revisions() -> tuple[list[str], list[str]]:
    files: list[str] = []
    revisions: dict[str, str | None] = {}
    for path in sorted(VERSIONS_DIR.glob("*.py")):
        if path.name == "__init__.py":
            continue
        text = path.read_text(encoding="utf-8")
        revision_match = _REVISION_RE.search(text)
        if not revision_match:
            continue
        files.append(path.name)
        down_match = _DOWN_REVISION_RE.search(text)
        revisions[revision_match.group(1)] = down_match.group(1) if down_match else None
    parents = {parent for parent in revisions.values() if parent}
    heads = sorted(rev for rev in revisions if rev not in parents)
    return files, heads


def inspect_migration_tree() -> MigrationReport:
    """Inspect the migration tree and return a :class:`MigrationReport`."""
    report = MigrationReport()
    report.env_py = ENV_PY.is_file()
    report.script_mako = SCRIPT_MAKO.is_file()
    report.alembic_ini = ALEMBIC_INI.is_file()
    report.versions_dir = VERSIONS_DIR.is_dir()

    if report.env_py:
        env_text = ENV_PY.read_text(encoding="utf-8")
        report.canonical_target = (
            CANONICAL_METADATA_IMPORT in env_text
            and CANONICAL_TARGET_STATEMENT in env_text
        )
        if not report.canonical_target:
            report.errors.append(
                f"migrations/env.py does not target the canonical ORM tree ({CANONICAL_METADATA_IMPORT})"
            )

    if report.alembic_ini:
        ini_text = ALEMBIC_INI.read_text(encoding="utf-8")
        url_lines = [
            line for line in ini_text.splitlines() if line.strip().startswith("sqlalchemy.url")
        ]
        report.url_has_no_credentials = all(
            not _CREDENTIALS_IN_URL.search(line) for line in url_lines
        )
        if not url_lines:
            report.errors.append("alembic.ini has no sqlalchemy.url entry")
        elif not report.url_has_no_credentials:
            report.errors.append("alembic.ini sqlalchemy.url embeds credentials (F-07)")

    if report.versions_dir:
        try:
            report.revision_files, report.heads = _parse_revisions()
        except OSError as exc:  # pragma: no cover - defensive
            report.errors.append(f"could not read migrations/versions: {exc}")

    if not report.env_py:
        report.errors.append(f"missing {ENV_PY.relative_to(REPO_ROOT)}")
    if not report.script_mako:
        report.errors.append(f"missing {SCRIPT_MAKO.relative_to(REPO_ROOT)}")
    if not report.alembic_ini:
        report.errors.append(f"missing {ALEMBIC_INI.relative_to(REPO_ROOT)}")
    if not report.versions_dir:
        report.errors.append("missing migrations/versions/ directory")
    elif not report.revision_files:
        report.errors.append(
            "migrations/versions/ has no revision files - F-12 open (blocked on an "
            "authorised disposable PostGIS database for autogenerate + upgrade/downgrade)"
        )
    elif len(report.heads) != 1:
        report.errors.append(f"expected exactly one head revision, found {report.heads}")

    return report


def _print_human(report: MigrationReport, config_only: bool) -> None:
    def mark(ok: bool) -> str:
        return "OK  " if ok else "FAIL"

    print("Migration readiness check (F-12)")
    print(f"  [{mark(report.env_py)}] migrations/env.py")
    print(f"  [{mark(report.script_mako)}] migrations/script.py.mako")
    print(f"  [{mark(report.alembic_ini)}] alembic.ini")
    print(f"  [{mark(report.canonical_target)}] targets canonical ORM tree ({CANONICAL_METADATA_IMPORT})")
    print(f"  [{mark(report.url_has_no_credentials)}] sqlalchemy.url has no embedded credentials")
    print(f"  [{mark(report.versions_dir)}] migrations/versions/ exists")
    print(f"  revision files: {report.revision_files or 'none'}")
    if report.revision_files:
        print(f"  heads: {report.heads}")

    if config_only:
        print(f"Config: {'OK' if report.config_ok else 'FAIL'}")
    else:
        print(f"Ready: {'YES' if report.ready else 'NO'}")
    for error in report.errors:
        print(f"  - {error}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check Alembic migration readiness (F-12).")
    parser.add_argument(
        "--config-only",
        action="store_true",
        help="Only check the Alembic configuration, not the presence of revisions",
    )
    parser.add_argument("--json", action="store_true", help="Emit a JSON report")
    args = parser.parse_args(argv)

    report = inspect_migration_tree()

    if args.json:
        payload = asdict(report)
        payload["config_ok"] = report.config_ok
        payload["ready"] = report.ready
        print(json.dumps(payload, indent=2))
    else:
        _print_human(report, args.config_only)

    if args.config_only:
        return 0 if report.config_ok else 1
    return 0 if report.ready else 1


if __name__ == "__main__":
    sys.exit(main())
