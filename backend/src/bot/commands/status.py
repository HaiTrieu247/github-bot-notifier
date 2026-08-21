"""Discord slash command: /status [repository]"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

import discord
from discord import app_commands

from src.config import Config
from src.github.client import GitHubAPIError, get_github_client

logger = logging.getLogger(__name__)


def register(tree: app_commands.CommandTree) -> None:

    @tree.command(name="status", description="Show GitHub status for monitored repositories")
    @app_commands.describe(repository="Optional: specific repo name (e.g. homestay-backend)")
    async def status(interaction: discord.Interaction, repository: Optional[str] = None) -> None:
        await interaction.response.defer(thinking=True)
        if repository:
            await _status_single(interaction, repository)
        else:
            await _status_all(interaction)


async def _status_single(interaction: discord.Interaction, repo_name: str) -> None:
    github = get_github_client()
    full_name: Optional[str] = None
    for r in Config.monitored_repositories:
        if r.split("/")[-1] == repo_name or r == repo_name:
            full_name = r
            break

    if not full_name:
        await interaction.followup.send(f"❌ Repository `{repo_name}` is not monitored.", ephemeral=True)
        return

    try:
        repo_data = await github.get_repo(full_name)
        workflow_runs = await github.get_workflow_runs(full_name, per_page=1)
        deployments = await github.get_deployments(full_name, per_page=1)
    except GitHubAPIError as exc:
        await interaction.followup.send(
            f"❌ Unable to retrieve GitHub status.\n\nReason: {exc}\n\nPlease try again later.",
            ephemeral=True,
        )
        return

    latest_run = workflow_runs[0] if workflow_runs else None
    latest_dep = deployments[0] if deployments else None

    ci_status = "—"
    if latest_run:
        conclusion = latest_run.get("conclusion")
        status_val = latest_run.get("status")
        if conclusion == "success":
            ci_status = "🟢 SUCCESS"
        elif conclusion == "failure":
            ci_status = "🔴 FAILED"
        elif status_val in ("queued", "in_progress"):
            ci_status = "🟡 RUNNING"
        else:
            ci_status = f"⚪ {conclusion or status_val}"

    dep_status = "—"
    if latest_dep:
        dep_statuses = await github.get_deployment_statuses(full_name, latest_dep["id"])
        if dep_statuses:
            dep_state = dep_statuses[0].get("state", "")
            if dep_state == "success":
                dep_status = "🟢 SUCCESS"
            elif dep_state in ("failure", "error"):
                dep_status = "🔴 FAILED"
            else:
                dep_status = f"⚪ {dep_state}"

    default_branch = repo_data.get("default_branch", "main")
    commits = await github.get_commits(full_name, branch=default_branch, per_page=1)
    latest_commit = commits[0] if commits else None
    commit_sha = (latest_commit or {}).get("sha", "")[:7] if latest_commit else "—"
    commit_author = ((latest_commit or {}).get("commit", {}).get("author") or {}).get("name", "—")

    color = 0x57F287 if "🟢" in ci_status else (0xED4245 if "🔴" in ci_status else 0x5865F2)
    embed = discord.Embed(title=f"📊 {repo_name}", color=color, timestamp=datetime.now(timezone.utc))
    embed.add_field(name="Repository", value=f"`{full_name}`", inline=False)
    embed.add_field(name="Default branch", value=f"`{default_branch}`", inline=True)
    embed.add_field(name="Latest commit", value=f"`{commit_sha}`", inline=True)
    embed.add_field(name="Author", value=f"`{commit_author}`", inline=True)
    embed.add_field(name="CI", value=ci_status, inline=True)
    embed.add_field(name="Deployment", value=dep_status, inline=True)
    if latest_run:
        embed.add_field(name="Latest workflow", value=latest_run.get("name", "—"), inline=True)
    embed.add_field(name="\u200b", value=f"[Open GitHub](https://github.com/{full_name})", inline=False)
    embed.set_footer(text="Last checked")
    await interaction.followup.send(embed=embed)


async def _status_all(interaction: discord.Interaction) -> None:
    github = get_github_client()
    repos = Config.monitored_repositories

    if not repos:
        await interaction.followup.send("No repositories configured.", ephemeral=True)
        return

    embed = discord.Embed(title="GitHub Status", color=0x5865F2, timestamp=datetime.now(timezone.utc))

    for full_name in repos:
        repo_name = full_name.split("/")[-1]
        try:
            workflow_runs = await github.get_workflow_runs(full_name, per_page=1)
            latest_run = workflow_runs[0] if workflow_runs else None

            if latest_run:
                conclusion = latest_run.get("conclusion")
                status_val = latest_run.get("status")
                if conclusion == "success":
                    ci_icon, ci_label = "🟢", "SUCCESS"
                elif conclusion == "failure":
                    ci_icon, ci_label = "🔴", "FAILED"
                elif status_val in ("queued", "in_progress"):
                    ci_icon, ci_label = "🟡", "RUNNING"
                else:
                    ci_icon, ci_label = "⚪", conclusion or status_val or "—"
            else:
                ci_icon, ci_label = "⚪", "—"

            deploy_icon = "—"
            deployments = await github.get_deployments(full_name, per_page=1)
            if deployments:
                dep_statuses = await github.get_deployment_statuses(full_name, deployments[0]["id"])
                if dep_statuses:
                    dep_state = dep_statuses[0].get("state", "")
                    if dep_state == "success":
                        deploy_icon = "🟢 SUCCESS"
                    elif dep_state in ("failure", "error"):
                        deploy_icon = "🔴 FAILED"
                    else:
                        deploy_icon = f"⚪ {dep_state}"

            embed.add_field(
                name=f"{ci_icon} {repo_name}",
                value=f"CI: {ci_icon} {ci_label}\nDeploy: {deploy_icon}",
                inline=False,
            )
        except GitHubAPIError as exc:
            embed.add_field(name=f"⚠️ {repo_name}", value=f"Error: {exc}", inline=False)

    embed.set_footer(text="Last checked: just now")
    await interaction.followup.send(embed=embed)
