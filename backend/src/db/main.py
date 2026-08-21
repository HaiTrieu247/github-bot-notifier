"""Database engine, session factory, init_db — Blueprint pattern (no Alembic)."""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel, text

from src.config import Config

logger = logging.getLogger(__name__)

engine = create_async_engine(
    Config.database_url,
    echo=Config.app_env == "development",
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields a DB session and commits on success."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Create all tables (safe to run multiple times) and run manual migrations.
    Blueprint pattern: no Alembic, use SQLModel.metadata.create_all + SQL IF NOT EXISTS.
    """
    # Import models so SQLModel registers their metadata
    import src.models  # noqa: F401

    async with engine.begin() as conn:
        logger.info("Creating tables (if not exist)…")
        await conn.run_sync(SQLModel.metadata.create_all)
        await _run_migrations(conn)

    logger.info("Database initialised")


async def _run_migrations(conn) -> None:
    """
    Manual, idempotent schema migrations.
    Use IF NOT EXISTS / IF EXISTS guards — safe to run on every startup.
    Add new migrations at the bottom.
    """
    await conn.execute(text("""
        DO $$
        BEGIN
            -- Add unique constraint on workflow_runs(repository_id, github_run_id)
            -- (table created by create_all; constraint may not exist on old DBs)
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'uq_workflow_run_repo_run'
            ) THEN
                BEGIN
                    ALTER TABLE workflow_runs
                        ADD CONSTRAINT uq_workflow_run_repo_run
                        UNIQUE (repository_id, github_run_id);
                EXCEPTION WHEN duplicate_table THEN NULL;
                END;
            END IF;

            -- Add unique constraint on deployments(repository_id, github_deployment_id)
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'uq_deployment_repo_dep'
            ) THEN
                BEGIN
                    ALTER TABLE deployments
                        ADD CONSTRAINT uq_deployment_repo_dep
                        UNIQUE (repository_id, github_deployment_id);
                EXCEPTION WHEN duplicate_table THEN NULL;
                END;
            END IF;
        END $$;
    """))
    logger.debug("Migrations applied")
