"""F-12 regression tests: the migration-readiness checker behaves correctly.

Verifies (Phase 2, Priority 5 — F-12 / R21):
1. The Alembic configuration is present, targets the canonical ORM tree, and is credential-free.
2. The checker's revision inventory matches what is actually on disk (so its "F-12 open"
   report is trustworthy and cannot silently drift).
3. The CLI runs and its config-only mode succeeds.

Note: this does **not** assert that revisions exist. Generating/testing the initial revision
requires a live PostGIS database, which is outside the authorised scope; the checker reports that
gap explicitly instead.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "check_migrations.py"
VERSIONS_DIR = REPO_ROOT / "migrations" / "versions"


def _load_module():
    spec = importlib.util.spec_from_file_location("check_migrations", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Register before execution: the script uses `from __future__ import annotations`, and
    # dataclasses resolve type annotations via sys.modules.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_checker_reports_config_ok() -> None:
    report = _load_module().inspect_migration_tree()
    assert report.env_py and report.script_mako and report.alembic_ini
    assert report.canonical_target, "migrations/env.py must target app.database.models"
    assert report.url_has_no_credentials, "alembic.ini must not embed credentials (F-07)"
    assert report.versions_dir, "migrations/versions/ must exist"
    assert report.config_ok


def test_checker_revision_inventory_matches_disk() -> None:
    report = _load_module().inspect_migration_tree()
    expected = sorted(p.name for p in VERSIONS_DIR.glob("*.py") if p.name != "__init__.py")
    assert report.revision_files == expected
    if expected:
        assert len(report.heads) == 1
    else:
        assert report.heads == []
        assert report.ready is False  # no revisions yet => F-12 still open


def test_checker_cli_config_only_succeeds() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--config-only"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Config: OK" in result.stdout
