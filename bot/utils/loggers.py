from loguru import logger

database = logger.bind(name="bot.database")


def setup_logger(level: str = "INFO") -> None:
    for name in ("aiogram.middlewares", "aiogram.event", "aiohttp.access"):
        logger.bind(name=name).level("WARNING")

    logger.add(
        sink="logs/{time:%Y-%m-%d}.log",
        format="{time} {level} {message}",
        level=level,
        rotation="12:00",
        compression="tar.gz",
    )
