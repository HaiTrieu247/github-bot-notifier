"""Route: POST /github/webhook — GitHub webhook receiver."""

from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Config
from src.db.main import AsyncSessionLocal
from src.github.webhooks import verify_signature
from src.repository.repository import RepositoryRepo
from src.repository.event import EventRepo
from src.repository.workflow_run import WorkflowRunRepo
from src.repository.deployment import DeploymentRepo
from src.services.event import EventService
from src.services.notification import NotificationService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["GitHub Webhook"])


def _build_event_service(session: AsyncSession) -> EventService:
    """Factory: wire up the full DI graph for EventService."""
    return EventService(
        session=session,
        repo_repo=RepositoryRepo(session),
        event_repo=EventRepo(session),
        workflow_repo=WorkflowRunRepo(session),
        deployment_repo=DeploymentRepo(session),
        notification_svc=NotificationService(),
    )


@router.post("/github/webhook")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hub_signature_256: str = Header(default="", alias="X-Hub-Signature-256"),
    x_github_event: str = Header(default="", alias="X-GitHub-Event"),
    x_github_delivery: str = Header(default="", alias="X-GitHub-Delivery"),
) -> dict[str, str]:
    payload_bytes = await request.body()

    # ── Signature verification ────────────────────────────────────────────────
    if not verify_signature(payload_bytes, x_hub_signature_256, Config.github_webhook_secret):
        logger.warning("Invalid webhook signature — delivery=%s", x_github_delivery)
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    payload = await request.json()
    repo_full_name = (payload.get("repository") or {}).get("full_name", "unknown")

    logger.info(
        "GitHub webhook received | event=%s | repo=%s | delivery=%s",
        x_github_event,
        repo_full_name,
        x_github_delivery,
    )

    # ── Background processing (return 200 immediately) ────────────────────────
    async def _process() -> None:
        async with AsyncSessionLocal() as session:
            svc = _build_event_service(session)
            await svc.process(
                event_type=x_github_event,
                github_event_id=x_github_delivery,
                payload=payload,
            )

    background_tasks.add_task(_process)
    return {"status": "accepted"}
