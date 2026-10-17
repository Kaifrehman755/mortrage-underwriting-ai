#!/usr/bin/env python3
"""Canonical dataset builder (R21 deliverable, F-18).

Builds the processed reference-rate dataset from the raw snapshot files by driving the
**canonical, gated** ingestion pipeline (``ReferenceRateFileProvider``) — the same code path
used in production. It does not re-implement any parsing or validation.

Safety properties
-----------------
* **Dry-run by default.** Nothing is written unless ``--write`` is passed.
* **The source-approval gate is enforced, never bypassed.** A source whose register decision is
  not ``approved`` is reported as ``BLOCKED`` and the build fails closed (exit 2). Because the
  F-03 reference-rate fixtures are deliberately ``pending_review``, this script currently
  refuses all four states — that refusal is the correct, honest outcome, not a bug.
* No network access and no database access.

Usage::

    python scripts/build_dataset.py                 # dry-run, all states
    python scripts/build_dataset.py --state UP      # one state
    python scripts/build_dataset.py --write         # persist accepted rows + manifest
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND = REPO_ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.ingestion.deduplicate import DeduplicationIndex
from app.ingestion.provider import ReferenceRateFileProvider
from app.ingestion.registry import SourceApprovalError, default_registry

STATE_SOURCES: dict[str, tuple[str, str]] = {
    "UP": ("IGRSUP Circle Rate Services", "data/reference_rates/up_lucknow_circle_rates_2024.csv"),
    "MH": ("IGR Maharashtra eASR (Ready Reckoner Rates)", "data/reference_rates/mh_mumbai_ready_reckoner_2024.csv"),
    "KA": ("Kaveri 2.0 Guidance Value Services", "data/reference_rates/ka_bengaluru_guidance_values_2024.csv"),
    "TS": ("IGRS Telangana Market Value & Unit Rates", "data/reference_rates/ts_hyderabad_market_values_2024.csv"),
}

PROCESSED_DIR = REPO_ROOT / "data" / "processed" / "reference_rates"
MANIFEST_DIR = REPO_ROOT / "data" / "processed" / "manifests"

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_BLOCKED = 2


def build_state(state_code: str, write: bool) -> str:
    """Returns 'built', 'blocked' or 'error'."""
    source_name, rel_file = STATE_SOURCES[state_code]
    snapshot = REPO_ROOT / rel_file

    print(f"\n=== {state_code} | {source_name} ===")
    print(f"snapshot: {rel_file}")

    try:
        source = default_registry.verify_approval(state_code, source_name)
    except SourceApprovalError as exc:
        print(f"[BLOCKED] source-approval gate: {exc}")
        print("          Refusing to build from an unapproved source (F-03). No output written.")
        return "blocked"

    if not snapshot.exists():
        print(f"[ERROR] snapshot file not found: {snapshot}")
        return "error"

    provider = ReferenceRateFileProvider(source=source, dedup_index=DeduplicationIndex())
    try:
        accepted, accounting, quarantined = provider.ingest_file(snapshot)
    except Exception as exc:  # noqa: BLE001 - report, do not crash the batch
        print(f"[ERROR] {type(exc).__name__}: {exc}")
        return "error"

    total = (
        accounting.rows_accepted
        + accounting.rows_quarantined
        + accounting.rows_duplicate
        + accounting.rows_rejected
    )
    print(f"run {accounting.run_id}: received={accounting.rows_received} accepted={accounting.rows_accepted} "
          f"quarantined={accounting.rows_quarantined} duplicate={accounting.rows_duplicate} "
          f"rejected={accounting.rows_rejected}")
    if accounting.rows_received != total:
        print("[ERROR] row-accounting invariant violated")
        return "error"

    for record in quarantined:
        print(f"  quarantined [{record.reason_code.value}] {record.reason_detail}")

    if not write:
        print("[DRY-RUN] accepted rows not persisted (pass --write to persist).")
        return "built"

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    out_file = PROCESSED_DIR / f"{snapshot.stem}.jsonl"
    with open(out_file, "w", encoding="utf-8") as handle:
        for record in accepted:
            handle.write(record.model_dump_json() + "\n")
    manifest_file = MANIFEST_DIR / f"manifest_{accounting.run_id}.json"
    manifest_file.write_text(accounting.model_dump_json(indent=2), encoding="utf-8")
    print(f"[WROTE] {len(accepted)} row(s) -> {out_file.relative_to(REPO_ROOT)}")
    print(f"[WROTE] manifest -> {manifest_file.relative_to(REPO_ROOT)}")
    return "built"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the processed reference-rate dataset (gated).")
    parser.add_argument("--state", action="append", choices=sorted(STATE_SOURCES), help="State code (repeatable)")
    parser.add_argument("--write", action="store_true", help="Persist output (default: dry-run)")
    args = parser.parse_args(argv)

    states = args.state or sorted(STATE_SOURCES)
    print("Canonical dataset builder (R21 / F-18)")
    print(f"mode: {'WRITE' if args.write else 'DRY-RUN'} | states: {', '.join(states)}")

    outcomes = {state: build_state(state, args.write) for state in states}

    built = [s for s, o in outcomes.items() if o == "built"]
    blocked = [s for s, o in outcomes.items() if o == "blocked"]
    errored = [s for s, o in outcomes.items() if o == "error"]
    print(f"\nsummary: built={built or '[]'} blocked={blocked or '[]'} errors={errored or '[]'}")

    if errored:
        return EXIT_ERROR
    if blocked:
        print("One or more sources are not approved; see data/source_readiness.csv (F-03).")
        return EXIT_BLOCKED
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
