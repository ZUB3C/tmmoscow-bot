from __future__ import annotations

from typing import TYPE_CHECKING

from .base import BaseRepository
from .users import UsersRepository

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class Repository(BaseRepository):
    """
    The general repository.
    """

    users: UsersRepository

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session)
        self.users = UsersRepository(session=session)
