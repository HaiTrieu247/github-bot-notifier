"""Discord slash command: /check [repository]"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

import discord
from discord import app_commands

from src.db.main import AsyncSessionLocal
from src.github.client import GitHubAPIError, get_github_client
from src.repository.repository import RepositoryRepo
from src.repository.workflow_run import WorkflowRunRepo
from src.repository.deployment import DeploymentRepo

logger = logging.getLogger(__name__)


def register(tree: app_commands.CommandTree) -> None:

    @tree.command(name="check", description="Force-check GitHub status and sync to database")
    @app_commands.describe(repository="Repo name to check (e.g. homestay-backend)")
    async def check(
        interaction: discord.Interaction,
        repository: Optional[str] = None,
    ) -> None:
        await interaction.response.defer(thinking=True)

        from src.services import config_service
        all_repos = await config_service.get_monitored_repositories()
        repos_to_check: list[str] = []
        if repository:
            for r in all_repos:
                if r.split("/")[-1] == repository or r == repository:
                    repos_to_check = [r]
                    break
            if not repos_to_check:
                await interaction.followup.send(
                    f"❌ Repository `{repository}` is not monitored.", ephemeral=True
                )
                return
        else:
            repos_to_check = all_repos

        if not repos_to_check:
            await interaction.followup.send("No repositories configured.", ephemeral=True)
            return

        github = await get_github_client()
        results = []

        for full_name in repos_to_check:
            repo_name = full_name.split("/")[-1]
            try:
                workflow_runs = await github.get_workflow_runs(full_name, per_page=1)
                latest_run = workflow_runs[0] if workflow_runs else None
                deployments = await github.get_deployments(full_name, per_page=1)
                latest_dep = deployments[0] if deployments else None

                async with AsyncSessionLocal() as session:
                    repo_repo = RepositoryRepo(session)
                    workflow_repo = WorkflowRunRepo(session)
                    deployment_repo = DeploymentRepo(session)

                    db_repo = await repo_repo.get_by_full_name(full_name)
                    if db_repo:
                        if latest_run:
                            run_data = latest_run
                            started_at: Optional[datetime] = None
                            completed_at: Optional[datetime] = None
                            try:
                                if run_data.get("run_started_at"):
                                    started_at = datetime.fromisoformat(
                                        run_data["run_started_at"].replace("Z", "+00:00")
                                    )
                                if run_data.get("updated_at") and run_data.get("status") == "completed":
                                    completed_at = datetime.fromisoformat(
                                        run_data["updated_at"].replace("Z", "+00:00")
                                    )
                            except (ValueError, AttributeError):
                                pass

                            await workflow_repo.upsert(
                                repository_id=db_repo.id,
                                github_run_id=run_data.get("id", 0),
                                workflow_name=run_data.get("name"),
                                branch=run_data.get("head_branch"),
                                commit_sha=(run_data.get("head_sha") or "")[:7],
                                status=run_data.get("status"),
                                conclusion=run_data.get("conclusion"),
                                run_url=run_data.get("html_url"),
                                started_at=started_at,
                                completed_at=completed_at,
                            )

                        if latest_dep:
                            dep_statuses = await github.get_deployment_statuses(full_name, latest_dep["id"])
                            dep_state = dep_statuses[0].get("state") if dep_statuses else None
                            await deployment_repo.upsert(
                                repository_id=db_repo.id,
                                github_deployment_id=latest_dep["id"],
                                environment=latest_dep.get("environment"),
                                status=dep_state,
                                commit_sha=(latest_dep.get("sha") or "")[:7],
                            )

                        await session.commit()

                ci_str = "—"
                if latest_run:
                    c = latest_run.get("conclusion")
                    s = latest_run.get("status")
                    if c == "success":
                        ci_str = "🟢 SUCCESS"
                    elif c == "failure":
                        ci_str = "🔴 FAILED"
                    elif s in ("queued", "in_progress"):
                        ci_str = "🟡 RUNNING"
                    else:
                        ci_str = f"⚪ {c or s}"

                results.append(f"**{repo_name}** — CI: {ci_str}")

            except GitHubAPIError as exc:
                results.append(f"**{repo_name}** — ❌ Error: {exc}")

        embed = discord.Embed(
            title="✅ GitHub Check Complete",
            description="\n".join(results),
            color=0x57F287,
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_footer(text="Database synced")
        await interaction.followup.send(embed=embed)
