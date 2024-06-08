from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository:
    _session: AsyncSession

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
