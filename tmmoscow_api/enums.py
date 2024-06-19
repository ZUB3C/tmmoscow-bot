from enum import Enum, auto


class NewsCategory(Enum):
    # Types of distance
    INDOORS = (1, "В закрытых помещениях")
    WALKING = (2, "Пешеходные")
    SKI = (3, "Лыжные")
    MOUNTAIN = (4, "Горные")
    SPELEO = (5, "Спелео")
    COMBINED_SRW = (6, "Комбинированные (ПСР)")
    AQUATIC = (10, "Водные")
    BICYCLE = (11, "Велосипедные")
    AUTO_MOTO = (12, "Авто-мото")
    EQUESTRIAN = (13, "Конные")
    SAILING = (14, "Парусные")
    NORDIC_WALKING = (15, "Северная ходьба")

    # Locations
    IN_MOSCOW = (8, "В Москве")
    IN_RUSSIA = (9, "В России")

    # Other
    MISCELLANEOUS = (7, "Разное")

    def __init__(self, id: int, title: str) -> None:
        self.id = id
        self.title = title

    @property
    def url(self) -> str:
        return f"http://www.tmmoscow.ru/index.php?go=News&in=cat&id={self.id}"


class _ParseCompetitionFrom(Enum):
    NEWS = auto()
    COMPETITION = auto()
