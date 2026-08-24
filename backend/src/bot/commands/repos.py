"""Discord slash command: /repos"""

from __future__ import annotations

from datetime import datetime, timezone

import discord
from discord import app_commands


def register(tree: app_commands.CommandTree) -> None:

    @tree.command(name="repos", description="List all monitored GitHub repositories")
    async def repos(interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True)
        from src.services import config_service
        monitored = await config_service.get_monitored_repositories()

        embed = discord.Embed(
            title="Monitored Repositories",
            color=0x5865F2,
            timestamp=datetime.now(timezone.utc),
        )

        if not monitored:
            embed.description = "No repositories configured.\nUse the Admin Dashboard at `/admin` to add repositories."
        else:
            lines = []
            for i, full_name in enumerate(monitored, 1):
                repo_name = full_name.split("/")[-1]
                lines.append(f"`{i}.` [{repo_name}](https://github.com/{full_name}) 🟢 Active")
            embed.description = "\n".join(lines)

        embed.set_footer(text=f"Total: {len(monitored)} repositor{'y' if len(monitored) == 1 else 'ies'}")
        await interaction.followup.send(embed=embed)
