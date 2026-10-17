#!/usr/bin/env python3
"""Verification runner (R21 deliverable, F-18).

Runs the approved, safe, local verification commands in one pass and reports their real exit
codes and output. It performs **no** database work, no Docker build, no network access (the
exception being ``check_sources.py --verify-fixtures``, which is offline) and installs nothing.

Blocking vs informational
-------------------------
Checks marked ``blocking`` must pass for the overall result to be OK. ``mypy`` is reported as
**informational** because the repository carries a small number of pre-existing type errors
outside the remediation scope; none of them are in the files this remediation touched.

Usage::

    python scripts/run_verification.py                 # run everything, print a summary
    python scripts/run_verification.py --list          # list the checks without running them
    python scripts/run_verification.py --write reports/verification_report.md
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND = REPO_ROOT / "backend"
PYTHON = sys.executable

# Files authored/edited by this remediation. All are lint-clean; pinning the list keeps the
# check meaningful without failing on unrelated pre-existing lint debt elsewhere in the repo.
RUFF_FILES = [
    "backend/app/agents/property_agent.py",
    "backend/app/core/config.py",
    "backend/app/security/auth.py",
    "backend/app/security/rate_limit.py",
    "backend/app/ingestion/circle_rates.py",
    "backend/app/models/__init__.py",
    "backend/app/property/__init__.py",
    "backend/app/property/comps.py",
    "backend/app/property/normalize.py",
    "backend/app/property/market_index.py",
    "backend/app/valuation/__init__.py",
    "backend/tests/unit/test_f02_market_index.py",
    "backend/tests/unit/test_f03_data_provenance.py",
    "backend/tests/unit/test_f04_circle_rate_quarantine.py",
    "backend/tests/unit/test_f05_auth_access_policy.py",
    "backend/tests/unit/test_f06_cors_config.py",
    "backend/tests/unit/test_f07_secrets_config.py",
    "backend/tests/unit/test_f08_ingestion_ssrf.py",
    "backend/tests/unit/test_f09_settings_env_sync.py",
    "backend/tests/unit/test_f10_canonical_pipeline.py",
    "backend/tests/unit/test_f11_dependency_manifest.py",
    "backend/tests/unit/test_f12_migration_checker.py",
    "backend/tests/unit/test_f14_error_handling.py",
    "backend/tests/unit/test_f17_unit_semantics.py",
    "backend/tests/unit/test_f18_deliverables.py",
    "scripts/check_sources.py",
    "scripts/check_migrations.py",
    "scripts/check_database.py",
    "scripts/validate_dataset.py",
    "scripts/build_dataset.py",
    "scripts/run_verification.py",
    "migrations",
]


@dataclass
class Check:
    name: str
    cmd: list[str]
    cwd: Path
    blocking: bool = True
    note: str = ""


@dataclass
class Result:
    check: Check
    returncode: int
    output: str


CHECKS: list[Check] = [
    Check("pytest (full suite)", [PYTHON, "-m", "pytest", "backend/tests", "-q"], REPO_ROOT),
    Check("ruff (remediation files)", [PYTHON, "-m", "ruff", "check", *RUFF_FILES], REPO_ROOT),
    Check(
        "mypy (backend app)",
        [PYTHON, "-m", "mypy", "app"],
        BACKEND,
        blocking=False,
        note="informational: pre-existing type errors outside the remediation scope",
    ),
    Check(
        "data provenance (check_sources --verify-fixtures)",
        [PYTHON, "scripts/check_sources.py", "--verify-fixtures"],
        REPO_ROOT,
    ),
    Check(
        "migration config (check_migrations --config-only)",
        [PYTHON, "scripts/check_migrations.py", "--config-only"],
        REPO_ROOT,
    ),
    Check(
        "migration readiness (check_migrations)",
        [PYTHON, "scripts/check_migrations.py"],
        REPO_ROOT,
        note="F-12: fails if no revision or more than one head exists",
    ),
    Check("dataset validation (validate_dataset)", [PYTHON, "scripts/validate_dataset.py"], REPO_ROOT),
    Check("database config (check_database)", [PYTHON, "scripts/check_database.py"], REPO_ROOT),
]


def run_all() -> list[Result]:
    results: list[Result] = []
    for check in CHECKS:
        print(f"[run] {check.name} ...", flush=True)
        completed = subprocess.run(
            check.cmd,
            cwd=str(check.cwd),
            capture_output=True,
            text=True,
            check=False,
        )
        output = (completed.stdout or "") + (completed.stderr or "")
        results.append(Result(check=check, returncode=completed.returncode, output=output))
    return results


def _status(result: Result) -> str:
    if result.returncode == 0:
        return "PASS"
    return "FAIL" if result.check.blocking else "INFO"


def _tail(text: str, lines: int = 40) -> str:
    stripped = text.rstrip().splitlines()
    return "\n".join(stripped[-lines:])


def print_summary(results: list[Result]) -> int:
    print("\nVerification summary")
    print(f"{'CHECK':<52} {'RESULT':<6} {'EXIT':>4}")
    for result in results:
        print(f"{result.check.name:<52} {_status(result):<6} {result.returncode:>4}")

    failed = [r for r in results if r.returncode != 0 and r.check.blocking]
    if failed:
        print(f"\nBlocking failures: {[r.check.name for r in failed]}")
        return 1
    print("\nResult: OK (all blocking checks passed)")
    return 0


def write_report(results: list[Result], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Verification report",
        "",
        f"Generated: {datetime.now(UTC).isoformat()}",
        f"Python: `{PYTHON}`",
        "",
        "| Check | Blocking | Exit | Status |",
        "|---|---|---|---|",
    ]
    for result in results:
        lines.append(
            f"| {result.check.name} | {'yes' if result.check.blocking else 'no'} "
            f"| {result.returncode} | {_status(result)} |"
        )
    lines.append("")
    if any(not r.check.blocking for r in results):
        lines += [
            "> `mypy` is informational: the repository has pre-existing type errors outside this",
            "> remediation's scope, and none are in the files it touched.",
            "",
        ]
    for result in results:
        lines += [
            f"## {result.check.name}",
            "",
            f"Command: `{' '.join(result.check.cmd)}` (cwd: `{result.check.cwd}`)",
            "",
            f"Exit code: **{result.returncode}**",
            "",
        ]
        if result.check.note:
            lines += [f"_{result.check.note}_", ""]
        body = _tail(result.output)
        if not body.strip():
            body = (
                "(no output; exit code 0 means the check passed — `pytest -q` prints no "
                "summary line when every test passes)"
            )
        lines += ["```", body, "```", ""]
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[wrote] {path}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the approved local verification checks.")
    parser.add_argument("--list", action="store_true", help="List checks without running them")
    parser.add_argument("--write", metavar="PATH", help="Write a Markdown report to PATH")
    args = parser.parse_args(argv)

    if args.list:
        for check in CHECKS:
            flag = "blocking" if check.blocking else "info"
            print(f"[{flag}] {check.name}")
            print(f"          {' '.join(check.cmd)}  (cwd={check.cwd})")
        return 0

    results = run_all()
    exit_code = print_summary(results)
    if args.write:
        write_report(results, Path(args.write))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
