"""SQLAlchemy async engine and session helpers."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from news_scraper.settings import Settings, get_settings

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine(settings: Settings | None = None) -> AsyncEngine:
    global _engine, _session_factory
    if _engine is None:
        cfg = settings or get_settings()
        _engine = create_async_engine(cfg.database_url, pool_pre_ping=True)
        _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine


def get_session_factory(
    settings: Settings | None = None,
) -> async_sessionmaker[AsyncSession]:
    get_engine(settings)
    assert _session_factory is not None
    return _session_factory


@asynccontextmanager
async def get_async_session(
    settings: Settings | None = None,
) -> AsyncIterator[AsyncSession]:
    factory = get_session_factory(settings)
    async with factory() as session:
        yield session


async def init_db(settings: Settings | None = None) -> None:
    """Create tables if they do not exist (dev convenience). Prefer Alembic in prod."""
    from news_scraper.db.models import Base

    engine = get_engine(settings)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def reset_engine() -> None:
    """Reset cached engine (useful in tests)."""
    global _engine, _session_factory
    _engine = None
    _session_factory = None
