"""Route: /api/v1/config — Dynamic runtime configuration CRUD."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.services import config_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/config", tags=["Config"])


class ConfigUpdateRequest(BaseModel):
    discord_token: str | None = None
    discord_guild_id: str | None = None
    discord_default_channel_id: str | None = None
    discord_repo_channel_map: str | None = None
    github_token: str | None = None
    github_webhook_secret: str | None = None
    github_repositories: str | None = None


class ConfigResponse(BaseModel):
    discord_token: str = ""
    discord_guild_id: str = ""
    discord_default_channel_id: str = ""
    discord_repo_channel_map: str = ""
    github_token: str = ""
    github_webhook_secret: str = ""
    github_repositories: str = ""


@router.get("", response_model=ConfigResponse, summary="Get current config (sensitive values masked)")
async def get_config() -> ConfigResponse:
    """Returns all dynamic config values. Sensitive fields (tokens, secrets) are masked."""
    data = await config_service.get_all_masked()
    return ConfigResponse(**{k: data.get(k, "") for k in ConfigResponse.model_fields})


@router.get("/raw", response_model=ConfigResponse, summary="Get full config (unmasked — internal use)")
async def get_config_raw() -> ConfigResponse:
    """Returns all config values unmasked. Use this for the admin dashboard internal calls."""
    data = await config_service.get_all()
    return ConfigResponse(**{k: data.get(k, "") for k in ConfigResponse.model_fields})


@router.put("", response_model=ConfigResponse, summary="Update config values")
async def update_config(body: ConfigUpdateRequest) -> ConfigResponse:
    """
    Update one or more config keys. Only non-None fields are updated.
    Changes take effect immediately for new webhook events.
    To apply Discord token/guild changes, also call POST /api/v1/config/reload.
    """
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields provided to update")

    await config_service.set_many(updates)
    logger.info("Config updated via API: %s", list(updates.keys()))

    data = await config_service.get_all_masked()
    return ConfigResponse(**{k: data.get(k, "") for k in ConfigResponse.model_fields})


@router.post("/reload", summary="Restart Discord bot with new config")
async def reload_bot() -> dict[str, str]:
    """
    Restarts the Discord bot thread with the latest config from DB.
    Required after changing discord_token or discord_guild_id.
    """
    try:
        from src.bot.client import restart_bot
        msg = await restart_bot()
        return {"status": "ok", "message": msg}
    except Exception as exc:
        logger.error("Bot reload failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Bot reload failed: {exc}") from exc
