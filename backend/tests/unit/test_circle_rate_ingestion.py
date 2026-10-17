"""Unit tests for circle rate ingestion normalization (no database required)."""

from datetime import datetime, UTC

import pytest
from sqlalchemy import inspect as sa_inspect

from app.database.models.circle_rate import CircleRate
from app.ingestion.circle_rates import (
    CircleRateIngestor,
    _clean_rate,
    _clean_year,
    _looks_like_rate_table,
    _normalize_row,
)
from app.ingestion.schemas import CircleRateRecord


def test_clean_rate_parses_indian_formats() -> None:
    assert _clean_rate("5,400") == 5400.0
    assert _clean_rate("₹5,400") == 5400.0
    assert _clean_rate("54000") == 54000.0
    assert _clean_rate("54,000.50") == 54000.5


def test_clean_rate_rejects_invalid() -> None:
    assert _clean_rate(None) is None
    assert _clean_rate("-100") is None
    assert _clean_rate("0") is None
    assert _clean_rate("not a rate") is None


def test_clean_year_parses_financial_year_labels() -> None:
    assert _clean_year("2023") == 2023
    assert _clean_year("2023-24") == 2023
    assert _clean_year("FY 2024-25") == 2024
    assert _clean_year("Notification Year: 2022") == 2022
    assert _clean_year(None) is None
    assert _clean_year("not a year") is None


def test_looks_like_rate_table() -> None:
    assert _looks_like_rate_table(["district", "tehsil", "locality", "circle rate per sqm"]) is True
    assert _looks_like_rate_table(["name", "address", "phone"]) is False
    assert _looks_like_rate_table([]) is False


def test_normalize_row_maps_aliases() -> None:
    row = {
        "district": "Lucknow",
        "tehsil": "Lucknow Sadar",
        "locality": "Gomti Nagar",
        "circle rate per sqm": "54,000",
        "effective year": "FY 2023-24",
    }
    result = _normalize_row(row, "UP", "Lucknow", "https://igrsup.gov.in/rates")

    assert result is not None
    assert result["state"] == "UP"
    assert result["district"] == "Lucknow"
    assert result["zone_tehsil"] == "Lucknow Sadar"
    assert result["locality"] == "Gomti Nagar"
    assert result["property_type"] == "residential_flat"
    assert result["rate_per_sqm"] == 54000.0
    assert result["effective_year"] == 2023
    assert result["source_url"] == "https://igrsup.gov.in/rates"
    assert isinstance(result["fetched_at"], datetime)


def test_normalize_row_rejects_missing_or_bad_rows() -> None:
    assert (
        _normalize_row({"district": "Lucknow"}, "UP", "Lucknow", "http://example.com") is None
    )
    bad_rate = {
        "district": "Lucknow",
        "tehsil": "Lucknow Sadar",
        "locality": "Gomti Nagar",
        "circle rate per sqm": "free",
        "effective year": "2024",
    }
    assert _normalize_row(bad_rate, "UP", "Lucknow", "http://example.com") is None
    bad_year = {
        "district": "Lucknow",
        "tehsil": "Lucknow Sadar",
        "locality": "Gomti Nagar",
        "circle rate per sqm": "54000",
        "effective year": "unknown",
    }
    assert _normalize_row(bad_year, "UP", "Lucknow", "http://example.com") is None


def test_circle_rate_record_validation() -> None:
    record = CircleRateRecord(
        state="UP",
        district="Lucknow",
        zone_tehsil="Lucknow Sadar",
        locality="Gomti Nagar",
        property_type="residential",
        rate_per_sqm=54000.0,
        effective_year=2024,
        source_url="http://example.com",
        fetched_at=datetime.now(UTC),
    )
    assert record.rate_per_sqm == 54000.0

    with pytest.raises(Exception):
        CircleRateRecord(
            state="UP",
            district="Lucknow",
            zone_tehsil="Lucknow Sadar",
            locality="Gomti Nagar",
            property_type="residential",
            rate_per_sqm=0,
            effective_year=2024,
            source_url="http://example.com",
            fetched_at=datetime.now(UTC),
        )


def test_circle_rate_model_columns() -> None:
    columns = {column.key for column in sa_inspect(CircleRate).columns}
    expected = {
        "id",
        "state",
        "district",
        "zone_tehsil",
        "locality",
        "property_type",
        "rate_per_sqm",
        "effective_year",
        "source_url",
        "fetched_at",
        "created_at",
        "updated_at",
    }
    assert expected.issubset(columns)


def test_ingestor_defaults_use_settings() -> None:
    ingestor = CircleRateIngestor()
    assert ingestor.state == "UP"
    assert ingestor.district == "Lucknow"
    assert ingestor.city == "Lucknow"
