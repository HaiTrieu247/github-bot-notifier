"""Pydantic schemas for Repository endpoints."""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class RepositoryCreate(BaseModel):
    owner: str = Field(..., min_length=1, max_length=255)
    name: str = Field(..., min_length=1, max_length=255)


class RepositoryRead(BaseModel):
    id: str
    owner: str
    name: str
    full_name: str
    default_branch: Optional[str]
    github_id: Optional[int]
    active: bool
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class RepositoryListResponse(BaseModel):
    items: list[RepositoryRead]
    total: int
