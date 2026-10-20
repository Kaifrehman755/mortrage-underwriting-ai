#!/usr/bin/env python3
"""Dataset validator (R21 deliverable, F-18).

Static and read-only: validates the on-disk reference-rate dataset against the canonical
contracts. It never writes, never connects to a database, and never fetches anything.

Checks
------
1. Every ``data/processed/reference_rates/*.jsonl`` row parses as ``ReferenceRateCreate``.
2. Every processed row declares provenance (``source_url`` + ``source_record_hash``).
3. Every ``data/processed/manifests/*.json`` parses as ``IngestionRunAccounting`` (which
   enforces the row-accounting invariant).
4. Every ``data/quarantine/*.jsonl`` row parses as ``QuarantineRecord`` with a known reason code.

Exit code 0 when everything validates, 1 when any category has failures.

Usage::

    python scripts/validate_dataset.py
    python scripts/validate_dataset.py --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND = REPO_ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.ingestion.quarantine import (
    IngestionRunAccounting,
    QuarantineReason,
    QuarantineRecord,
)
from app.schemas.transaction import ReferenceRateCreate
from pydantic import ValidationError

PROCESSED_DIR = REPO_ROOT / "data" / "processed" / "reference_rates"
MANIFEST_DIR = REPO_ROOT / "data" / "processed" / "manifests"
QUARANTINE_DIR = REPO_ROOT / "data" / "quarantine"

MAX_ERRORS_PER_CATEGORY = 20
_KNOWN_REASON_CODES = {reason.value for reason in QuarantineReason}


def _iter_jsonl(path: Path):
    with open(path, encoding="utf-8") as handle:
        for line_no, raw in enumerate(handle, start=1):
            line = raw.strip()
            if line:
                yield line_no, line


def validate_processed() -> tuple[int, int, list[str]]:
    """Return (files, rows_checked, errors)."""
    errors: list[str] = []
    files = 0
    rows = 0
    for path in sorted(PROCESSED_DIR.glob("*.jsonl")):
        files += 1
        for line_no, line in _iter_jsonl(path):
            rows += 1
            try:
                record = ReferenceRateCreate.model_validate_json(line)
            except ValidationError as exc:
                errors.append(f"{path.name}:{line_no}: {exc.error_count()} validation error(s)")
                continue
            if not record.source_url or not record.source_record_hash:
                errors.append(f"{path.name}:{line_no}: missing provenance")
    return files, rows, errors


def validate_manifests() -> tuple[int, list[str]]:
    errors: list[str] = []
    files = 0
    for path in sorted(MANIFEST_DIR.glob("*.json")):
        files += 1
        try:
            accounting = IngestionRunAccounting.model_validate_json(path.read_text(encoding="utf-8"))
        except ValidationError as exc:
            errors.append(f"{path.name}: {exc.error_count()} validation error(s)")
            continue
        if accounting.finished_at is None:
            errors.append(f"{path.name}: run did not finish (finished_at is null)")
    return files, errors


def validate_quarantine() -> tuple[int, int, list[str]]:
    errors: list[str] = []
    files = 0
    rows = 0
    for path in sorted(QUARANTINE_DIR.glob("*.jsonl")):
        files += 1
        for line_no, line in _iter_jsonl(path):
            rows += 1
            try:
                record = QuarantineRecord.model_validate_json(line)
            except ValidationError as exc:
                errors.append(f"{path.name}:{line_no}: {exc.error_count()} validation error(s)")
                continue
            if record.reason_code.value not in _KNOWN_REASON_CODES:
                errors.append(f"{path.name}:{line_no}: unknown reason_code {record.reason_code!r}")
    return files, rows, errors


def _truncate(errors: list[str]) -> list[str]:
    if len(errors) <= MAX_ERRORS_PER_CATEGORY:
        return errors
    return errors[:MAX_ERRORS_PER_CATEGORY] + [f"... {len(errors) - MAX_ERRORS_PER_CATEGORY} more"]


def run_checks() -> dict[str, object]:
    processed_files, processed_rows, processed_errors = validate_processed()
    manifest_files, manifest_errors = validate_manifests()
    quarantine_files, quarantine_rows, quarantine_errors = validate_quarantine()
    errors = processed_errors + manifest_errors + quarantine_errors
    return {
        "ok": not errors,
        "processed": {"files": processed_files, "rows": processed_rows, "errors": processed_errors},
        "manifests": {"files": manifest_files, "errors": manifest_errors},
        "quarantine": {
            "files": quarantine_files,
            "rows": quarantine_rows,
            "errors": quarantine_errors,
        },
        "error_count": len(errors),
    }


def _print_human(report: dict[str, object]) -> None:
    processed = report["processed"]
    manifests = report["manifests"]
    quarantine = report["quarantine"]
    print("Dataset validation (R21 / F-18)")
    print(
        f"  processed:  {processed['files']} file(s), {processed['rows']} row(s), "
        f"{len(processed['errors'])} error(s)"
    )
    print(f"  manifests:  {manifests['files']} file(s), {len(manifests['errors'])} error(s)")
    print(
        f"  quarantine: {quarantine['files']} file(s), {quarantine['rows']} row(s), "
        f"{len(quarantine['errors'])} error(s)"
    )
    for category in ("processed", "manifests", "quarantine"):
        for message in _truncate(report[category]["errors"]):  # type: ignore[index]
            print(f"  - {message}")
    print(f"Result: {'OK' if report['ok'] else 'FAIL'}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the on-disk reference-rate dataset.")
    parser.add_argument("--json", action="store_true", help="Emit a JSON report")
    args = parser.parse_args(argv)

    report = run_checks()
    if args.json:
        print(json.dumps(report, indent=2, default=str))
    else:
        _print_human(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
