"""
Dynamic Config Service — reads/writes config from DB, with in-memory cache.

All Discord/GitHub settings are stored in app_config table (DB is source of truth).
On first startup, seeds missing keys from environment variables as defaults.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# ── All supported config keys ─────────────────────────────────────────────────
CONFIG_KEYS = [
    "discord_token",
    "discord_guild_id",
    "discord_default_channel_id",
    "discord_repo_channel_map",
    "github_token",
    "github_webhook_secret",
    "github_repositories",
]

# Sensitive keys — masked in API responses
SENSITIVE_KEYS = {"discord_token", "github_token", "github_webhook_secret"}

# ── In-memory cache ───────────────────────────────────────────────────────────
_cache: dict[str, str] = {}
_cache_loaded: bool = False


async def _load_cache() -> None:
    """Load all config from DB into the in-memory cache."""
    global _cache, _cache_loaded
    from src.db.main import AsyncSessionLocal
    from src.repository.config import ConfigRepo

    async with AsyncSessionLocal() as session:
        repo = ConfigRepo(session)
        _cache = await repo.get_all()
    _cache_loaded = True
    logger.debug("Config cache loaded: %d keys", len(_cache))


def _invalidate_cache() -> None:
    global _cache_loaded
    _cache_loaded = False
    _cache.clear()


async def _ensure_loaded() -> None:
    if not _cache_loaded:
        await _load_cache()


# ── Seed from environment (first run) ─────────────────────────────────────────

async def seed_from_env() -> None:
    """
    Seed DB config from environment variables for any keys not already set.
    Called once at startup — env vars are the initial defaults.
    """
    from src.db.main import AsyncSessionLocal
    from src.repository.config import ConfigRepo

    env_defaults = {
        "discord_token": os.getenv("DISCORD_TOKEN", ""),
        "discord_guild_id": os.getenv("DISCORD_GUILD_ID", ""),
        "discord_default_channel_id": os.getenv("DISCORD_DEFAULT_CHANNEL_ID", ""),
        "discord_repo_channel_map": os.getenv("DISCORD_REPO_CHANNEL_MAP", ""),
        "github_token": os.getenv("GITHUB_TOKEN", ""),
        "github_webhook_secret": os.getenv("GITHUB_WEBHOOK_SECRET", ""),
        "github_repositories": os.getenv("GITHUB_REPOSITORIES", ""),
    }

    async with AsyncSessionLocal() as session:
        repo = ConfigRepo(session)
        existing = await repo.get_all()
        to_seed = {k: v for k, v in env_defaults.items() if k not in existing}
        if to_seed:
            await repo.set_many(to_seed)
            await session.commit()
            logger.info("Seeded %d config keys from environment", len(to_seed))
        else:
            logger.info("Config already exists in DB — skipping env seed")

    _invalidate_cache()


# ── Public getters ────────────────────────────────────────────────────────────

async def get(key: str) -> str:
    await _ensure_loaded()
    return _cache.get(key, "")


async def get_all() -> dict[str, str]:
    await _ensure_loaded()
    return dict(_cache)


async def get_all_masked() -> dict[str, str]:
    """Return all config, with sensitive values masked for API responses."""
    data = await get_all()
    return {
        k: ("***" if k in SENSITIVE_KEYS and v else v)
        for k, v in data.items()
    }


# ── Public setters ────────────────────────────────────────────────────────────

async def set_many(mapping: dict[str, str]) -> None:
    """Update config keys in DB and invalidate the cache."""
    from src.db.main import AsyncSessionLocal
    from src.repository.config import ConfigRepo

    async with AsyncSessionLocal() as session:
        repo = ConfigRepo(session)
        await repo.set_many(mapping)
        await session.commit()

    _invalidate_cache()
    logger.info("Config updated: %s", list(mapping.keys()))


# ── Typed helpers (for internal use) ─────────────────────────────────────────

async def get_discord_token() -> str:
    return await get("discord_token")


async def get_discord_guild_id() -> int:
    val = await get("discord_guild_id")
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0


async def get_discord_default_channel_id() -> int:
    val = await get("discord_default_channel_id")
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0


async def get_discord_repo_channel_map() -> dict[str, int]:
    val = await get("discord_repo_channel_map")
    mapping: dict[str, int] = {}
    if not val:
        return mapping
    for entry in val.split(","):
        entry = entry.strip()
        if ":" not in entry:
            continue
        repo, channel_id_str = entry.rsplit(":", 1)
        try:
            mapping[repo.strip()] = int(channel_id_str.strip())
        except ValueError:
            pass
    return mapping


async def get_channel_id(full_repo_name: str) -> Optional[int]:
    mapping = await get_discord_repo_channel_map()
    if full_repo_name in mapping:
        return mapping[full_repo_name]
    default = await get_discord_default_channel_id()
    return default if default else None


async def get_github_token() -> str:
    return await get("github_token")


async def get_github_webhook_secret() -> str:
    return await get("github_webhook_secret")


async def get_monitored_repositories() -> list[str]:
    val = await get("github_repositories")
    if not val:
        return []
    return [r.strip() for r in val.split(",") if r.strip()]
