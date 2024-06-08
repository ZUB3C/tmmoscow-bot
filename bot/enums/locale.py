from __future__ import annotations

from enum import StrEnum, auto


class Locale(StrEnum):
    EN = auto()
    RU = auto()

    DEFAULT = RU

    @classmethod
    def resolve(cls, locale: str | None = None) -> Locale:
        if locale is None or locale not in cls.__members__:
            return Locale.DEFAULT
        return Locale(locale)
