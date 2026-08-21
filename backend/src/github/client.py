"""GitHub REST API client using httpx."""

from __future__ import annotations

import logging
from typing import Any, Optional

import httpx

from src.config import Config

logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"


class GitHubAPIError(Exception):
    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        super().__init__(f"GitHub API error {status_code}: {message}")


class GitHubRateLimitError(GitHubAPIError):
    pass


class GitHubClient:
    def __init__(self, token: Optional[str] = None) -> None:
        self._token = token or Config.github_token
        self._client = httpx.AsyncClient(
            base_url=GITHUB_API_BASE,
            headers=self._default_headers(),
            timeout=15.0,
        )

    def _default_headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    async def _get(self, path: str, **params: Any) -> dict[str, Any] | list[Any]:
        response = await self._client.get(path, params=params)
        self._handle_rate_limit(response)
        response.raise_for_status()
        return response.json()

    def _handle_rate_limit(self, response: httpx.Response) -> None:
        if response.status_code == 403:
            remaining = response.headers.get("X-RateLimit-Remaining", "?")
            reset = response.headers.get("X-RateLimit-Reset", "?")
            logger.warning(
                "GitHub API rate limit hit. Remaining: %s, Reset: %s", remaining, reset
            )
            raise GitHubRateLimitError(403, "Rate limit exceeded")

    async def get_repo(self, full_name: str) -> dict[str, Any]:
        data = await self._get(f"/repos/{full_name}")
        assert isinstance(data, dict)
        return data

    async def get_commits(self, full_name: str, branch: str = "main", per_page: int = 10) -> list[dict[str, Any]]:
        data = await self._get(f"/repos/{full_name}/commits", sha=branch, per_page=per_page)
        assert isinstance(data, list)
        return data

    async def get_workflow_runs(
        self, full_name: str, branch: Optional[str] = None, per_page: int = 10
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"per_page": per_page}
        if branch:
            params["branch"] = branch
        data = await self._get(f"/repos/{full_name}/actions/runs", **params)
        assert isinstance(data, dict)
        return data.get("workflow_runs", [])  # type: ignore[return-value]

    async def get_pull_requests(
        self, full_name: str, state: str = "open", per_page: int = 10
    ) -> list[dict[str, Any]]:
        data = await self._get(
            f"/repos/{full_name}/pulls",
            state=state,
            per_page=per_page,
            sort="updated",
            direction="desc",
        )
        assert isinstance(data, list)
        return data

    async def get_deployments(
        self, full_name: str, environment: Optional[str] = None, per_page: int = 10
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"per_page": per_page}
        if environment:
            params["environment"] = environment
        data = await self._get(f"/repos/{full_name}/deployments", **params)
        assert isinstance(data, list)
        return data

    async def get_deployment_statuses(
        self, full_name: str, deployment_id: int
    ) -> list[dict[str, Any]]:
        data = await self._get(f"/repos/{full_name}/deployments/{deployment_id}/statuses")
        assert isinstance(data, list)
        return data

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "GitHubClient":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.aclose()


_github_client: Optional[GitHubClient] = None


def get_github_client() -> GitHubClient:
    global _github_client
    if _github_client is None:
        _github_client = GitHubClient()
    return _github_client
