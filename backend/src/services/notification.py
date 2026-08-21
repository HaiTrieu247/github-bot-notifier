"""Service: Discord notification orchestration (class-based, blueprint DI pattern)."""

from __future__ import annotations

import logging
from typing import Optional

from src.github.events import (
    DeploymentStatusEvent,
    PullRequestEvent,
    PushEvent,
    WorkflowRunEvent,
)

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Orchestrates sending Discord notifications for GitHub events.
    Errors are logged but never raised — a notification failure must not
    lose the event from the database.
    """

    async def notify_push(self, event: PushEvent) -> None:
        from src.bot.client import get_bot
        from src.bot.notifications import build_push_embed, send_to_channel

        bot = get_bot()
        if bot is None:
            logger.warning("Discord bot not running — skipping push notification")
            return

        from src.config import Config
        channel_id = Config.get_channel_id(event.repo_full_name)
        if not channel_id:
            logger.warning("No channel configured for %s", event.repo_full_name)
            return

        embed = build_push_embed(event)
        await send_to_channel(bot, channel_id, embed)

    async def notify_workflow(self, event: WorkflowRunEvent) -> None:
        from src.bot.client import get_bot
        from src.bot.notifications import build_workflow_embed, send_to_channel

        bot = get_bot()
        if bot is None:
            return

        embed = build_workflow_embed(event)
        if embed is None:
            return  # queued / in_progress — no notification

        from src.config import Config
        channel_id = Config.get_channel_id(event.repo_full_name)
        if not channel_id:
            logger.warning("No channel configured for %s", event.repo_full_name)
            return

        await send_to_channel(bot, channel_id, embed)

    async def notify_pull_request(self, event: PullRequestEvent) -> None:
        from src.bot.client import get_bot
        from src.bot.notifications import build_pr_embed, send_to_channel

        bot = get_bot()
        if bot is None:
            return

        embed = build_pr_embed(event)
        if embed is None:
            return

        from src.config import Config
        channel_id = Config.get_channel_id(event.repo_full_name)
        if not channel_id:
            logger.warning("No channel configured for %s", event.repo_full_name)
            return

        await send_to_channel(bot, channel_id, embed)

    async def notify_deployment_status(self, event: DeploymentStatusEvent) -> None:
        from src.bot.client import get_bot
        from src.bot.notifications import build_deployment_status_embed, send_to_channel

        bot = get_bot()
        if bot is None:
            return

        embed = build_deployment_status_embed(event)
        if embed is None:
            return

        from src.config import Config
        channel_id = Config.get_channel_id(event.repo_full_name)
        if not channel_id:
            logger.warning("No channel configured for %s", event.repo_full_name)
            return

        await send_to_channel(bot, channel_id, embed)
