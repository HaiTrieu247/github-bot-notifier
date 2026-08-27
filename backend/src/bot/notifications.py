"""Discord embed builders and notification sender."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

import discord

from src.github.events import (
    DeploymentStatusEvent,
    PullRequestEvent,
    PushEvent,
    WorkflowRunEvent,
)

logger = logging.getLogger(__name__)

COLOR_PUSH = 0x5865F2
COLOR_SUCCESS = 0x57F287
COLOR_FAILURE = 0xED4245
COLOR_PR_OPEN = 0x5865F2
COLOR_PR_MERGED = 0x9B59B6
COLOR_DEPLOY_SUCCESS = 0x57F287
COLOR_DEPLOY_FAIL = 0xED4245
COLOR_DEPLOY_PENDING = 0xFEE75C
COLOR_NEUTRAL = 0x95A5A6


def _duration_str(started: Optional[datetime], completed: Optional[datetime]) -> str:
    if not started or not completed:
        return "—"
    delta = completed - started
    total_seconds = int(delta.total_seconds())
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes}m {seconds}s" if minutes else f"{seconds}s"


def build_push_embed(event: PushEvent) -> discord.Embed:
    embed = discord.Embed(title="📦 New Push", color=COLOR_PUSH, timestamp=datetime.now(timezone.utc))
    embed.add_field(name="Repository", value=f"`{event.repo_full_name}`", inline=False)
    embed.add_field(name="Branch", value=f"`{event.branch}`", inline=True)
    embed.add_field(name="Author", value=f"`{event.author}`", inline=True)
    embed.add_field(name="Commit", value=f"`{event.commit_sha}`", inline=True)
    if event.commit_message:
        embed.add_field(name="Message", value=event.commit_message[:200], inline=False)
    embed.add_field(name="Files Changed", value=str(event.files_changed), inline=True)
    if event.commit_url:
        embed.add_field(name="\u200b", value=f"[View Commit]({event.commit_url})", inline=False)
    return embed


def build_workflow_embed(event: WorkflowRunEvent) -> Optional[discord.Embed]:
    if event.status != "completed":
        return None

    conclusion = event.conclusion or "unknown"
    if conclusion == "success":
        color, title = COLOR_SUCCESS, "🟢 GitHub Action Success"
    elif conclusion == "failure":
        color, title = COLOR_FAILURE, "🔴 GitHub Action Failed"
    elif conclusion == "timed_out":
        color, title = COLOR_FAILURE, "⏰ GitHub Action Timed Out"
    elif conclusion == "cancelled":
        color, title = COLOR_NEUTRAL, "🚫 GitHub Action Cancelled"
    else:
        color, title = COLOR_NEUTRAL, f"⚪ GitHub Action {conclusion.capitalize()}"

    embed = discord.Embed(title=title, color=color, timestamp=datetime.now(timezone.utc))
    embed.add_field(name="Repository", value=f"`{event.repo_name}`", inline=False)
    embed.add_field(name="Workflow", value=f"`{event.workflow_name}`", inline=True)
    embed.add_field(name="Branch", value=f"`{event.branch}`", inline=True)
    embed.add_field(name="Commit", value=f"`{event.commit_sha}`", inline=True)

    if conclusion == "success":
        embed.add_field(name="Duration", value=_duration_str(event.started_at, event.completed_at), inline=True)
    else:
        embed.add_field(name="Status", value=conclusion, inline=True)

    if event.run_url:
        embed.add_field(name="\u200b", value=f"[View Workflow]({event.run_url})", inline=False)
    return embed


def build_pr_embed(event: PullRequestEvent) -> Optional[discord.Embed]:
    if event.action in ("opened", "reopened"):
        embed = discord.Embed(title="🔵 Pull Request Opened", color=COLOR_PR_OPEN, timestamp=datetime.now(timezone.utc))
        embed.add_field(name="Repository", value=f"`{event.repo_name}`", inline=False)
        embed.add_field(name="PR", value=f"`#{event.pr_number}`", inline=True)
        embed.add_field(name="Author", value=f"`{event.author}`", inline=True)
        embed.add_field(name="Title", value=event.title[:200], inline=False)
        embed.add_field(name="Branch", value=f"`{event.head_branch}` → `{event.base_branch}`", inline=False)
        if event.pr_url:
            embed.add_field(name="\u200b", value=f"[View Pull Request]({event.pr_url})", inline=False)
        return embed

    if event.action == "closed" and event.merged:
        embed = discord.Embed(title="🟣 Pull Request Merged", color=COLOR_PR_MERGED, timestamp=datetime.now(timezone.utc))
        embed.add_field(name="Repository", value=f"`{event.repo_name}`", inline=False)
        embed.add_field(name="PR", value=f"`#{event.pr_number}`", inline=True)
        embed.add_field(name="Title", value=event.title[:200], inline=False)
        if event.merged_by:
            embed.add_field(name="Merged by", value=f"`{event.merged_by}`", inline=True)
        if event.pr_url:
            embed.add_field(name="\u200b", value=f"[View Pull Request]({event.pr_url})", inline=False)
        return embed

    return None


def build_deployment_status_embed(event: DeploymentStatusEvent) -> Optional[discord.Embed]:
    state = event.state
    if state == "success":
        color, title = COLOR_DEPLOY_SUCCESS, "🚀 Deployment Success"
    elif state in ("failure", "error"):
        color, title = COLOR_DEPLOY_FAIL, "🔴 Deployment Failed"
    elif state == "pending":
        color, title = COLOR_DEPLOY_PENDING, "⏳ Deployment Pending"
    else:
        return None

    embed = discord.Embed(title=title, color=color, timestamp=datetime.now(timezone.utc))
    embed.add_field(name="Repository", value=f"`{event.repo_name}`", inline=False)
    embed.add_field(name="Environment", value=f"`{event.environment}`", inline=True)
    embed.add_field(name="Commit", value=f"`{event.commit_sha}`", inline=True)
    embed.add_field(name="Status", value=state, inline=True)
    if event.description:
        embed.add_field(name="Info", value=event.description[:200], inline=False)
    if event.deploy_url:
        embed.add_field(name="\u200b", value=f"[View Deployment]({event.deploy_url})", inline=False)
    return embed


async def _send_on_bot_loop(
    bot: discord.Client,
    channel_id: int,
    embed: discord.Embed,
    retries: int,
) -> bool:
    """Runs inside the bot's own event loop — safe to touch discord.py internals here."""
    for attempt in range(retries + 1):
        try:
            channel = bot.get_channel(channel_id)
            if channel is None:
                channel = await bot.fetch_channel(channel_id)
            if not isinstance(channel, discord.TextChannel):
                logger.error("Channel %s is not a text channel", channel_id)
                return False
            await channel.send(embed=embed)
            logger.info("Discord notification sent to channel %s", channel_id)
            return True
        except discord.Forbidden:
            logger.error(
                "Missing permissions for channel %s — bot needs View Channel, "
                "Send Messages and Embed Links",
                channel_id,
            )
            return False
        except discord.NotFound:
            logger.error("Channel %s not found — check the configured channel ID", channel_id)
            return False
        except discord.HTTPException as exc:
            logger.warning("Discord send failed (attempt %d/%d): %s", attempt + 1, retries + 1, exc)
            if attempt == retries:
                logger.error("Discord notification failed after %d attempts", retries + 1)
                return False
    return False


async def send_to_channel(
    bot: discord.Client,
    channel_id: int,
    embed: discord.Embed,
    retries: int = 2,
) -> bool:
    """Send an embed to a Discord channel.

    The bot runs in a separate thread with its own event loop, while callers
    (webhook background tasks) run on the FastAPI loop. Awaiting discord.py
    coroutines across loops breaks aiohttp, so hand the work to the bot's loop.
    """
    from src.bot.client import get_bot_loop

    loop = get_bot_loop()
    if loop is None or not loop.is_running():
        logger.error("Discord bot loop is not running — cannot send notification")
        return False

    future = asyncio.run_coroutine_threadsafe(
        _send_on_bot_loop(bot, channel_id, embed, retries), loop
    )
    try:
        return await asyncio.wrap_future(future)
    except Exception as exc:
        logger.error("Failed to dispatch Discord notification: %s", exc, exc_info=True)
        return False
