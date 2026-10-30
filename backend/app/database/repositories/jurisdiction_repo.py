"""Repository for versioned jurisdiction packs.

The playbook requires a ``jurisdiction`` row per state with a config payload and
``config_version``. The Python packs remain the reviewed source of truth for the
pilot; this repository mirrors them into Postgres so regulatory documents and
findings can carry a real state foreign key.
"""

from __future__ import annotations

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.jurisdiction import Jurisdiction
from app.property.jurisdictions import JURISDICTIONS, JurisdictionPack


class JurisdictionRepository:
    """Upsert jurisdiction packs into the canonical database table."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert_pack(self, pack: JurisdictionPack) -> None:
        """Insert or update one pack, keyed by its two-letter state code."""
        insert_stmt = pg_insert(Jurisdiction).values(
            state_code=pack.state_code.upper(),
            name=pack.name,
            status=pack.status,
            config=pack.model_dump(mode="json"),
            config_version=pack.config_version,
        )
        statement = insert_stmt.on_conflict_do_update(
            index_elements=[Jurisdiction.state_code],
            set_={
                "name": insert_stmt.excluded.name,
                "status": insert_stmt.excluded.status,
                "config": insert_stmt.excluded.config,
                "config_version": insert_stmt.excluded.config_version,
            },
        )
        await self.session.execute(statement)

    async def upsert_all(
        self,
        packs: dict[str, JurisdictionPack] | None = None,
    ) -> int:
        """Upsert every configured pack and return the number written."""
        selected = packs or JURISDICTIONS
        for pack in selected.values():
            await self.upsert_pack(pack)
        await self.session.flush()
        return len(selected)
