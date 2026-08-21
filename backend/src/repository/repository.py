"""Repository layer — Repository entity CRUD (class-based, blueprint pattern)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.repository import Repository

logger = logging.getLogger(__name__)

VN_TZ = timezone(timedelta(hours=7))


class RepositoryRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_full_name(self, full_name: str) -> Optional[Repository]:
        result = await self.session.execute(
            select(Repository).where(Repository.full_name == full_name)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, repo_id: str) -> Optional[Repository]:
        result = await self.session.execute(
            select(Repository).where(Repository.id == repo_id)
        )
        return result.scalar_one_or_none()

    async def get_all(self, active_only: bool = True) -> list[Repository]:
        q = select(Repository)
        if active_only:
            q = q.where(Repository.active.is_(True))
        q = q.order_by(Repository.full_name)
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def create(
        self,
        *,
        owner: str,
        name: str,
        full_name: str,
        default_branch: Optional[str] = None,
        github_id: Optional[int] = None,
    ) -> Repository:
        repo = Repository(
            owner=owner,
            name=name,
            full_name=full_name,
            default_branch=default_branch,
            github_id=github_id,
            active=True,
        )
        self.session.add(repo)
        await self.session.flush()
        await self.session.refresh(repo)
        return repo

    async def set_active(self, repo_id: str, active: bool) -> None:
        now = datetime.now(VN_TZ).replace(tzinfo=None)
        await self.session.execute(
            update(Repository)
            .where(Repository.id == repo_id)
            .values(active=active, updated_at=now)
        )

    async def delete(self, repo: Repository) -> None:
        await self.session.delete(repo)

    async def commit(self) -> None:
        await self.session.commit()
