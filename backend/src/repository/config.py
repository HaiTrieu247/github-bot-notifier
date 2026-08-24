"""Repository layer — AppConfig key-value CRUD (blueprint pattern)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.config import AppConfig

logger = logging.getLogger(__name__)

VN_TZ = timezone(timedelta(hours=7))


class ConfigRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, key: str) -> Optional[str]:
        result = await self.session.execute(
            select(AppConfig).where(AppConfig.key == key)
        )
        row = result.scalar_one_or_none()
        return row.value if row else None

    async def get_all(self) -> dict[str, str]:
        result = await self.session.execute(select(AppConfig))
        return {row.key: row.value for row in result.scalars().all()}

    async def set(self, key: str, value: str) -> None:
        result = await self.session.execute(
            select(AppConfig).where(AppConfig.key == key)
        )
        row = result.scalar_one_or_none()
        now = datetime.now(VN_TZ).replace(tzinfo=None)
        if row:
            row.value = value
            row.updated_at = now
        else:
            self.session.add(AppConfig(key=key, value=value, updated_at=now))
        await self.session.flush()

    async def set_many(self, mapping: dict[str, str]) -> None:
        for key, value in mapping.items():
            await self.set(key, value)

    async def delete(self, key: str) -> None:
        result = await self.session.execute(
            select(AppConfig).where(AppConfig.key == key)
        )
        row = result.scalar_one_or_none()
        if row:
            await self.session.delete(row)
            await self.session.flush()
