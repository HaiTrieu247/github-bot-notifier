"""Service: Repository management (class-based, blueprint DI pattern)."""

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.repository import Repository
from src.repository.repository import RepositoryRepo
from src.github.client import GitHubAPIError, get_github_client

logger = logging.getLogger(__name__)


class RepositoryNotFoundError(Exception):
    pass


class RepositoryAlreadyExistsError(Exception):
    pass


class RepositoryService:
    def __init__(self, session: AsyncSession, repo_repo: RepositoryRepo) -> None:
        self.session = session
        self.repo_repo = repo_repo

    async def list_repositories(self) -> list[Repository]:
        return await self.repo_repo.get_all(active_only=True)

    async def get_repository(self, repo_id: str) -> Repository:
        repo = await self.repo_repo.get_by_id(repo_id)
        if not repo:
            raise RepositoryNotFoundError(f"Repository '{repo_id}' not found")
        return repo

    async def add_repository(self, owner: str, name: str) -> Repository:
        full_name = f"{owner}/{name}"
        existing = await self.repo_repo.get_by_full_name(full_name)
        if existing:
            if not existing.active:
                await self.repo_repo.set_active(existing.id, True)
                await self.repo_repo.commit()
                refreshed = await self.repo_repo.get_by_id(existing.id)
                return refreshed  # type: ignore[return-value]
            return existing

        # Validate against GitHub API
        github = await get_github_client()
        try:
            repo_data = await github.get_repo(full_name)
        except GitHubAPIError as exc:
            raise ValueError(f"GitHub API error for '{full_name}': {exc}") from exc

        repo = await self.repo_repo.create(
            owner=owner,
            name=name,
            full_name=full_name,
            default_branch=repo_data.get("default_branch"),
            github_id=repo_data.get("id"),
        )
        await self.repo_repo.commit()
        logger.info("Repository %s added", full_name)
        return repo

    async def remove_repository(self, repo_id: str) -> None:
        repo = await self.repo_repo.get_by_id(repo_id)
        if not repo:
            raise RepositoryNotFoundError(f"Repository '{repo_id}' not found")
        await self.repo_repo.delete(repo)
        await self.repo_repo.commit()
        logger.info("Repository %s removed", repo_id)
