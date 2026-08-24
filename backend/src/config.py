"""
GitHub Discord Bot — Configuration.

Static settings (read once at startup from env):
  - DATABASE_URL  (required — must always be in .env)
  - APP_ENV, LOG_LEVEL, PORT

Dynamic settings (Discord/GitHub) are stored in DB via src.services.config_service
and can be changed at runtime through the Admin API without restarting Docker.

The legacy `Config` singleton is kept for backward-compat code that reads
APP_ENV / LOG_LEVEL / PORT / DATABASE_URL.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Database (always from env — cannot be changed at runtime) ─────────────
    database_url: str = "postgresql+asyncpg://user:pass@localhost/github_bot"

    # ── Application ──────────────────────────────────────────────────────────
    app_env: str = "production"
    log_level: str = "INFO"
    port: int = 8000

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


# Blueprint pattern: singleton for static config only
Config = Settings()
