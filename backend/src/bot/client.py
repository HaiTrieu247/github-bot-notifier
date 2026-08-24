"""Discord Bot client — runs in background thread, registers slash commands.

Bot is now dynamically configurable: token and guild_id are loaded from DB
at runtime. Call restart_bot() after changing Discord config to reconnect.
"""

from __future__ import annotations

import asyncio
import logging
import threading
from typing import Optional

import discord
from discord import app_commands

logger = logging.getLogger(__name__)


class GitHubDiscordBot(discord.Client):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self._ready_event = asyncio.Event()

    async def setup_hook(self) -> None:
        from src.services import config_service
        guild_id = await config_service.get_discord_guild_id()
        if guild_id:
            guild = discord.Object(id=guild_id)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            logger.info("Slash commands synced to guild %s", guild_id)
        else:
            await self.tree.sync()
            logger.info("Slash commands synced globally")

    async def on_ready(self) -> None:
        logger.info(
            "Discord Bot connected as %s (ID: %s)",
            self.user,
            self.user.id if self.user else "?",
        )
        self._ready_event.set()

    async def wait_until_bot_ready(self, timeout: float = 30.0) -> None:
        try:
            await asyncio.wait_for(self._ready_event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning("Discord bot did not become ready within %ss", timeout)


_bot: Optional[GitHubDiscordBot] = None
_bot_thread: Optional[threading.Thread] = None
_bot_loop: Optional[asyncio.AbstractEventLoop] = None


def get_bot() -> Optional[GitHubDiscordBot]:
    return _bot


async def start_bot() -> None:
    """Start the Discord bot in a background thread with its own event loop.
    Token is loaded from DB (config_service). If no token is set, bot is skipped.
    """
    await _start_bot_async()


async def _start_bot_async() -> None:
    global _bot, _bot_thread, _bot_loop

    from src.services import config_service
    token = await config_service.get_discord_token()

    if not token:
        logger.warning("discord_token not configured in DB — Discord bot disabled")
        return

    _bot = GitHubDiscordBot()
    _register_commands(_bot)

    def _run() -> None:
        global _bot_loop
        _bot_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_bot_loop)
        _bot_loop.run_until_complete(_bot.start(token))  # type: ignore[union-attr]

    _bot_thread = threading.Thread(target=_run, daemon=True, name="discord-bot")
    _bot_thread.start()
    logger.info("Discord bot thread started")


async def stop_bot() -> None:
    """Gracefully close the current bot instance."""
    global _bot, _bot_thread, _bot_loop
    if _bot and not _bot.is_closed():
        logger.info("Stopping Discord bot for restart…")
        if _bot_loop and _bot_loop.is_running():
            future = asyncio.run_coroutine_threadsafe(_bot.close(), _bot_loop)
            try:
                future.result(timeout=10)
            except Exception as exc:
                logger.warning("Error closing bot: %s", exc)
    _bot = None
    _bot_thread = None
    _bot_loop = None


async def restart_bot() -> str:
    """Stop current bot, reload config from DB, start fresh bot thread.
    Returns status message.
    """
    await stop_bot()
    await _start_bot_async()
    return "Bot restarted with new configuration"


def _register_commands(bot: GitHubDiscordBot) -> None:
    from src.bot.commands.check import register as reg_check
    from src.bot.commands.logs import register as reg_logs
    from src.bot.commands.repos import register as reg_repos
    from src.bot.commands.status import register as reg_status

    reg_status(bot.tree)
    reg_repos(bot.tree)
    reg_logs(bot.tree)
    reg_check(bot.tree)
