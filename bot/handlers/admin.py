from typing import Final

from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import BotCommand, BotCommandScopeDefault, Message
from aiogram.utils.markdown import hcode
from aiogram_i18n import I18nContext, L
from loguru import logger

from ..database import DBUser

router: Final[Router] = Router(name=__name__)

AVAILABLE_COMMANDS: Final[tuple[str, ...]] = (
    "person",
    "subject",
    "start",
    "settoken",
    "redl",
    "cancel",
)


@router.message(Command("setcommands"))
async def cmd_set_commands(message: Message, i18n: I18nContext, bot: Bot, user: DBUser) -> None:
    available_locales = i18n.core.available_locales
    for locale in available_locales:
        with i18n.use_locale(locale):
            commands = [
                BotCommand(command=f"/{command}", description=L(f"commands-{command}").data)
                for command in AVAILABLE_COMMANDS
            ]

        # None as language code will set commands for all unspecified locales
        for language_code in [locale, None] if locale == i18n.core.default_locale else [locale]:
            await bot.set_my_commands(
                commands=commands, language_code=language_code, scope=BotCommandScopeDefault()
            )

    await message.answer(
        i18n.messages.commands_set(
            count=len(available_locales),
            locales=", ".join([hcode(locale) for locale in available_locales]),
        ),
    )
    logger.info("{} - Set bot commands for next locales: {}", user, ", ".join(available_locales))
