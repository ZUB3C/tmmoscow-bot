from datetime import datetime

from .consts import TIMEZONE


def get_current_time() -> datetime:
    return datetime.now(tz=TIMEZONE)
