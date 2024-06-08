from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

if TYPE_CHECKING:
    from sqlalchemy import URL


def create_pool(dsn: str | URL, enable_logging: bool = False) -> async_sessionmaker[AsyncSession]:
    engine: AsyncEngine = create_async_engine(url=dsn, echo=enable_logging)
    return async_sessionmaker(engine, expire_on_commit=False)
