"""Repository layer — WorkflowRun CRUD (class-based, blueprint pattern)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.workflow_run import WorkflowRun

logger = logging.getLogger(__name__)

VN_TZ = timezone(timedelta(hours=7))


class WorkflowRunRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_run_id(self, repository_id: str, github_run_id: int) -> Optional[WorkflowRun]:
        result = await self.session.execute(
            select(WorkflowRun).where(
                WorkflowRun.repository_id == repository_id,
                WorkflowRun.github_run_id == github_run_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_latest(self, repository_id: str) -> Optional[WorkflowRun]:
        result = await self.session.execute(
            select(WorkflowRun)
            .where(WorkflowRun.repository_id == repository_id)
            .order_by(WorkflowRun.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        *,
        repository_id: str,
        github_run_id: int,
        workflow_name: Optional[str] = None,
        branch: Optional[str] = None,
        commit_sha: Optional[str] = None,
        status: Optional[str] = None,
        conclusion: Optional[str] = None,
        run_url: Optional[str] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
    ) -> WorkflowRun:
        run = await self.get_by_run_id(repository_id, github_run_id)
        if run is None:
            run = WorkflowRun(
                repository_id=repository_id,
                github_run_id=github_run_id,
            )
            self.session.add(run)

        if workflow_name is not None:
            run.workflow_name = workflow_name
        if branch is not None:
            run.branch = branch
        if commit_sha is not None:
            run.commit_sha = commit_sha
        if status is not None:
            run.status = status
        if conclusion is not None:
            run.conclusion = conclusion
        if run_url is not None:
            run.run_url = run_url
        if started_at is not None:
            run.started_at = started_at.replace(tzinfo=None) if started_at.tzinfo else started_at
        if completed_at is not None:
            run.completed_at = completed_at.replace(tzinfo=None) if completed_at.tzinfo else completed_at

        await self.session.flush()
        await self.session.refresh(run)
        return run

    async def commit(self) -> None:
        await self.session.commit()
