"""Route: /api/v1/repositories — CRUD for monitored GitHub repositories."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.main import get_session
from src.repository.repository import RepositoryRepo
from src.schemas.repository import RepositoryCreate, RepositoryListResponse, RepositoryRead
from src.services.repository import (
    RepositoryNotFoundError,
    RepositoryService,
)
from src.routes.auth import get_current_admin

router = APIRouter(
    prefix="/api/v1/repositories",
    tags=["Repositories"],
    dependencies=[Depends(get_current_admin)]
)


# ── Dependency: build service via DI ─────────────────────────────────────────

async def get_service(session: AsyncSession = Depends(get_session)) -> RepositoryService:
    repo_repo = RepositoryRepo(session)
    return RepositoryService(session=session, repo_repo=repo_repo)


# ── Helper ────────────────────────────────────────────────────────────────────

def _to_read(repo) -> RepositoryRead:
    return RepositoryRead(
        id=repo.id,
        owner=repo.owner,
        name=repo.name,
        full_name=repo.full_name,
        default_branch=repo.default_branch,
        github_id=repo.github_id,
        active=repo.active,
        created_at=repo.created_at.isoformat(),
        updated_at=repo.updated_at.isoformat(),
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("", response_model=RepositoryListResponse)
async def list_repositories(
    service: RepositoryService = Depends(get_service),
) -> RepositoryListResponse:
    repos = await service.list_repositories()
    items = [_to_read(r) for r in repos]
    return RepositoryListResponse(items=items, total=len(items))


@router.post("", response_model=RepositoryRead, status_code=status.HTTP_201_CREATED)
async def add_repository(
    body: RepositoryCreate,
    service: RepositoryService = Depends(get_service),
) -> RepositoryRead:
    try:
        repo = await service.add_repository(owner=body.owner, name=body.name)
        return _to_read(repo)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{repository_id}", response_model=RepositoryRead)
async def get_repository(
    repository_id: str,
    service: RepositoryService = Depends(get_service),
) -> RepositoryRead:
    try:
        repo = await service.get_repository(repository_id)
        return _to_read(repo)
    except RepositoryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/{repository_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_repository(
    repository_id: str,
    service: RepositoryService = Depends(get_service),
) -> Response:
    try:
        await service.remove_repository(repository_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except RepositoryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
