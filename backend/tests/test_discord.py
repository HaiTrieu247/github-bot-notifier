"""Tests for Discord embed builders."""

from datetime import datetime, timezone

import discord

from src.github.events import (
    DeploymentStatusEvent,
    PullRequestEvent,
    PushEvent,
    WorkflowRunEvent,
)
from src.bot.notifications import (
    build_push_embed,
    build_workflow_embed,
    build_pr_embed,
    build_deployment_status_embed,
)


def test_build_push_embed():
    event = PushEvent(
        repo_full_name="Kens0107/homestay-backend",
        repo_name="homestay-backend",
        branch="main",
        author="Kens0107",
        commit_sha="a82f31c",
        commit_message="fix authentication bug",
        commit_url="https://github.com/commit/abc",
        files_changed=3,
        compare_url="https://github.com/compare/abc",
    )
    embed = build_push_embed(event)
    assert isinstance(embed, discord.Embed)
    assert "Push" in embed.title
    assert embed.color.value == 0x5865F2


def test_build_workflow_success_embed():
    event = WorkflowRunEvent(
        repo_full_name="Kens0107/homestay-backend",
        repo_name="homestay-backend",
        workflow_name="CI",
        branch="main",
        commit_sha="a82f31c",
        status="completed",
        conclusion="success",
        run_id=123,
        run_url="https://github.com/runs/123",
        started_at=datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
        completed_at=datetime(2026, 1, 1, 10, 2, 31, tzinfo=timezone.utc),
    )
    embed = build_workflow_embed(event)
    assert embed is not None
    assert "Success" in embed.title
    assert embed.color.value == 0x57F287


def test_build_workflow_queued_returns_none():
    event = WorkflowRunEvent(
        repo_full_name="r/r", repo_name="r", workflow_name="CI", branch="main",
        commit_sha="abc", status="queued", conclusion=None,
        run_id=1, run_url="", started_at=None, completed_at=None,
    )
    assert build_workflow_embed(event) is None


def test_build_pr_embed_opened():
    event = PullRequestEvent(
        repo_full_name="Kens0107/homestay-backend", repo_name="homestay-backend",
        action="opened", pr_number=42, title="Add auth middleware", author="Kens0107",
        head_branch="feature/auth", base_branch="main",
        pr_url="https://github.com/pr/42", merged=False, merged_by=None,
    )
    embed = build_pr_embed(event)
    assert embed is not None
    assert "Opened" in embed.title


def test_build_pr_embed_merged():
    event = PullRequestEvent(
        repo_full_name="Kens0107/homestay-backend", repo_name="homestay-backend",
        action="closed", pr_number=42, title="Add auth middleware", author="Kens0107",
        head_branch="feature/auth", base_branch="main",
        pr_url="https://github.com/pr/42", merged=True, merged_by="Kens0107",
    )
    embed = build_pr_embed(event)
    assert embed is not None
    assert "Merged" in embed.title


def test_build_deployment_status_success():
    event = DeploymentStatusEvent(
        repo_full_name="Kens0107/homestay-backend", repo_name="homestay-backend",
        deployment_id=1, environment="production", state="success",
        commit_sha="a82f31c", deploy_url="https://staging.example.com",
        description="Deploy OK",
    )
    embed = build_deployment_status_embed(event)
    assert embed is not None
    assert "Success" in embed.title


def test_build_deployment_inactive_skipped():
    event = DeploymentStatusEvent(
        repo_full_name="r/r", repo_name="r", deployment_id=1,
        environment="production", state="inactive",
        commit_sha="abc", deploy_url=None, description=None,
    )
    assert build_deployment_status_embed(event) is None
