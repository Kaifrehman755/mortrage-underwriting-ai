"""F-08 regression tests: SSRF and arbitrary-file-read hardening.

Verifies (Phase 2, Priority 4 — F-08):
1. Outbound ingestion URLs must be HTTPS and must target an allowlisted host.
2. IP literals in internal/reserved ranges (e.g. the cloud metadata address) are blocked,
   even if they appear on the allowlist.
3. An empty allowlist refuses to fetch (fail closed).
4. Redirects are not followed (no pivot to an unvalidated internal host).
5. Local file ingestion is confined to the approved intake directory (no path traversal)
   and only accepted file types are read.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from app.ingestion import circle_rates as circle_rates_module
from app.ingestion.circle_rates import (
    CircleRateIngestor,
    IngestionError,
    ParseOutcome,
    resolve_intake_path,
    validate_ingestion_url,
)

CSV_HEADER = "district,tehsil,locality,circle rate per sqm,effective year\n"
CSV_ROW = "Lucknow,Lucknow Sadar,Gomti Nagar,54000,2024\n"

METADATA_URL = "https://169.254.169.254/latest/meta-data/"


# =========================================================================
# 1. URL policy
# =========================================================================

def test_rejects_non_https_scheme() -> None:
    with pytest.raises(IngestionError):
        validate_ingestion_url("http://igrsup.gov.in/rates", ("igrsup.gov.in",))


def test_rejects_empty_url() -> None:
    with pytest.raises(IngestionError):
        validate_ingestion_url("", ("igrsup.gov.in",))


def test_rejects_host_not_on_allowlist() -> None:
    with pytest.raises(IngestionError):
        validate_ingestion_url("https://evil.example.com/rates", ("igrsup.gov.in",))


def test_empty_allowlist_refuses_to_fetch() -> None:
    with pytest.raises(IngestionError):
        validate_ingestion_url("https://igrsup.gov.in/rates", ())


def test_allows_allowlisted_host_and_subdomain() -> None:
    url = "https://igrsup.gov.in/rates"
    assert validate_ingestion_url(url, ("igrsup.gov.in",)) == url
    assert (
        validate_ingestion_url("https://www.igrsup.gov.in/rates", ("igrsup.gov.in",))
        == "https://www.igrsup.gov.in/rates"
    )


@pytest.mark.parametrize(
    "url",
    [
        "https://169.254.169.254/latest/meta-data/",
        "https://127.0.0.1/",
        "https://10.0.0.5/",
        "https://192.168.1.10/",
        "https://[::1]/",
    ],
)
def test_rejects_internal_ip_literals_even_if_allowlisted(url: str) -> None:
    from urllib.parse import urlparse

    host = urlparse(url).hostname or ""
    with pytest.raises(IngestionError):
        validate_ingestion_url(url, (host,))


# =========================================================================
# 2. fetch_raw integration (no real network access)
# =========================================================================

class _FakeResponse:
    def __init__(self, status_code: int, headers=None, text: str = "") -> None:
        self.status_code = status_code
        self.headers = headers or {}
        self.text = text

    @property
    def is_redirect(self) -> bool:
        return self.status_code in (301, 302, 303, 307, 308)

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise AssertionError(f"unexpected HTTP {self.status_code}")


class _FakeAsyncClient:
    """Minimal httpx.AsyncClient stand-in used to avoid real network access."""

    last_kwargs: dict = {}
    next_response: _FakeResponse = _FakeResponse(200, text="ok")

    def __init__(self, *args, **kwargs) -> None:
        type(self).last_kwargs = kwargs

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc) -> bool:
        return False

    async def get(self, url: str):  # noqa: ANN201 - test double
        return type(self).next_response


def _ingestor(source_url: str, allowed_hosts) -> CircleRateIngestor:
    return CircleRateIngestor(source_url=source_url, allowed_hosts=allowed_hosts)


def test_fetch_raw_refuses_metadata_url() -> None:
    ingestor = _ingestor(METADATA_URL, [""])
    with pytest.raises(IngestionError):
        asyncio.run(ingestor.fetch_raw())


def test_fetch_raw_does_not_follow_redirects(monkeypatch: pytest.MonkeyPatch) -> None:
    _FakeAsyncClient.next_response = _FakeResponse(302, {"location": METADATA_URL})
    monkeypatch.setattr(circle_rates_module.httpx, "AsyncClient", _FakeAsyncClient)

    ingestor = _ingestor("https://igrsup.gov.in/rates", ["igrsup.gov.in"])
    with pytest.raises(IngestionError):
        asyncio.run(ingestor.fetch_raw())
    assert _FakeAsyncClient.last_kwargs.get("follow_redirects") is False


def test_fetch_raw_returns_body_for_allowlisted_host(monkeypatch: pytest.MonkeyPatch) -> None:
    _FakeAsyncClient.next_response = _FakeResponse(200, text="<html>rates</html>")
    monkeypatch.setattr(circle_rates_module.httpx, "AsyncClient", _FakeAsyncClient)

    ingestor = _ingestor("https://igrsup.gov.in/rates", ["igrsup.gov.in"])
    assert asyncio.run(ingestor.fetch_raw()) == "<html>rates</html>"


# =========================================================================
# 3. Intake-directory confinement
# =========================================================================

def test_resolve_intake_path_rejects_traversal(tmp_path: Path) -> None:
    approved = tmp_path / "approved"
    approved.mkdir()
    with pytest.raises(IngestionError):
        resolve_intake_path(approved / ".." / ".." / "etc" / "passwd", approved)


def test_resolve_intake_path_rejects_unsupported_suffix(tmp_path: Path) -> None:
    approved = tmp_path / "approved"
    approved.mkdir()
    target = approved / "rates.txt"
    target.write_text("nope", encoding="utf-8")
    with pytest.raises(IngestionError):
        resolve_intake_path(target, approved)


def test_parse_file_rejects_file_outside_intake_dir(tmp_path: Path) -> None:
    approved = tmp_path / "approved"
    approved.mkdir()
    outside = tmp_path / "outside.csv"
    outside.write_text(CSV_HEADER + CSV_ROW, encoding="utf-8")

    ingestor = CircleRateIngestor(intake_dir=approved, quarantine_dir=tmp_path)
    with pytest.raises(IngestionError):
        ingestor.parse_file(str(outside))


def test_ingest_file_rejects_file_outside_intake_dir(tmp_path: Path) -> None:
    approved = tmp_path / "approved"
    approved.mkdir()
    outside = tmp_path / "outside.csv"
    outside.write_text(CSV_HEADER + CSV_ROW, encoding="utf-8")

    ingestor = CircleRateIngestor(intake_dir=approved, quarantine_dir=tmp_path)
    with pytest.raises(IngestionError):
        ingestor.ingest_file(outside)


def test_parse_file_reads_file_inside_intake_dir(tmp_path: Path) -> None:
    approved = tmp_path / "approved"
    approved.mkdir()
    inside = approved / "circle_rates.csv"
    inside.write_text(CSV_HEADER + CSV_ROW, encoding="utf-8")

    ingestor = CircleRateIngestor(intake_dir=approved, quarantine_dir=tmp_path)
    outcome = ingestor.parse_file(str(inside))
    assert isinstance(outcome, ParseOutcome)
    assert len(outcome.rows) == 1


def test_empty_allowlist_is_the_secure_default() -> None:
    ingestor = CircleRateIngestor(source_url="https://igrsup.gov.in/rates", allowed_hosts=())
    assert ingestor.allowed_hosts == ()
    with pytest.raises(IngestionError):
        asyncio.run(ingestor.fetch_raw())


def test_settings_parses_empty_allowlist_to_empty_list() -> None:
    from app.core.config import Settings

    settings = Settings(APP_ENV="test", _env_file=None, CIRCLE_RATE_ALLOWED_HOSTS="")
    assert settings.CIRCLE_RATE_ALLOWED_HOSTS == []
