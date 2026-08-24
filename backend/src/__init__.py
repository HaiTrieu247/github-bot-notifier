"""
GitHub Discord Bot — FastAPI application factory.
Blueprint pattern: src/__init__.py is the app entry point.
"""

from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from src.config import Config

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, Config.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Starting GitHub Discord Bot (env=%s)", Config.app_env)

    # Init DB — create tables + run migrations
    from src.db.main import init_db
    await init_db()

    # Seed dynamic config from environment variables (first-run only)
    from src.services.config_service import seed_from_env
    await seed_from_env()

    # Start Discord bot in background thread
    from src.bot.client import start_bot
    await start_bot()

    yield

    logger.info("Shutting down GitHub Discord Bot")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="GitHub Discord Bot",
    description="Backend service connecting GitHub webhooks to Discord notifications.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if not Config.is_production else None,
    redoc_url="/redoc" if not Config.is_production else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
from src.routes.webhook import router as webhook_router
from src.routes.health import router as health_router
from src.routes.repositories import router as repositories_router
from src.routes.config import router as config_router

app.include_router(health_router)
app.include_router(webhook_router)
app.include_router(repositories_router)
app.include_router(config_router)

# ── Static Files (Admin Dashboard) ────────────────────────────────────────────
_static_dir = Path(__file__).parent / "static"
_static_dir.mkdir(exist_ok=True)
app.mount("/admin", StaticFiles(directory=str(_static_dir), html=True), name="admin")


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    return {"service": "github-discord-bot", "status": "running"}
