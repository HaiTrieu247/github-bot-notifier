"""Discord slash command: /logs [repository] [limit]"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

import discord
from discord import app_commands

from src.config import Config
from src.db.main import AsyncSessionLocal
from src.repository.event import EventRepo
from src.repository.repository import RepositoryRepo

logger = logging.getLogger(__name__)

EVENT_ICONS = {
    "push": "📦 PUSH",
    "workflow_run": "⚙️ WORKFLOW",
    "pull_request": "🔵 PR",
    "deployment_status": "🚀 DEPLOY",
    "deployment": "🚀 DEPLOY",
}


def _event_icon(event_type: str, payload: Optional[dict]) -> str:
    if event_type == "workflow_run" and payload:
        conclusion = (payload.get("workflow_run") or {}).get("conclusion")
        if conclusion == "success":
            return "🟢 CI SUCCESS"
        elif conclusion == "failure":
            return "🔴 CI FAILED"
        elif conclusion == "cancelled":
            return "🚫 CI CANCELLED"
    if event_type == "pull_request" and payload:
        action = payload.get("action", "")
        merged = (payload.get("pull_request") or {}).get("merged", False)
        if action == "closed" and merged:
            return "🟣 PR MERGED"
        if action == "opened":
            return "🔵 PR OPENED"
    return EVENT_ICONS.get(event_type, f"📋 {event_type.upper()}")


def register(tree: app_commands.CommandTree) -> None:

    @tree.command(name="logs", description="Show recent GitHub activity from the database")
    @app_commands.describe(
        repository="Filter by repo name (e.g. homestay-backend)",
        limit="Number of events to show (default: 10, max: 25)",
    )
    async def logs(
        interaction: discord.Interaction,
        repository: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> None:
        await interaction.response.defer(thinking=True)
        limit = min(limit or 10, 25)

        async with AsyncSessionLocal() as session:
            repo_id: Optional[str] = None
            if repository:
                full_name: Optional[str] = None
                for r in Config.monitored_repositories:
                    if r.split("/")[-1] == repository or r == repository:
                        full_name = r
                        break
                if full_name:
                    repo_repo = RepositoryRepo(session)
                    repo = await repo_repo.get_by_full_name(full_name)
                    if repo:
                        repo_id = repo.id

            event_repo = EventRepo(session)
            events = await event_repo.get_recent(repository_id=repo_id, limit=limit)

        embed = discord.Embed(
            title="Recent GitHub Activity",
            color=0x5865F2,
            timestamp=datetime.now(timezone.utc),
        )

        if not events:
            embed.description = "No events found."
        else:
            lines = []
            for event in events:
                ts = event.created_at
                time_str = ts.strftime("%H:%M") if ts else "—"
                icon = _event_icon(event.event_type, event.payload)
                repo_name = ""
                if event.payload:
                    repo_name = (event.payload.get("repository") or {}).get("name", "")
                lines.append(f"`{time_str}` {icon}\n{repo_name}")
            embed.description = "\n\n".join(lines)

        embed.set_footer(text=f"Showing last {limit} events")
        await interaction.followup.send(embed=embed)
