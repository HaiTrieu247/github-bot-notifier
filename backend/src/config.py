"""GitHub Discord Bot — Configuration (Blueprint pattern: singleton Config object)."""

from __future__ import annotations

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Discord ──────────────────────────────────────────────────────────────
    discord_token: str = ""
    discord_guild_id: int = 0
    discord_default_channel_id: int = 0

    # "owner/repo:channel_id,owner/repo2:channel_id2"
    discord_repo_channel_map: str = ""

    # ── GitHub ───────────────────────────────────────────────────────────────
    github_token: str = ""
    github_webhook_secret: str = ""

    # "Kens0107/homestay-backend,Kens0107/frontend"
    github_repositories: str = ""

    # ── Database ─────────────────────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://github_bot:password@postgres:5432/github_bot"
    postgres_db: str = "github_bot"
    postgres_user: str = "github_bot"
    postgres_password: str = ""

    # ── Application ──────────────────────────────────────────────────────────
    app_env: str = "production"
    log_level: str = "INFO"
    port: int = 8000

    # ── Computed helpers ─────────────────────────────────────────────────────

    @property
    def monitored_repositories(self) -> list[str]:
        """Return list of 'owner/repo' strings."""
        if not self.github_repositories:
            return []
        return [r.strip() for r in self.github_repositories.split(",") if r.strip()]

    @property
    def repo_channel_map(self) -> dict[str, int]:
        """Return mapping of 'owner/repo' → discord channel_id."""
        mapping: dict[str, int] = {}
        if not self.discord_repo_channel_map:
            return mapping
        for entry in self.discord_repo_channel_map.split(","):
            entry = entry.strip()
            if ":" not in entry:
                continue
            repo, channel_id_str = entry.rsplit(":", 1)
            try:
                mapping[repo.strip()] = int(channel_id_str.strip())
            except ValueError:
                pass
        return mapping

    def get_channel_id(self, full_repo_name: str) -> Optional[int]:
        """Get Discord channel ID for a given repo, falling back to default."""
        mapping = self.repo_channel_map
        if full_repo_name in mapping:
            return mapping[full_repo_name]
        if self.discord_default_channel_id:
            return self.discord_default_channel_id
        return None

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


# Blueprint pattern: singleton Config object
Config = Settings()
