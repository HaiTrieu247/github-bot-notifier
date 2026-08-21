"""SQLModel table: WorkflowRun."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlmodel import Field, SQLModel

VN_TZ = timezone(timedelta(hours=7))


def _now_vn() -> datetime:
    return datetime.now(VN_TZ).replace(tzinfo=None)


class WorkflowRun(SQLModel, table=True):
    __tablename__ = "workflow_runs"

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
    github_run_id: int = Field(nullable=False)
    workflow_name: Optional[str] = Field(default=None, max_length=255)
    branch: Optional[str] = Field(default=None, max_length=255)
    commit_sha: Optional[str] = Field(default=None, max_length=40)
    status: Optional[str] = Field(default=None, max_length=50)
    conclusion: Optional[str] = Field(default=None, max_length=50)
    run_url: Optional[str] = Field(default=None)
    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=_now_vn)

    def __repr__(self) -> str:
        return f"<WorkflowRun {self.workflow_name} run_id={self.github_run_id}>"
