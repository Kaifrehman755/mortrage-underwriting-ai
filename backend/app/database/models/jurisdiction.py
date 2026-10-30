"""SQLAlchemy ORM model for jurisdiction packs.

Playbook section 15.3 requires one ``jurisdiction`` row per state with a
versioned configuration payload. A blank or unverified pack remains ``planned``
and is never treated as a live jurisdiction.
"""

from typing import Any

from sqlalchemy import CheckConstraint, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class Jurisdiction(Base, TimestampMixin):
    """A state/union-territory configuration pack."""

    __tablename__ = "jurisdiction"

    state_code: Mapped[str] = mapped_column(String(2), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="planned", server_default="planned", index=True
    )
    config: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="'{}'::jsonb"
    )
    config_version: Mapped[str] = mapped_column(String(50), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "status IN ('planned','pilot','live','paused')",
            name="ck_jurisdiction_status",
        ),
    )
