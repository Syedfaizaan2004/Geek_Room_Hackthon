"""
db/session.py — Async SQLAlchemy engine and session factory.

Designed for:
  - SQLite (development) via aiosqlite
  - PostgreSQL (production/Render) via asyncpg — just swap DATABASE_URL

Usage (FastAPI dependency injection):
    async def my_route(db: AsyncSession = Depends(get_db)):
        ...
"""

import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    AsyncEngine,
)

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# ------------------------------------------------------------------
# Resolve async-compatible DATABASE_URL
# ------------------------------------------------------------------
# The .env stores the URL without an async driver prefix (e.g. "sqlite:///...")
# SQLAlchemy async engine requires the driver to be explicit:
#   sqlite:///...         → sqlite+aiosqlite:///...
#   postgresql:///...     → postgresql+asyncpg:///...
def _make_async_url(url: str) -> str:
    """Patch a plain DB URL to its async-driver equivalent."""
    if url.startswith("sqlite:///") and "+aiosqlite" not in url:
        return url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
    if url.startswith("postgresql://") and "+asyncpg" not in url:
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://") and "+asyncpg" not in url:
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


_async_db_url = _make_async_url(settings.DATABASE_URL)

# ------------------------------------------------------------------
# Engine
# ------------------------------------------------------------------
# connect_args only needed for SQLite (to enable WAL mode for concurrency)
_connect_args: dict = {}
if _async_db_url.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}

engine: AsyncEngine = create_async_engine(
    url=_async_db_url,
    echo=settings.is_debug,          # Log all SQL statements in debug mode
    future=True,                     # SQLAlchemy 2.0 mode
    connect_args=_connect_args,
)

# ------------------------------------------------------------------
# Session factory
# ------------------------------------------------------------------
AsyncSessionFactory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,    # Objects stay usable after commit
    autoflush=False,
    autocommit=False,
)


# ------------------------------------------------------------------
# FastAPI dependency — yields a transactional session per request
# ------------------------------------------------------------------
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Async generator that yields an AsyncSession.
    Automatically commits on success and rolls back on exception.

    Use as:
        db: AsyncSession = Depends(get_db)
    """
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ------------------------------------------------------------------
# Database initialisation — called once at application startup
# ------------------------------------------------------------------
async def init_db() -> None:
    """
    Create all tables defined by models that have imported Base.
    Each phase adds model imports here to register them with SQLAlchemy metadata.

    Phase 0: No models — confirmed connectivity only.
    Phase 1: User model registered → creates 'users' table.
    """
    from db.base import Base  # noqa: F401

    # ── Phase 1 + 2: register User and UserPreferences models ────────────────
    from memory.models import User, UserPreferences  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database initialised successfully", extra={"url": settings.DATABASE_URL})


async def close_db() -> None:
    """Dispose the engine pool — called on application shutdown."""
    await engine.dispose()
    logger.info("Database engine disposed")
