"""F-12 regression tests: the migration-readiness checker behaves correctly.

Verifies (Phase 2, Priority 5 — F-12 / R21):
1. The Alembic configuration is present, targets the canonical ORM tree, and is credential-free.
2. The checker's revision inventory matches what is actually on disk (so its readiness report is
   trustworthy and cannot silently drift).
3. The CLI runs and its config-only mode succeeds.

The initial revision was generated and its ``upgrade head`` / ``downgrade base`` were exercised
against the disposable local PostGIS database ``mortgage_underwriting_test``. The assertions below
pin that revision's shape so the destructive-autogenerate hazards (dropping PostGIS internals,
duplicate spatial indexes, the stale ``rate_inr_normalized`` column) cannot silently return.
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


# =========================================================================
# The generated initial revision is safe and matches the ratified schema
# =========================================================================

CANONICAL_TABLES = (
    "circle_rates",
    "data_sources",
    "ingestion_runs",
    "property_listings",
    "property_records",
    "property_transactions",
    "quarantine_records",
    "reference_rates",
    "valuation_comparables",
    "valuation_runs",
)


def _initial_revision_source() -> str:
    revisions = sorted(p for p in VERSIONS_DIR.glob("*.py") if p.name != "__init__.py")
    assert len(revisions) == 1, f"expected exactly one revision, found {revisions}"
    return revisions[0].read_text(encoding="utf-8")


def test_initial_revision_is_the_root_and_creates_canonical_tables() -> None:
    source = _initial_revision_source()
    assert "down_revision: str | None = None" in source
    for table in CANONICAL_TABLES:
        assert f"op.create_table('{table}'" in source, f"missing create_table for {table}"


def test_initial_revision_uses_ratified_column_name() -> None:
    source = _initial_revision_source()
    assert "'rate_inr_per_sqft'" in source
    assert "rate_inr_normalized" not in source


def test_initial_revision_never_manages_postgis_internals() -> None:
    source = _initial_revision_source()
    assert "spatial_ref_sys" not in source
    assert "schema='tiger'" not in source
    assert "schema='topology'" not in source


def test_spatial_index_is_owned_by_alembic_not_geoalchemy2() -> None:
    # F-12: GeoAlchemy2 must not auto-create the spatial index, otherwise it is created twice
    # (once by CREATE TABLE, once by the generated create_index).
    from app.database.models.property import PropertyRecord

    geometry = PropertyRecord.__table__.c["location"].type
    assert geometry.spatial_index is False
    index_names = {index.name for index in PropertyRecord.__table__.indexes}
    assert "idx_property_record_location" in index_names
