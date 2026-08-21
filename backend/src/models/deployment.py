"""SQLModel table: Deployment."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlmodel import Field, SQLModel

VN_TZ = timezone(timedelta(hours=7))


def _now_vn() -> datetime:
    return datetime.now(VN_TZ).replace(tzinfo=None)


class Deployment(SQLModel, table=True):
    __tablename__ = "deployments"

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
    github_deployment_id: int = Field(nullable=False)
    environment: Optional[str] = Field(default=None, max_length=100)
    status: Optional[str] = Field(default=None, max_length=50)
    commit_sha: Optional[str] = Field(default=None, max_length=40)
    deploy_url: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=_now_vn)
    updated_at: datetime = Field(default_factory=_now_vn)

    def __repr__(self) -> str:
        return f"<Deployment {self.environment} dep_id={self.github_deployment_id}>"
