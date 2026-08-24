"""SQLModel table: AppConfig — key-value store for dynamic runtime configuration."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

from sqlmodel import Field, SQLModel

VN_TZ = timezone(timedelta(hours=7))


def _now_vn() -> datetime:
    return datetime.now(VN_TZ).replace(tzinfo=None)


class AppConfig(SQLModel, table=True):
    __tablename__ = "app_config"

    key: str = Field(primary_key=True, max_length=128, nullable=False)
    value: str = Field(default="", sa_column_kwargs={"nullable": False})
    updated_at: datetime = Field(default_factory=_now_vn)

    def __repr__(self) -> str:
        return f"<AppConfig key={self.key}>"
