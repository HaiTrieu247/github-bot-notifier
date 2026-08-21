"""Service: GitHub event processing (class-based, blueprint DI pattern).

Flow: parse event → idempotency check → persist → update specialised tables → notify Discord
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.repository.repository import RepositoryRepo
from src.repository.event import EventRepo
from src.repository.workflow_run import WorkflowRunRepo
from src.repository.deployment import DeploymentRepo
from src.services.notification import NotificationService
from src.github import events as github_events

logger = logging.getLogger(__name__)


class EventNotFoundError(Exception):
    pass


class EventService:
    def __init__(
        self,
        session: AsyncSession,
        repo_repo: RepositoryRepo,
        event_repo: EventRepo,
        workflow_repo: WorkflowRunRepo,
        deployment_repo: DeploymentRepo,
        notification_svc: NotificationService,
    ) -> None:
        self.session = session
        self.repo_repo = repo_repo
        self.event_repo = event_repo
        self.workflow_repo = workflow_repo
        self.deployment_repo = deployment_repo
        self.notification_svc = notification_svc

    async def process(
        self,
        *,
        event_type: str,
        github_event_id: str,
        payload: dict[str, Any],
    ) -> None:
        """
        Main processing entry point.
        1. Idempotency check
        2. Auto-create repository record if unknown
        3. Persist event
        4. Handle specialised tables + notify Discord
        """
        # 1. Idempotency
        if await self.event_repo.exists(github_event_id):
            logger.info("Duplicate event %s — skipping", github_event_id)
            return

        # 2. Resolve repository
        repo_data = payload.get("repository", {})
        full_name: str = repo_data.get("full_name", "")
        if not full_name:
            logger.warning("Payload missing repository.full_name for event %s", event_type)
            return

        owner, _, name = full_name.partition("/")
        db_repo = await self.repo_repo.get_by_full_name(full_name)
        if db_repo is None:
            db_repo = await self.repo_repo.create(
                owner=owner,
                name=name,
                full_name=full_name,
                default_branch=repo_data.get("default_branch"),
                github_id=repo_data.get("id"),
            )
            logger.info("Auto-created repository record: %s", full_name)

        # 3. Persist event
        event_record = await self.event_repo.create(
            repository_id=db_repo.id,
            event_type=event_type,
            github_event_id=github_event_id,
            payload=payload,
        )
        await self.session.commit()

        # 4. Dispatch
        try:
            await self._dispatch(event_type, payload, db_repo)
            await self.event_repo.mark_processed(event_record.id)
            await self.session.commit()
        except Exception as exc:
            logger.error(
                "Error processing event %s: %s", github_event_id, exc, exc_info=True
            )
            # Don't re-raise — event is already saved in the DB

    async def _dispatch(self, event_type: str, payload: dict[str, Any], db_repo: Any) -> None:
        """Route each event type to its handler."""

        if event_type == "push":
            event = github_events.parse_push_event(payload)
            await self.notification_svc.notify_push(event)

        elif event_type == "workflow_run":
            event = github_events.parse_workflow_run_event(payload)
            run = payload.get("workflow_run", {})
            started_at = _parse_dt(run.get("run_started_at"))
            completed_at = _parse_dt(run.get("updated_at")) if run.get("status") == "completed" else None

            await self.workflow_repo.upsert(
                repository_id=db_repo.id,
                github_run_id=run.get("id", 0),
                workflow_name=run.get("name"),
                branch=run.get("head_branch"),
                commit_sha=(run.get("head_sha") or "")[:7],
                status=run.get("status"),
                conclusion=run.get("conclusion"),
                run_url=run.get("html_url"),
                started_at=started_at,
                completed_at=completed_at,
            )
            await self.notification_svc.notify_workflow(event)

        elif event_type == "pull_request":
            event = github_events.parse_pull_request_event(payload)
            await self.notification_svc.notify_pull_request(event)

        elif event_type == "deployment":
            dep = payload.get("deployment", {})
            await self.deployment_repo.upsert(
                repository_id=db_repo.id,
                github_deployment_id=dep.get("id", 0),
                environment=dep.get("environment"),
                commit_sha=(dep.get("sha") or "")[:7],
            )

        elif event_type == "deployment_status":
            event = github_events.parse_deployment_status_event(payload)
            dep = payload.get("deployment", {})
            dep_status = payload.get("deployment_status", {})
            await self.deployment_repo.upsert(
                repository_id=db_repo.id,
                github_deployment_id=dep.get("id", 0),
                environment=dep.get("environment"),
                status=dep_status.get("state"),
                commit_sha=(dep.get("sha") or "")[:7],
                deploy_url=dep_status.get("target_url"),
            )
            await self.notification_svc.notify_deployment_status(event)

        else:
            logger.info("Unhandled event type: %s", event_type)


def _parse_dt(value: Any) -> "datetime | None":
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None
