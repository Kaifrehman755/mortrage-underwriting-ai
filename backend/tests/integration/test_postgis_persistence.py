"""Integration tests against a real PostgreSQL/PostGIS instance (GEMINI.md §15.7).

These tests are skipped automatically when no database is reachable, so the unit
suite still runs on machines without Docker. Start the database with
``docker compose up -d postgres`` and apply migrations with
``alembic upgrade head`` before running them.

Every test runs inside an outer transaction that is rolled back, so the database
is never mutated permanently.
"""

from __future__ import annotations

import hashlib
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.database.models.jurisdiction import Jurisdiction
from app.database.models.source import DataSource
from app.database.repositories.jurisdiction_repo import JurisdictionRepository
from app.database.repositories.property_repo import PropertyRepository
from app.database.repositories.reference_rate_repo import ReferenceRateRepository
from app.database.repositories.source_repo import SourceFreshnessRepository
from app.property.jurisdictions import JURISDICTIONS
from app.rag.postgres_store import PostgresVectorStore
from app.rag.schemas import RegChunk, RegDocument
from app.schemas.property import PropertyRecordCreate
from app.schemas.transaction import ReferenceRateCreate

pytestmark = pytest.mark.integration

EXPECTED_TABLES = {
    "circle_rates",
    "compliance_finding",
    "data_sources",
    "ingestion_runs",
    "jurisdiction",
    "market_indicator",
    "property_listings",
    "property_records",
    "property_transactions",
    "quarantine_records",
    "raw_record",
    "reference_rates",
    "reg_chunk",
    "reg_document",
    "valuation_comparables",
    "valuation_runs",
}


def _database_url() -> str:
    return str(get_settings().DATABASE_URL)


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a session bound to an outer transaction that is always rolled back."""
    engine = create_async_engine(_database_url(), poolclass=NullPool)
    try:
        try:
            async with engine.connect() as probe:
                await probe.execute(text("SELECT 1"))
        except Exception as exc:  # noqa: BLE001 - skip, never fail, without a database
            pytest.skip(f"PostgreSQL/PostGIS unavailable: {type(exc).__name__}")

        async with engine.connect() as connection:
            transaction = await connection.begin()
            session = AsyncSession(bind=connection, expire_on_commit=False)
            try:
                yield session
            finally:
                await session.close()
                await transaction.rollback()
    finally:
        await engine.dispose()


def _synthetic_approval_fields() -> dict[str, object]:
    """A complete, explicitly test-only approval record for synthetic rows."""
    license_scope = "Test fixtures only; never production evidence."
    return {
        "license_scope": license_scope,
        "approval_status": "approved",
        "access_mode": "official_download",
        "approved_by": "integration-test-fixture",
        "approved_at": datetime.now(UTC),
        "terms_snapshot_sha256": hashlib.sha256(license_scope.encode("utf-8")).hexdigest(),
        "review_due": date.today() + timedelta(days=30),
        "decision_note": "Synthetic integration fixture; not a regulatory source.",
    }


async def _create_source(session: AsyncSession, state_code: str = "UP") -> uuid.UUID:
    """Insert an approved synthetic data source and return its id."""
    source_id = uuid.uuid4()
    session.add(
        DataSource(
            source_id=source_id,
            source_name=f"Synthetic integration fixture {source_id}",
            state_code=state_code,
            source_type="synthetic_test",
            official_url="local://synthetic/integration",
            access_method="manual_authorized_import",
            **_synthetic_approval_fields(),
        )
    )
    await session.flush()
    return source_id


async def test_schema_tables_and_postgis_extension(db_session: AsyncSession) -> None:
    """The migrated schema exposes every expected table and both required extensions."""
    tables = set(
        (
            await db_session.execute(
                text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
            )
        )
        .scalars()
        .all()
    )
    assert EXPECTED_TABLES <= tables, f"missing tables: {sorted(EXPECTED_TABLES - tables)}"

    extensions = set(
        (await db_session.execute(text("SELECT extname FROM pg_extension"))).scalars().all()
    )
    assert "postgis" in extensions
    assert "vector" in extensions


async def test_property_persists_postgis_point_and_distance(
    db_session: AsyncSession,
) -> None:
    """A property keeps its WGS-84 point and PostGIS computes a sane metric distance."""
    source_id = await _create_source(db_session)
    repository = PropertyRepository(db_session)

    latitude, longitude = 26.8500, 80.9500  # Lucknow
    record = PropertyRecordCreate(
        source_id=source_id,
        source_record_id="integration-property-1",
        state_code="UP",
        district="Lucknow",
        city="Lucknow",
        locality="Gomti Nagar",
        property_type="apartment",
        area_value_raw=1200.0,
        area_unit_raw="sqft",
        area_sqft=1200.0,
        area_type="carpet",
        latitude=latitude,
        longitude=longitude,
        source_url="local://synthetic/integration/property-1",
        source_record_hash="a" * 32,
    )
    entity = await repository.create(record)
    await db_session.flush()

    fetched = await repository.get_by_id(entity.property_id)
    assert fetched is not None
    assert fetched.latitude == pytest.approx(latitude)
    assert fetched.longitude == pytest.approx(longitude)

    # 0.001 degrees of latitude is ~111 m everywhere; PostGIS must agree in metres.
    distance_m = (
        await db_session.execute(
            text(
                """
                SELECT ST_Distance(
                    location::geography,
                    ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography
                )
                FROM property_records
                WHERE property_id = :property_id
                """
            ),
            {
                "lon": longitude,
                "lat": latitude + 0.001,
                "property_id": str(entity.property_id),
            },
        )
    ).scalar_one()
    assert 105.0 <= float(distance_m) <= 118.0


async def test_reference_rate_upsert_is_idempotent(db_session: AsyncSession) -> None:
    """Re-upserting the same natural key updates in place instead of duplicating."""
    source_id = await _create_source(db_session)
    repository = ReferenceRateRepository(db_session)

    def build(rate: float) -> ReferenceRateCreate:
        return ReferenceRateCreate(
            source_id=source_id,
            state_code="UP",
            district="Lucknow",
            locality="Gomti Nagar",
            property_category="residential_flat",
            rate_raw=rate,
            rate_unit_raw="per_sqft",
            rate_inr_per_sqft=rate,
            effective_from=date(2024, 4, 1),
            source_url="local://synthetic/integration/reference-rate",
            source_record_hash="b" * 32,
        )

    await repository.create_or_update(build(5400.0))
    await db_session.flush()
    await repository.create_or_update(build(5600.0))
    await db_session.flush()

    count = (
        await db_session.execute(
            text(
                """
                SELECT count(*) FROM reference_rates
                WHERE state_code = 'UP' AND locality = 'Gomti Nagar'
                  AND property_category = 'residential_flat'
                  AND effective_from = DATE '2024-04-01'
                """
            )
        )
    ).scalar_one()
    assert count == 1

    benchmark = await repository.lookup_benchmark("UP", "Lucknow", "Gomti Nagar")
    assert benchmark is not None
    assert float(benchmark.rate_inr_per_sqft) == pytest.approx(5600.0)


async def test_jurisdiction_packs_upsert_without_duplicates(
    db_session: AsyncSession,
) -> None:
    """The four reviewed packs can be mirrored into the jurisdiction table."""
    repository = JurisdictionRepository(db_session)
    assert await repository.upsert_all() == len(JURISDICTIONS)
    assert await repository.upsert_all() == len(JURISDICTIONS)

    up = await db_session.get(Jurisdiction, "UP")
    assert up is not None
    assert up.status == JURISDICTIONS["UP"].status
    assert up.config_version == JURISDICTIONS["UP"].config_version
    assert up.config["state_code"] == "UP"


async def test_source_freshness_records_attempt_success_and_staleness(
    db_session: AsyncSession,
) -> None:
    """Freshness writes are bounded, auditable, and visible to stale-source queries."""
    source_id = await _create_source(db_session)
    repository = SourceFreshnessRepository(db_session)
    source = await db_session.get(DataSource, source_id)
    assert source is not None

    await repository.record_attempt(source_id)
    await db_session.refresh(source)
    assert source.last_attempt_at is not None
    assert source.last_success_at is None
    assert source.last_error is None

    await repository.record_failure(source_id, "x" * 900)
    await db_session.refresh(source)
    assert source.last_error == "x" * 500

    await repository.record_success(source_id)
    await db_session.refresh(source)
    assert source.last_error is None
    assert source.last_success_at is not None
    assert source.last_successful_sync_at is not None

    source.refresh_interval_days = 30
    source.last_success_at = datetime.now(UTC) - timedelta(days=31)
    source.last_successful_sync_at = source.last_success_at
    await db_session.flush()

    summary = await repository.freshness_summary(source_id)
    assert summary is not None
    assert summary["stale"] is True

    stale = await repository.list_stale(default_interval_days=90)
    assert any(item.source_id == source_id for item in stale)


async def test_pgvector_evidence_store_is_idempotent_and_state_isolated(
    db_session: AsyncSession,
) -> None:
    """The Postgres store persists approved evidence and never returns another state."""
    db_session.add(
        Jurisdiction(
            state_code="UP",
            name="Uttar Pradesh",
            status="pilot",
            config={"test": True},
            config_version="test-fixture",
        )
    )
    await db_session.flush()

    raw_text = "Section 3. Key Fact Statement disclosure requirements for borrowers."
    doc = RegDocument(
        source_name="Integration Test Regulatory Document",
        authority="Integration Test Authority",
        version_or_date="2026-01-01",
        url="local://synthetic/regulatory/test",
        sha256=hashlib.sha256(raw_text.encode("utf-8")).hexdigest(),
        approved=True,
        approved_by="integration-test-fixture",
        approved_at=datetime.now(UTC).isoformat(),
        review_due="2027-01-01",
        terms_snapshot_sha256=hashlib.sha256(b"test terms").hexdigest(),
        scope="state",
        state_code="UP",
        effective_from="2020-01-01",
        effective_to="2099-12-31",
    )
    embedding = [0.0] * 384
    embedding[0] = 1.0
    chunks = [
        RegChunk(
            doc_id=doc.doc_id,
            source_name=doc.source_name,
            authority=doc.authority,
            section_ref="Section 3",
            text=raw_text,
            embedding=embedding,
            scope="state",
            state_code="UP",
            approved=True,
            effective_from=doc.effective_from,
            effective_to=doc.effective_to,
            version_or_date=doc.version_or_date,
            index_version="integration_test_v1",
        )
    ]
    store = PostgresVectorStore(db_session)
    assert await store.is_doc_ingested(doc.sha256) is False
    assert await store.ingest_document(doc, chunks) == 1
    assert await store.is_doc_ingested(doc.sha256) is True
    # Re-running the same document must update, not duplicate.
    assert await store.ingest_document(doc, chunks) == 1

    results = await store.hybrid_search(
        query_text="Key Fact Statement disclosure requirements",
        query_vector=embedding,
        state_code="UP",
        loan_date="2026-10-25",
        top_k=5,
        index_version="integration_test_v1",
    )
    assert results
    assert results[0][0].section_ref == "Section 3"

    # A Maharashtra case must not receive the UP document, even by exact text.
    state_results = await store.hybrid_search(
        query_text="Key Fact Statement disclosure requirements",
        query_vector=embedding,
        state_code="MH",
        loan_date="2026-10-25",
        top_k=5,
        index_version="integration_test_v1",
    )
    assert all(chunk.state_code != "UP" for chunk, _score in state_results)


async def test_transaction_rollback_discards_writes() -> None:
    """An aborted transaction leaves no rows behind."""
    engine = create_async_engine(_database_url(), poolclass=NullPool)
    marker = f"rollback-{uuid.uuid4()}"
    try:
        try:
            async with engine.connect() as probe:
                await probe.execute(text("SELECT 1"))
        except Exception as exc:  # noqa: BLE001
            pytest.skip(f"PostgreSQL/PostGIS unavailable: {type(exc).__name__}")

        async with engine.connect() as connection:
            transaction = await connection.begin()
            session = AsyncSession(bind=connection, expire_on_commit=False)
            session.add(
                DataSource(
                    source_id=uuid.uuid4(),
                    source_name=marker,
                    state_code="UP",
                    source_type="synthetic_test",
                    official_url="local://synthetic/integration",
                    access_method="manual_authorized_import",
                    **_synthetic_approval_fields(),
                )
            )
            await session.flush()
            await transaction.rollback()
            await session.close()

        async with engine.connect() as connection:
            remaining = (
                await connection.execute(
                    text("SELECT count(*) FROM data_sources WHERE source_name = :name"),
                    {"name": marker},
                )
            ).scalar_one()
        assert remaining == 0
    finally:
        await engine.dispose()
