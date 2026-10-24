"""Integration tests against a real PostgreSQL/PostGIS instance (GEMINI.md §15.7).

These tests are skipped automatically when no database is reachable, so the unit
suite still runs on machines without Docker. Start the database with
``docker compose up -d postgres`` and apply migrations with
``alembic upgrade head`` before running them.

Every test runs inside an outer transaction that is rolled back, so the database
is never mutated permanently.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import date

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.database.models.source import DataSource
from app.database.repositories.property_repo import PropertyRepository
from app.database.repositories.reference_rate_repo import ReferenceRateRepository
from app.schemas.property import PropertyRecordCreate
from app.schemas.transaction import ReferenceRateCreate

pytestmark = pytest.mark.integration

EXPECTED_TABLES = {
    "circle_rates",
    "data_sources",
    "ingestion_runs",
    "property_listings",
    "property_records",
    "property_transactions",
    "quarantine_records",
    "reference_rates",
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
            license_scope="Test fixtures only; never production evidence.",
            approval_status="approved",
        )
    )
    await session.flush()
    return source_id


async def test_schema_tables_and_postgis_extension(db_session: AsyncSession) -> None:
    """The migrated schema exposes every expected table and the PostGIS extension."""
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
                    license_scope="Test fixtures only.",
                    approval_status="approved",
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
