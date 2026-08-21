"""Repository layer — Deployment CRUD (class-based, blueprint pattern)."""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.deployment import Deployment

logger = logging.getLogger(__name__)


class DeploymentRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_dep_id(
        self, repository_id: str, github_deployment_id: int
    ) -> Optional[Deployment]:
        result = await self.session.execute(
            select(Deployment).where(
                Deployment.repository_id == repository_id,
                Deployment.github_deployment_id == github_deployment_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_latest(self, repository_id: str) -> Optional[Deployment]:
        result = await self.session.execute(
            select(Deployment)
            .where(Deployment.repository_id == repository_id)
            .order_by(Deployment.updated_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        *,
        repository_id: str,
        github_deployment_id: int,
        environment: Optional[str] = None,
        status: Optional[str] = None,
        commit_sha: Optional[str] = None,
        deploy_url: Optional[str] = None,
    ) -> Deployment:
        from datetime import datetime, timezone, timedelta

        dep = await self.get_by_dep_id(repository_id, github_deployment_id)
        if dep is None:
            dep = Deployment(
                repository_id=repository_id,
                github_deployment_id=github_deployment_id,
            )
            self.session.add(dep)

        if environment is not None:
            dep.environment = environment
        if status is not None:
            dep.status = status
        if commit_sha is not None:
            dep.commit_sha = commit_sha
        if deploy_url is not None:
            dep.deploy_url = deploy_url

        VN_TZ = timezone(timedelta(hours=7))
        dep.updated_at = datetime.now(VN_TZ).replace(tzinfo=None)

        await self.session.flush()
        await self.session.refresh(dep)
        return dep

    async def commit(self) -> None:
        await self.session.commit()
