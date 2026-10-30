"""Repository for source approval and freshness state.

Playbook sections 19.3 and SOP-4 require an auditable per-source record of the
last attempt, last successful sync, refresh interval, and last error. This
repository centralizes those writes so collectors do not invent inconsistent
timestamps. It does not approve a source; approval remains an explicit owner
action.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.source import DataSource

MAX_ERROR_LENGTH = 500


class SourceFreshnessRepository:
    """Read and update source freshness fields."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record_attempt(self, source_id: UUID) -> None:
        """Record that a fetch was attempted, without claiming success."""
        now = datetime.now(UTC)
        await self.session.execute(
            update(DataSource)
            .where(DataSource.source_id == source_id)
            .values(last_checked_at=now, last_attempt_at=now)
        )

    async def record_success(self, source_id: UUID) -> None:
        """Record a successful sync in both legacy and playbook fields."""
        now = datetime.now(UTC)
        await self.session.execute(
            update(DataSource)
            .where(DataSource.source_id == source_id)
            .values(
                last_checked_at=now,
                last_attempt_at=now,
                last_success_at=now,
                last_successful_sync_at=now,
                last_error=None,
            )
        )

    async def record_failure(self, source_id: UUID, error: str) -> None:
        """Record a failed attempt with a bounded, non-secret error summary."""
        now = datetime.now(UTC)
        await self.session.execute(
            update(DataSource)
            .where(DataSource.source_id == source_id)
            .values(
                last_checked_at=now,
                last_attempt_at=now,
                last_error=error[:MAX_ERROR_LENGTH],
            )
        )

    async def list_stale(
        self,
        *,
        as_of: datetime | None = None,
        default_interval_days: int = 90,
    ) -> list[DataSource]:
        """Return approved sources whose last success exceeds their interval.

        A source with no recorded success is stale. A source without a
        ``refresh_interval_days`` uses ``default_interval_days``.
        """
        if default_interval_days < 1:
            raise ValueError("default_interval_days must be at least 1")
        reference = as_of or datetime.now(UTC)
        if reference.tzinfo is None:
            reference = reference.replace(tzinfo=UTC)

        interval = func.coalesce(
            DataSource.refresh_interval_days, default_interval_days
        )
        last_success = func.coalesce(
            DataSource.last_success_at, DataSource.last_successful_sync_at
        )
        cutoff = reference - func.make_interval(0, 0, 0, interval)
        statement = (
            select(DataSource)
            .where(
                DataSource.approval_status == "approved",
                or_(last_success.is_(None), last_success < cutoff),
            )
            .order_by(DataSource.source_name)
        )
        return list((await self.session.execute(statement)).scalars().all())

    async def freshness_summary(self, source_id: UUID) -> dict[str, object] | None:
        """Return a compact freshness record for a rule input or audit log."""
        source = await self.session.get(DataSource, source_id)
        if source is None:
            return None
        last_success = source.last_success_at or source.last_successful_sync_at
        interval_days = source.refresh_interval_days
        stale: bool | None = None
        if last_success is not None and interval_days is not None:
            stale = (datetime.now(UTC) - last_success) > timedelta(days=interval_days)
        return {
            "source_id": str(source.source_id),
            "source_name": source.source_name,
            "approval_status": source.approval_status,
            "last_attempt_at": source.last_attempt_at,
            "last_success_at": last_success,
            "refresh_interval_days": interval_days,
            "last_error": source.last_error,
            "stale": stale,
        }
