from enum import Enum, auto

from tmmoscow_api.types import NewsType


class NewsCategory(Enum):
    # Types of distance
    INDOORS = NewsType(id=1, title="В закрытых помещениях")
    WALKING = NewsType(id=2, title="Пешеходные")
    SKI = NewsType(id=3, title="Лыжные")
    MOUNTAIN = NewsType(id=4, title="Горные")
    SPELEO = NewsType(id=5, title="Спелео")
    COMBINED_SRW = NewsType(id=6, title="Комбинированные (ПСР)")
    MISCELLANEOUS = NewsType(id=7, title="Разное")
    AQUATIC = NewsType(id=10, title="Водные")
    BICYCLE = NewsType(id=11, title="Велосипедные")
    AUTO_MOTO = NewsType(id=12, title="Авто-мото")
    EQUESTRIAN = NewsType(id=13, title="Конные")
    SAILING = NewsType(id=14, title="Парусные")
    NORDIC_WALKING = NewsType(id=15, title="Северная ходьба")

    # Locations
    IN_MOSCOW = NewsType(id=8, title="В Москве")
    IN_RUSSIA = NewsType(id=9, title="В России")


class _CompetitionParseType(Enum):
    FROM_NEWS = auto()
    FROM_COMPETITION = auto()
