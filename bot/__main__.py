import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram_i18n import I18nMiddleware
from aiogram_i18n.cores import FluentRuntimeCore
from loguru import logger

from .database import create_pool
from .enums import Locale
from .handlers import admin, user
from .middlewares import DBSessionMiddleware, UserManager, UserMiddleware
from .settings import Settings
from .utils.loggers import setup_logger


async def main() -> None:
    setup_logger()
    settings = Settings()

    bot = Bot(
        token=settings.bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher(storage=MemoryStorage())

    admin.router.message.filter(F.from_user.id.in_(settings.admin_chat_id))

    dp.include_routers(user.router, admin.router)

    pool = dp["session_pool"] = create_pool(dsn=settings.build_dsn(), enable_logging=False)
    i18n_middleware = dp["i18n_middleware"] = I18nMiddleware(
        core=FluentRuntimeCore(
            path="translations/{locale}",
            raise_key_error=False,
        ),
        manager=UserManager(),
        default_locale=Locale.DEFAULT,
    )

    dp.update.outer_middleware(DBSessionMiddleware(session_pool=pool))
    dp.update.outer_middleware(UserMiddleware())
    i18n_middleware.setup(dispatcher=dp)

    await bot.delete_webhook(drop_pending_updates=settings.drop_pending_updates)
    if settings.drop_pending_updates:
        logger.info("Updates skipped successfully")

    logger.info("Bot started")
    await dp.start_polling(bot, settings=settings)


if __name__ == "__main__":
    asyncio.run(main())
