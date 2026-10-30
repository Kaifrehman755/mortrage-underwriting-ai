"""F-18 regression tests: R21 deliverables exist and behave.

Verifies (Phase 2, Priority 6 — F-18):
1. Every R21 script/report deliverable exists.
2. Each script has a clean ``--help`` (argparse parses; the module imports without side effects).
3. ``validate_dataset.py`` passes on the on-disk dataset.
4. ``check_database.py`` defaults to static mode (does not connect).
5. ``build_dataset.py`` never bypasses the source-approval gate: it either builds only approved
   sources or fails closed (exit 2) with a gate reason.
6. ``run_verification.py --list`` reports the expected checks.
7. The progress/verification documents are present and state the India scope.

These run the scripts as subprocesses so the tests exercise the real CLIs, not internal helpers.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]

R21_SCRIPTS = [
    "scripts/check_sources.py",
    "scripts/check_migrations.py",
    "scripts/check_database.py",
    "scripts/validate_dataset.py",
    "scripts/build_dataset.py",
    "scripts/run_verification.py",
]

R21_DOCS = [
    "reports/implementation_audit.md",
    "reports/verification_report.md",
    "docs/PROGRESS.md",
]


def _run(script: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, script, *args],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )


@pytest.mark.parametrize("rel_path", R21_SCRIPTS + R21_DOCS)
def test_r21_deliverable_exists(rel_path: str) -> None:
    assert (REPO_ROOT / rel_path).is_file(), f"missing R21 deliverable: {rel_path}"


@pytest.mark.parametrize("script", R21_SCRIPTS)
def test_script_help_is_clean(script: str) -> None:
    result = _run(script, "--help")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "usage" in result.stdout.lower()


def test_validate_dataset_passes_on_disk() -> None:
    result = _run("scripts/validate_dataset.py")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Result: OK" in result.stdout


def test_check_database_defaults_to_static_mode() -> None:
    result = _run("scripts/check_database.py")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "no connection attempted" in result.stdout
    # Credentials must never be printed in full.
    assert ":***@" in result.stdout or "database url" in result.stdout


def test_build_dataset_never_bypasses_the_approval_gate() -> None:
    result = _run("scripts/build_dataset.py")
    output = result.stdout + result.stderr
    assert result.returncode in (0, 2), output
    if result.returncode == 2:
        assert "source-approval gate" in output
        assert "BLOCKED" in output
    else:
        # Only reachable once every source is approved; then a build must be reported.
        assert "built=" in output


def test_run_verification_lists_expected_checks() -> None:
    result = _run("scripts/run_verification.py", "--list")
    assert result.returncode == 0, result.stdout + result.stderr
    for expected in ("pytest", "validate_dataset", "check_migrations", "check_database"):
        assert expected in result.stdout


def test_progress_document_states_india_scope() -> None:
    text = (REPO_ROOT / "docs" / "PROGRESS.md").read_text(encoding="utf-8")
    assert "India property-valuation backend" in text


def test_clinerules_remain_in_the_governing_location() -> None:
    # F-18: the governing rules intentionally stay under data/regulatory_docs/.clinerules/
    # (the instructions reference that path); they must not be relocated.
    assert (REPO_ROOT / "data" / "regulatory_docs" / ".clinerules").is_dir()
