from typing import Final

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram_i18n import I18nContext

from ..database import DBUser

router: Final[Router] = Router(name=__name__)


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext, i18n: I18nContext, user: DBUser) -> None:
    await state.clear()
    await message.answer(i18n.messages.start(name=user.mention))
