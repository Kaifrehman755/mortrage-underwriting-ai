"""F-04 regression tests: circle-rate ingestion must never silently drop rows.

Verifies (Phase 2, Priority 3 — F-04, hard-rule 13 / R6):
1. Every received row is accounted for: rows_received == accepted + quarantined
   (+ duplicate + rejected).
2. Invalid CSV/HTML rows are emitted as reason-coded ``QuarantineRecord`` objects
   and written to a quarantine JSONL log, never skipped with a log warning.
3. Rejections carry the correct reason codes (MISSING_REQUIRED_FIELD, MISSING_PRICE,
   INVALID_DATE).
4. A schema-validation failure is returned as a rejection rather than swallowed.
5. A page with no recognizable rate table fails loudly.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.ingestion.circle_rates import (
    CircleRateIngestor,
    CircleRateRejection,
    IngestionError,
    ParseOutcome,
)
from app.ingestion.quarantine import QuarantineReason

CIRCLE_RATES_SRC = (
    Path(__file__).resolve().parents[3] / "backend" / "app" / "ingestion" / "circle_rates.py"
)

CSV_HEADER = "district,tehsil,locality,circle rate per sqm,effective year\n"

HTML_TABLE = """
<html><body>
<table>
  <tr><th>District</th><th>Tehsil</th><th>Locality</th><th>Circle Rate per Sqm</th><th>Effective Year</th></tr>
  <tr><td>Lucknow</td><td>Lucknow Sadar</td><td>Gomti Nagar</td><td>54,000</td><td>2024</td></tr>
  <tr><td>Lucknow</td><td>Lucknow Sadar</td></tr>
  <tr><td>Lucknow</td><td>Lucknow Sadar</td><td>Aliganj</td><td>n/a</td><td>2024</td></tr>
</table>
</body></html>
"""


def _ingestor(tmp_path: Path) -> CircleRateIngestor:
    return CircleRateIngestor(
        source_url="local://synthetic/circle_rates",
        quarantine_dir=tmp_path,
        intake_dir=tmp_path,
    )


def _write_csv(tmp_path: Path, rows: list[str]) -> Path:
    path = tmp_path / "circle_rates.csv"
    path.write_text(CSV_HEADER + "".join(rows), encoding="utf-8")
    return path


# =========================================================================
# 1. CSV path: no silent drops, full accounting, reason codes, quarantine file
# =========================================================================


def test_csv_invalid_rows_are_quarantined_not_dropped(tmp_path: Path) -> None:
    path = _write_csv(
        tmp_path,
        [
            "Lucknow,Lucknow Sadar,Gomti Nagar,54000,2024\n",       # valid
            "Lucknow,Lucknow Sadar,Aliganj,,2024\n",                 # missing rate -> MISSING_REQUIRED_FIELD
            "Lucknow,Lucknow Sadar,Indira Nagar,free,2024\n",        # bad rate -> MISSING_PRICE
            "Lucknow,Lucknow Sadar,Hazratganj,60000,unknown\n",      # bad year -> INVALID_DATE
            "Lucknow,Lucknow Sadar,,55000,2024\n",                   # missing locality -> MISSING_REQUIRED_FIELD
        ],
    )

    result = _ingestor(tmp_path).ingest_file(path)
    accounting = result.accounting

    # No silent loss: every received row is either accepted or quarantined.
    assert accounting.rows_received == 5
    assert accounting.rows_accepted == 1
    assert accounting.rows_quarantined == 4
    assert accounting.rows_received == (
        accounting.rows_accepted
        + accounting.rows_quarantined
        + accounting.rows_duplicate
        + accounting.rows_rejected
    )

    assert len(result.records) == 1
    assert result.records[0].locality == "Gomti Nagar"

    reasons = {record.reason_code for record in result.quarantine}
    assert QuarantineReason.MISSING_REQUIRED_FIELD in reasons
    assert QuarantineReason.MISSING_PRICE in reasons
    assert QuarantineReason.INVALID_DATE in reasons
    assert all(record.reason_detail for record in result.quarantine)
    assert all(record.source_record_id for record in result.quarantine)

    # A quarantine JSONL log is written alongside the accounting.
    assert result.quarantine_path is not None
    assert result.quarantine_path.exists()
    lines = result.quarantine_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 4
    first = json.loads(lines[0])
    assert first["reason_code"] in {r.value for r in QuarantineReason}


def test_overlong_csv_row_is_quarantined(tmp_path: Path) -> None:
    path = _write_csv(
        tmp_path,
        [
            "Lucknow,Lucknow Sadar,Gomti Nagar,54000,2024,EXTRA_FIELD\n",
            "Lucknow,Lucknow Sadar,Aliganj,55000,2024\n",
        ],
    )
    result = _ingestor(tmp_path).ingest_file(path)
    assert result.accounting.rows_received == 2
    assert result.accounting.rows_accepted == 1
    assert result.accounting.rows_quarantined == 1
    assert result.quarantine[0].reason_code == QuarantineReason.MISSING_REQUIRED_FIELD


# =========================================================================
# 2. HTML path: malformed + invalid rows quarantined
# =========================================================================


def test_html_short_and_invalid_rows_are_quarantined(tmp_path: Path) -> None:
    ingestor = _ingestor(tmp_path)
    outcome = ingestor.parse_html(HTML_TABLE)

    assert isinstance(outcome, ParseOutcome)
    assert outcome.rows_received == 3
    assert len(outcome.rows) == 1
    assert len(outcome.rejections) == 2
    assert outcome.rows_received == len(outcome.rows) + len(outcome.rejections)

    reasons = {rejection.reason_code for rejection in outcome.rejections}
    assert QuarantineReason.MISSING_REQUIRED_FIELD in reasons
    assert QuarantineReason.MISSING_PRICE in reasons

    result = ingestor.ingest_html(HTML_TABLE)
    assert result.accounting.rows_accepted == 1
    assert result.accounting.rows_quarantined == 2
    assert result.quarantine_path is not None and result.quarantine_path.exists()


def test_html_without_recognized_table_fails_loudly(tmp_path: Path) -> None:
    ingestor = _ingestor(tmp_path)
    with pytest.raises(IngestionError):
        ingestor.parse_html("<html><body><p>no tables here</p></body></html>")


# =========================================================================
# 3. Schema validation failures become rejections, not swallowed warnings
# =========================================================================


def test_validate_records_returns_rejections_for_schema_failures() -> None:
    ingestor = CircleRateIngestor()
    bad_row = {
        "state": "UP",
        "district": "Lucknow",
        "zone_tehsil": "Lucknow Sadar",
        "locality": "Gomti Nagar",
        "property_type": "residential",
        "rate_per_sqm": -5.0,  # violates CircleRateRecord(gt=0)
        "effective_year": 2024,
        "source_url": "local://synthetic/circle_rates",
    }
    records, rejections = ingestor.validate_records([bad_row])

    assert records == []
    assert len(rejections) == 1
    assert isinstance(rejections[0], CircleRateRejection)
    assert rejections[0].reason_code == QuarantineReason.MISSING_REQUIRED_FIELD


# =========================================================================
# 4. Source-level guard: the silent-skip code path is gone
# =========================================================================


def test_no_silent_skip_code_path_remains() -> None:
    src = CIRCLE_RATES_SRC.read_text(encoding="utf-8")
    assert "Skipping invalid circle rate row" not in src
    assert "if normalized is not None:\n                    rows.append" not in src


# =========================================================================
# 5. Backwards-compatible helper still works for valid rows
# =========================================================================


def test_parse_records_wrapper_still_returns_valid_records(tmp_path: Path) -> None:
    path = _write_csv(tmp_path, ["Lucknow,Lucknow Sadar,Gomti Nagar,54000,2024\n"])
    ingestor = _ingestor(tmp_path)
    outcome = ingestor.parse_file(str(path))
    records = ingestor.parse_records(outcome.rows)
    assert len(records) == 1
    assert records[0].rate_per_sqm == 54000.0


def test_ingestion_result_need_not_touch_database(tmp_path: Path) -> None:
    """ingest_file performs parse + accounting only; it returns records without upserting."""
    path = _write_csv(tmp_path, ["Lucknow,Lucknow Sadar,Gomti Nagar,54000,2024\n"])
    result = _ingestor(tmp_path).ingest_file(path)
    assert result.rows_upserted == 0
    assert result.accounting.source_snapshot_hash
    assert len(result.accounting.source_snapshot_hash) == 64
