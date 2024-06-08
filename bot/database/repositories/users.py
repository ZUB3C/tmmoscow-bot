from typing import cast

from sqlalchemy import select

from ..models import DBUser
from .base import BaseRepository


class UsersRepository(BaseRepository):
    async def get(self, user_id: int) -> DBUser | None:
        return cast(
            DBUser | None,
            await self._session.scalar(select(DBUser).where(DBUser.id == user_id)),
        )
