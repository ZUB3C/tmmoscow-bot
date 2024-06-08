from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from aiogram import BaseMiddleware

from ..database import DBUser
from ..utils.loggers import database as logger

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from aiogram.types import TelegramObject, User
    from aiogram_i18n import I18nMiddleware

    from ..database import Repository, UoW


class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any | None:
        aiogram_user: User | None = data.get("event_from_user")
        if aiogram_user is None or aiogram_user.is_bot:
            # Prevents the bot itself from being added to the database
            # when accepting chat_join_request and receiving chat_member.
            return await handler(event, data)

        repository: Repository = data["repository"]
        user: DBUser | None = await repository.users.get(user_id=aiogram_user.id)
        if user is None:
            i18n: I18nMiddleware = data["i18n_middleware"]
            uow: UoW = data["uow"]
            user = DBUser.from_aiogram(
                user=aiogram_user,
                locale=(
                    aiogram_user.language_code
                    if aiogram_user.language_code in i18n.core.available_locales
                    else cast(str, i18n.core.default_locale)
                ),
            )
            await uow.commit(user)
            logger.info("New user in database: {}", user)
        else:
            user.name = aiogram_user.full_name
        data["user"] = user
        return await handler(event, data)
