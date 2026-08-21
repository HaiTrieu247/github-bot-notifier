"""Pydantic schemas for health check endpoint."""

from __future__ import annotations

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    database: str = "ok"
    discord: str = "ok"
    github: str = "ok"
