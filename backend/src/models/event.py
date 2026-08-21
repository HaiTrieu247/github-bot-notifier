"""SQLModel table: Event."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

VN_TZ = timezone(timedelta(hours=7))


def _now_vn() -> datetime:
    return datetime.now(VN_TZ).replace(tzinfo=None)


class Event(SQLModel, table=True):
    __tablename__ = "events"

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True,
        index=True,
    )
    repository_id: str = Field(
        foreign_key="repositories.id",
        nullable=False,
        index=True,
    )
    event_type: str = Field(max_length=100, nullable=False)
    github_event_id: str = Field(max_length=255, nullable=False, unique=True, index=True)
    # JSONB for PostgreSQL — stored as JSON column
    payload: Optional[Any] = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
    )
    created_at: datetime = Field(default_factory=_now_vn, index=True)
    processed_at: Optional[datetime] = Field(default=None)

    def __repr__(self) -> str:
        return f"<Event {self.event_type} {self.github_event_id}>"
