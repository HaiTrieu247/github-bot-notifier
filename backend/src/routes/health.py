"""Route: GET /health — health check endpoint."""

from __future__ import annotations

import logging

from fastapi import APIRouter

from src.db.main import AsyncSessionLocal
from src.schemas.health import HealthResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    result = HealthResponse(status="ok")

    # Database check
    try:
        from sqlalchemy import text
        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT 1"))
        result.database = "ok"
    except Exception as exc:
        logger.error("Health check — database error: %s", exc)
        result.database = "error"
        result.status = "degraded"

    # Discord check
    try:
        from src.bot.client import get_bot
        bot = get_bot()
        result.discord = "ok" if (bot and not bot.is_closed()) else "not_connected"
    except Exception:
        result.discord = "error"

    result.github = "ok"
    return result
