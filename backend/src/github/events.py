"""GitHub event parsing — converts raw webhook payload into typed structures."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class PushEvent:
    repo_full_name: str
    repo_name: str
    branch: str
    author: str
    commit_sha: str
    commit_message: str
    commit_url: str
    files_changed: int
    compare_url: str


@dataclass
class WorkflowRunEvent:
    repo_full_name: str
    repo_name: str
    workflow_name: str
    branch: str
    commit_sha: str
    status: str  # queued, in_progress, completed
    conclusion: Optional[str]  # success, failure, cancelled, skipped, timed_out
    run_id: int
    run_url: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]


@dataclass
class PullRequestEvent:
    repo_full_name: str
    repo_name: str
    action: str  # opened, closed, merged, synchronize, reopened
    pr_number: int
    title: str
    author: str
    head_branch: str
    base_branch: str
    pr_url: str
    merged: bool
    merged_by: Optional[str]


@dataclass
class DeploymentEvent:
    repo_full_name: str
    repo_name: str
    deployment_id: int
    environment: str
    commit_sha: str
    deploy_url: Optional[str]


@dataclass
class DeploymentStatusEvent:
    repo_full_name: str
    repo_name: str
    deployment_id: int
    environment: str
    state: str  # pending, success, failure, error, inactive
    commit_sha: str
    deploy_url: Optional[str]
    description: Optional[str]


def parse_push_event(payload: dict[str, Any]) -> PushEvent:
    repo = payload.get("repository", {})
    head_commit = payload.get("head_commit", {})
    ref = payload.get("ref", "")
    branch = ref.replace("refs/heads/", "") if ref.startswith("refs/heads/") else ref
    commits = payload.get("commits", [])

    author_info = head_commit.get("author", {})
    author = author_info.get("username") or author_info.get("name", "unknown")

    return PushEvent(
        repo_full_name=repo.get("full_name", ""),
        repo_name=repo.get("name", ""),
        branch=branch,
        author=author,
        commit_sha=head_commit.get("id", "")[:7],
        commit_message=head_commit.get("message", "").split("\n")[0],
        commit_url=head_commit.get("url", ""),
        files_changed=len(commits),
        compare_url=payload.get("compare", ""),
    )


def parse_workflow_run_event(payload: dict[str, Any]) -> WorkflowRunEvent:
    repo = payload.get("repository", {})
    run = payload.get("workflow_run", {})

    started_at_raw = run.get("run_started_at") or run.get("created_at")
    completed_at_raw = run.get("updated_at") if run.get("status") == "completed" else None

    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    try:
        if started_at_raw:
            started_at = datetime.fromisoformat(started_at_raw.replace("Z", "+00:00"))
        if completed_at_raw:
            completed_at = datetime.fromisoformat(completed_at_raw.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        pass

    return WorkflowRunEvent(
        repo_full_name=repo.get("full_name", ""),
        repo_name=repo.get("name", ""),
        workflow_name=run.get("name", ""),
        branch=run.get("head_branch", ""),
        commit_sha=run.get("head_sha", "")[:7],
        status=run.get("status", ""),
        conclusion=run.get("conclusion"),
        run_id=run.get("id", 0),
        run_url=run.get("html_url", ""),
        started_at=started_at,
        completed_at=completed_at,
    )


def parse_pull_request_event(payload: dict[str, Any]) -> PullRequestEvent:
    repo = payload.get("repository", {})
    pr = payload.get("pull_request", {})
    action = payload.get("action", "")
    merged = pr.get("merged", False)
    merged_by_info = pr.get("merged_by") or {}

    return PullRequestEvent(
        repo_full_name=repo.get("full_name", ""),
        repo_name=repo.get("name", ""),
        action=action,
        pr_number=pr.get("number", 0),
        title=pr.get("title", ""),
        author=(pr.get("user") or {}).get("login", "unknown"),
        head_branch=pr.get("head", {}).get("ref", ""),
        base_branch=pr.get("base", {}).get("ref", ""),
        pr_url=pr.get("html_url", ""),
        merged=merged,
        merged_by=merged_by_info.get("login") if merged_by_info else None,
    )


def parse_deployment_event(payload: dict[str, Any]) -> DeploymentEvent:
    repo = payload.get("repository", {})
    dep = payload.get("deployment", {})

    return DeploymentEvent(
        repo_full_name=repo.get("full_name", ""),
        repo_name=repo.get("name", ""),
        deployment_id=dep.get("id", 0),
        environment=dep.get("environment", ""),
        commit_sha=(dep.get("sha") or "")[:7],
        deploy_url=dep.get("url"),
    )


def parse_deployment_status_event(payload: dict[str, Any]) -> DeploymentStatusEvent:
    repo = payload.get("repository", {})
    dep = payload.get("deployment", {})
    dep_status = payload.get("deployment_status", {})

    return DeploymentStatusEvent(
        repo_full_name=repo.get("full_name", ""),
        repo_name=repo.get("name", ""),
        deployment_id=dep.get("id", 0),
        environment=dep.get("environment", ""),
        state=dep_status.get("state", ""),
        commit_sha=(dep.get("sha") or "")[:7],
        deploy_url=dep_status.get("target_url"),
        description=dep_status.get("description"),
    )
