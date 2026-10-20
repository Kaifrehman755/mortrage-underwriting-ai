"""Source readiness audit and verification script.

Validates data/source_readiness.csv and audits:
1. Completeness of required fields.
2. Valid schema types and enumerations.
3. Safety invariants (no reference rate marked as transaction price, no source approved without review).
4. Connectivity check on source portals (optional --verify-connectivity --timeout).
5. Reference-rate fixture provenance (optional --verify-fixtures): fixtures must use local/synthetic
   provenance and must never claim a fabricated official government URL (F-03).
6. Versioned market-index provenance (optional --verify-fixtures): the HPI series must carry
   source, publication date, units and a truthful verification status (F-02).
"""

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

REQUIRED_FIELDS = [
    "state_code",
    "source_name",
    "source_url",
    "data_category",
    "access_method",
    "api_available",
    "sample_download_available",
    "historical_coverage",
    "residential_coverage",
    "transaction_price_available",
    "license_review_status",
    "commercial_use_allowed",
    "redistribution_allowed",
    "last_checked_at",
    "evidence_url",
    "next_action",
    "decision",
]

VALID_ACCESS_METHODS = {
    "API",
    "downloadable file",
    "manual authorized export",
    "licensed provider",
    "unknown",
}

VALID_LICENSE_STATUSES = {
    "approved",
    "pending_review",
    "restricted",
    "rejected",
}

VALID_DECISIONS = {
    "approved",
    "pending_review",
    "rejected",
    "hold",
}

TRI_STATE_VALUES = {"true", "false", "unknown"}


def audit_source_readiness(csv_path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Audit the source readiness CSV for schema and invariant compliance."""
    errors: list[str] = []
    records: list[dict[str, Any]] = []

    if not csv_path.exists():
        return [], [f"Source readiness file not found: {csv_path}"]

    with open(csv_path, mode="r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        missing_headers = [col for col in REQUIRED_FIELDS if col not in (reader.fieldnames or [])]
        if missing_headers:
            errors.append(f"Missing required columns in CSV: {missing_headers}")
            return [], errors

        for idx, row in enumerate(reader, start=2):
            source_id = f"{row.get('state_code', '?')}:{row.get('source_name', '?')}"

            # Check access method enum
            acc_method = row.get("access_method", "")
            if acc_method not in VALID_ACCESS_METHODS:
                errors.append(
                    f"Line {idx} ({source_id}): Invalid access_method '{acc_method}'. Must be one of {VALID_ACCESS_METHODS}"
                )

            # Check boolean/tri-state fields
            for field in [
                "api_available",
                "sample_download_available",
                "residential_coverage",
                "transaction_price_available",
                "commercial_use_allowed",
                "redistribution_allowed",
            ]:
                val = str(row.get(field, "")).strip().lower()
                if val not in TRI_STATE_VALUES:
                    errors.append(
                        f"Line {idx} ({source_id}): Field '{field}' has invalid value '{val}'. Must be true, false, or unknown."
                    )

            # Check license review status
            lic_status = row.get("license_review_status", "")
            if lic_status not in VALID_LICENSE_STATUSES:
                errors.append(
                    f"Line {idx} ({source_id}): Invalid license_review_status '{lic_status}'"
                )

            # Check decision
            decision = row.get("decision", "")
            if decision not in VALID_DECISIONS:
                errors.append(f"Line {idx} ({source_id}): Invalid decision '{decision}'")

            # Invariant 1: Reference rates must never be marked as containing transaction prices
            if (
                row.get("data_category") == "reference_rate"
                and str(row.get("transaction_price_available")).lower() == "true"
            ):
                errors.append(
                    f"Line {idx} ({source_id}): Invariant violation! Reference rates must never be marked as actual transaction prices."
                )

            # Invariant 2: Cannot be approved without approved license review status
            if decision == "approved" and lic_status != "approved":
                errors.append(
                    f"Line {idx} ({source_id}): Decision is 'approved' but license_review_status is '{lic_status}'. Approval gate failed."
                )

            records.append(row)

    return records, errors


def print_readiness_report(records: list[dict[str, Any]], errors: list[str]) -> None:
    print("=" * 80)
    print(" Indian Residential Property Valuation Agent - Source Readiness Audit")
    print("=" * 80)

    if errors:
        print("\n[!] AUDIT FAILED WITH ERRORS:")
        for err in errors:
            print(f"  - {err}")
        return

    print(f"\n[OK] Audited {len(records)} candidate sources across states.\n")
    print(f"{'State':<6} | {'Source Name':<42} | {'Category':<20} | {'Decision':<14}")
    print("-" * 86)
    for rec in records:
        print(
            f"{rec['state_code']:<6} | {rec['source_name'][:42]:<42} | {rec['data_category']:<20} | {rec['decision']:<14}"
        )

    print("\nSummary by State & Decision:")
    state_summary: dict[str, dict[str, int]] = {}
    for rec in records:
        st = rec["state_code"]
        dec = rec["decision"]
        state_summary.setdefault(st, {}).setdefault(dec, 0)
        state_summary[st][dec] += 1

    for st, counts in sorted(state_summary.items()):
        items = ", ".join(f"{k}: {v}" for k, v in counts.items())
        print(f"  {st:<5} -> {items}")


def verify_fixture_provenance(fixtures_dir: Path) -> list[str]:
    """F-03: reference-rate fixtures must carry honest local/synthetic provenance.

    A fixture row must never claim a fabricated official government URL; every row must use a
    ``local://synthetic/...`` source_url and carry a ``[SYNTHETIC DEV FIXTURE ...]`` notes marker.
    """
    errors: list[str] = []
    if not fixtures_dir.exists():
        return [f"Fixture directory not found: {fixtures_dir}"]

    for csv_path in sorted(fixtures_dir.glob("*.csv")):
        with open(csv_path, mode="r", encoding="utf-8", newline="") as handle:
            for idx, row in enumerate(csv.DictReader(handle), start=2):
                url = str(row.get("source_url", "")).strip()
                if not url.startswith("local://synthetic/"):
                    errors.append(
                        f"{csv_path.name} line {idx}: fixture source_url '{url}' is not local synthetic provenance"
                    )
                if "SYNTHETIC DEV FIXTURE" not in str(row.get("notes", "")):
                    errors.append(
                        f"{csv_path.name} line {idx}: missing synthetic provenance marker in notes"
                    )
    return errors


def verify_market_index_provenance(index_path: Path) -> tuple[list[str], str]:
    """F-02: the versioned market index must carry honest provenance.

    An ``unverified`` fixture is the expected state, so this does not fail on it; it only
    flags a file that over-claims verification while its identifying provenance fields are
    still unset. Returns ``(errors, status_line)``.
    """
    errors: list[str] = []
    if not index_path.exists():
        return [f"Market index file not found: {index_path}"], ""
    try:
        payload = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"Market index file {index_path.name} is not valid JSON: {exc}"], ""

    for field in (
        "source_name",
        "source_url",
        "publication_date",
        "units",
        "verification_status",
        "series",
    ):
        if field not in payload:
            errors.append(f"{index_path.name}: missing required provenance field '{field}'")

    status = str(payload.get("verification_status", "")).strip().lower()
    if status == "verified":
        for field in ("source_url", "publication_date", "retrieved_at"):
            value = str(payload.get(field, "")).strip().lower()
            if not value or value.startswith("todo"):
                errors.append(
                    f"{index_path.name}: verification_status='verified' but '{field}' "
                    f"is unset ('{payload.get(field, '')}')"
                )

    line = (
        f"market_index {payload.get('series_id', index_path.stem)}: "
        f"verification_status={payload.get('verification_status', '?')}, "
        f"periods={len(payload.get('series', {}))}"
    )
    return errors, line


def check_connectivity(records: list[dict[str, Any]], timeout: float) -> list[str]:
    """Best-effort reachability check for approved sources (docstring item 4).

    Only approved sources are fetched; non-HTTP URLs (e.g. ``local://``) are skipped. Transport
    failures are reported, not raised.
    """
    import urllib.error
    import urllib.request

    results: list[str] = []
    for row in records:
        if str(row.get("decision", "")).strip().lower() != "approved":
            continue
        for field in ("source_url", "evidence_url"):
            url = str(row.get(field, "")).strip()
            if not url.lower().startswith(("http://", "https://")):
                continue
            status = "unreachable"
            try:
                request = urllib.request.Request(
                    url, method="HEAD", headers={"User-Agent": "source-readiness-check/1.0"}
                )
                with urllib.request.urlopen(request, timeout=timeout) as response:
                    status = f"HTTP {response.status}"
            except urllib.error.HTTPError as exc:
                status = f"HTTP {exc.code}"
            except (OSError, ValueError) as exc:
                status = f"UNREACHABLE ({type(exc).__name__})"
            results.append(f"{row.get('state_code', '?')}:{field} {url} -> {status}")
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit data source readiness register.")
    parser.add_argument(
        "--file",
        default="data/source_readiness.csv",
        help="Path to source_readiness.csv (default: data/source_readiness.csv)",
    )
    parser.add_argument(
        "--fixtures-dir",
        default="data/reference_rates",
        help="Directory holding reference-rate fixtures (default: data/reference_rates)",
    )
    parser.add_argument(
        "--verify-fixtures",
        action="store_true",
        help="Enforce local/synthetic provenance on reference-rate fixtures and the market index (F-02/F-03).",
    )
    parser.add_argument(
        "--market-index",
        default="data/market_indices/rbi_hpi_urban_lucknow.json",
        help="Path to the versioned market-index JSON (default: data/market_indices/rbi_hpi_urban_lucknow.json)",
    )
    parser.add_argument(
        "--verify-connectivity",
        action="store_true",
        help="Fetch approved source URLs to confirm reachability (requires network).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="Per-request timeout in seconds for --verify-connectivity (default: 10).",
    )
    args = parser.parse_args()

    records, errors = audit_source_readiness(Path(args.file))
    print_readiness_report(records, errors)

    if args.verify_fixtures:
        fixture_errors = verify_fixture_provenance(Path(args.fixtures_dir))
        if fixture_errors:
            print("\n[!] FIXTURE PROVENANCE CHECK FAILED:")
            for err in fixture_errors:
                print(f"  - {err}")
            errors.extend(fixture_errors)
        else:
            print(
                "\n[OK] Fixture provenance check passed: all reference-rate fixtures use "
                "local://synthetic/ provenance."
            )

        index_errors, index_line = verify_market_index_provenance(Path(args.market_index))
        if index_errors:
            print("\n[!] MARKET-INDEX PROVENANCE CHECK FAILED:")
            for err in index_errors:
                print(f"  - {err}")
            errors.extend(index_errors)
        else:
            print(f"\n[OK] Market-index provenance check passed: {index_line}.")

    if args.verify_connectivity:
        print("\nConnectivity check (approved sources only):")
        results = check_connectivity(records, args.timeout)
        if results:
            for line in results:
                print(f"  - {line}")
        else:
            print("  (no approved HTTP sources to check)")

    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
