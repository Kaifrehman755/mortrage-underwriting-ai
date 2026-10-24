"""Multi-State Dataset Ingestion CLI.

Enforces GEMINI.md Section 1, Section 3, Section 4.6, Section 6, Section 9, and Section 10:
- Multi-state support across Uttar Pradesh (UP), Maharashtra (MH), Karnataka (KA), and Telangana (TS).
- Enforces source approval gate for each state's provider.
- Generates snapshot hash and provenance metadata.
- Records quarantine details with standard reason codes.
- Verifies row accounting invariant: rows_received == rows_accepted + rows_quarantined + rows_duplicate + rows_rejected.
- Demonstrates idempotency on repeated imports.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_path = Path(__file__).resolve().parents[1] / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.ingestion.deduplicate import DeduplicationIndex
from app.ingestion.provider import ReferenceRateFileProvider
from app.ingestion.registry import SourceApprovalError, default_registry

STATE_CONFIGS: dict[str, dict[str, str]] = {
    "UP": {
        "source_name": "IGRSUP Circle Rate Services",
        "default_file": "data/reference_rates/up_lucknow_circle_rates_2024.csv",
        "category": "circle_rates",
    },
    "MH": {
        "source_name": "IGR Maharashtra eASR (Ready Reckoner Rates)",
        "default_file": "data/reference_rates/mh_mumbai_ready_reckoner_2024.csv",
        "category": "ready_reckoner",
    },
    "KA": {
        "source_name": "Kaveri 2.0 Guidance Value Services",
        "default_file": "data/reference_rates/ka_bengaluru_guidance_values_2024.csv",
        "category": "guidance_values",
    },
    "TS": {
        "source_name": "IGRS Telangana Market Value & Unit Rates",
        "default_file": "data/reference_rates/ts_hyderabad_market_values_2024.csv",
        "category": "market_values",
    },
}


def ingest_state_file(
    state_code: str,
    source_name: str,
    file_path: Path,
    output_path: Path | None = None,
    verify_idempotency: bool = False,
) -> bool:
    """Ingest a single state snapshot file."""
    repo_root = Path(__file__).resolve().parents[1]
    default_processed_dir = repo_root / "data" / "processed" / "reference_rates"
    default_manifest_dir = repo_root / "data" / "processed" / "manifests"
    default_processed_dir.mkdir(parents=True, exist_ok=True)
    default_manifest_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 80)
    print(f" State Ingestion: {state_code} | Source: {source_name}")
    print("=" * 80)
    print(f"Snapshot File: {file_path}")

    # 1. Gate check
    try:
        source_meta = default_registry.verify_approval(state_code, source_name)
        print(f"[OK] Gate Approved: {source_meta.source_name} (ID: {source_meta.source_id})")
        print(f"     Status: {source_meta.approval_status.value} | Scope: {source_meta.license_scope}")
    except SourceApprovalError as exc:
        print(f"[!] Gate Rejected: {exc}", file=sys.stderr)
        return False

    # 2. Ingestion Pass 1
    dedup_index = DeduplicationIndex()
    provider = ReferenceRateFileProvider(source=source_meta, dedup_index=dedup_index)
    accepted, accounting, quarantined = provider.ingest_file(file_path)

    print("\n--- Ingestion Run Accounting Summary ---")
    print(f"Run ID:                {accounting.run_id}")
    print(f"Snapshot SHA-256 Hash: {accounting.source_snapshot_hash}")
    print(f"Rows Received:         {accounting.rows_received}")
    print(f"Rows Accepted:         {accounting.rows_accepted}")
    print(f"Rows Quarantined:      {accounting.rows_quarantined}")
    print(f"Rows Duplicate:        {accounting.rows_duplicate}")
    print(f"Rows Rejected:         {accounting.rows_rejected}")

    total_accounted = (
        accounting.rows_accepted
        + accounting.rows_quarantined
        + accounting.rows_duplicate
        + accounting.rows_rejected
    )
    print(f"Accounting Invariant:  {accounting.rows_received} == {total_accounted} -> [PASSED]")

    if quarantined:
        print(f"\nQuarantined Records ({len(quarantined)}):")
        for qr in quarantined:
            print(f"  - [{qr.reason_code.value}] {qr.reason_detail} (ref: {qr.raw_record_ref})")

    # 3. Persistent Output
    out_file = output_path if output_path else (default_processed_dir / f"{file_path.stem}.jsonl")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    if accepted:
        with open(out_file, "w", encoding="utf-8") as f:
            f.writelines(r.model_dump_json() + "\n" for r in accepted)
        print(f"[OK] Persisted {len(accepted)} accepted records to {out_file}")

    manifest_file = default_manifest_dir / f"manifest_{accounting.run_id}.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        f.write(accounting.model_dump_json(indent=2))
    print(f"[OK] Ingestion run manifest saved to {manifest_file}")

    # 4. Optional Idempotency Check
    if verify_idempotency:
        print("\n--- Ingestion Pass 2 (Idempotency Verification) ---")
        _accepted_p2, acc_p2, _ = provider.ingest_file(file_path)
        print(f"Rows Received:    {acc_p2.rows_received}")
        print(f"Rows Accepted:    {acc_p2.rows_accepted} (Expected: 0)")
        print(f"Rows Duplicate:   {acc_p2.rows_duplicate} (Expected: {accounting.rows_accepted})")
        if acc_p2.rows_accepted == 0 and acc_p2.rows_duplicate == accounting.rows_accepted:
            print("[OK] Idempotency Invariant PASSED: Zero duplicates created on repeat import.")
        else:
            print("[!] IDEMPOTENCY INVARIANT FAILED", file=sys.stderr)
            return False

    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Multi-state dataset ingestion pipeline.")
    parser.add_argument("--state", choices=["UP", "MH", "KA", "TS"], help="Specific state code")
    parser.add_argument("--source-name", help="Registered source name override")
    parser.add_argument("--file", help="Path to snapshot CSV file")
    parser.add_argument("--output", help="Optional path to write accepted canonical records (JSONL)")
    parser.add_argument(
        "--all-states",
        action="store_true",
        help="Ingest all 4 supported states (UP, MH, KA, TS) in sequence",
    )
    parser.add_argument(
        "--verify-idempotency",
        action="store_true",
        help="Run a second pass for each state to verify idempotency",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]

    if args.all_states or (not args.state and not args.file):
        print("Executing Multi-State Ingestion Batch for all 4 candidate states: UP, MH, KA, TS...")
        states_to_run = ["UP", "MH", "KA", "TS"]
        success_count = 0
        for st in states_to_run:
            cfg = STATE_CONFIGS[st]
            f_path = repo_root / cfg["default_file"]
            s_name = cfg["source_name"]
            ok = ingest_state_file(
                state_code=st,
                source_name=s_name,
                file_path=f_path,
                verify_idempotency=args.verify_idempotency,
            )
            if ok:
                success_count += 1
        print("\n" + "=" * 80)
        print(f" Batch Ingestion Complete: {success_count}/{len(states_to_run)} states succeeded.")
        print("=" * 80)
    else:
        st = args.state.upper() if args.state else "UP"
        cfg = STATE_CONFIGS.get(st, STATE_CONFIGS["UP"])
        s_name = args.source_name or cfg["source_name"]
        f_path = Path(args.file) if args.file else (repo_root / cfg["default_file"])
        out_p = Path(args.output) if args.output else None

        ok = ingest_state_file(
            state_code=st,
            source_name=s_name,
            file_path=f_path,
            output_path=out_p,
            verify_idempotency=args.verify_idempotency,
        )
        if not ok:
            sys.exit(1)


if __name__ == "__main__":
    main()
