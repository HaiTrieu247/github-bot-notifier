"""SQLModel table: Repository."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlmodel import Field, SQLModel

VN_TZ = timezone(timedelta(hours=7))


def _now_vn() -> datetime:
    """Current time GMT+7, naive datetime (compatible with PostgreSQL TIMESTAMP WITHOUT TZ)."""
    return datetime.now(VN_TZ).replace(tzinfo=None)


class Repository(SQLModel, table=True):
    __tablename__ = "repositories"

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True,
        index=True,
    )
    owner: str = Field(max_length=255, nullable=False)
    name: str = Field(max_length=255, nullable=False)
    full_name: str = Field(max_length=511, nullable=False, unique=True, index=True)
    default_branch: Optional[str] = Field(default=None, max_length=255)
    github_id: Optional[int] = Field(default=None)
    active: bool = Field(default=True, nullable=False)
    created_at: datetime = Field(default_factory=_now_vn)
    updated_at: datetime = Field(default_factory=_now_vn)

    def __repr__(self) -> str:
        return f"<Repository {self.full_name}>"
