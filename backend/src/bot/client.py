"""Discord Bot client — runs in background thread, registers slash commands."""

from __future__ import annotations

import asyncio
import logging
import threading
from typing import Optional

import discord
from discord import app_commands

from src.config import Config

logger = logging.getLogger(__name__)


class GitHubDiscordBot(discord.Client):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self._ready_event = asyncio.Event()

    async def setup_hook(self) -> None:
        guild_id = Config.discord_guild_id
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


def start_bot() -> None:
    """Start the Discord bot in a background thread with its own event loop."""
    global _bot, _bot_thread, _bot_loop

    if not Config.discord_token:
        logger.warning("DISCORD_TOKEN not set — Discord bot disabled")
        return

    _bot = GitHubDiscordBot()
    _register_commands(_bot)

    def _run() -> None:
        global _bot_loop
        _bot_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_bot_loop)
        _bot_loop.run_until_complete(_bot.start(Config.discord_token))  # type: ignore[union-attr]

    _bot_thread = threading.Thread(target=_run, daemon=True, name="discord-bot")
    _bot_thread.start()
    logger.info("Discord bot thread started")


def _register_commands(bot: GitHubDiscordBot) -> None:
    from src.bot.commands.check import register as reg_check
    from src.bot.commands.logs import register as reg_logs
    from src.bot.commands.repos import register as reg_repos
    from src.bot.commands.status import register as reg_status

    reg_status(bot.tree)
    reg_repos(bot.tree)
    reg_logs(bot.tree)
    reg_check(bot.tree)
