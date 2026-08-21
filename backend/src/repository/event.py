"""Repository layer — Event CRUD (class-based, blueprint pattern)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.event import Event

logger = logging.getLogger(__name__)

VN_TZ = timezone(timedelta(hours=7))


class EventRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def exists(self, github_event_id: str) -> bool:
        """Idempotency check — true if this delivery ID was already processed."""
        result = await self.session.execute(
            select(Event.id).where(Event.github_event_id == github_event_id)
        )
        return result.scalar_one_or_none() is not None

    async def create(
        self,
        *,
        repository_id: str,
        event_type: str,
        github_event_id: str,
        payload: Optional[dict[str, Any]] = None,
    ) -> Event:
        event = Event(
            repository_id=repository_id,
            event_type=event_type,
            github_event_id=github_event_id,
            payload=payload,
        )
        self.session.add(event)
        await self.session.flush()
        await self.session.refresh(event)
        return event

    async def mark_processed(self, event_id: str) -> None:
        now = datetime.now(VN_TZ).replace(tzinfo=None)
        await self.session.execute(
            update(Event)
            .where(Event.id == event_id)
            .values(processed_at=now)
        )

    async def get_recent(
        self,
        *,
        repository_id: Optional[str] = None,
        limit: int = 20,
    ) -> list[Event]:
        q = select(Event).order_by(Event.created_at.desc()).limit(limit)
        if repository_id:
            q = q.where(Event.repository_id == repository_id)
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def commit(self) -> None:
        await self.session.commit()
