from enum import Enum, auto


class _BaseCategory(Enum):
    def __init__(self, id: int, title: str) -> None:
        self.id = id
        self.title = title

    @property
    def url(self) -> str:
        return f"http://www.tmmoscow.ru/index.php?go=News&in=cat&id={self.id}"


class DistanceType(_BaseCategory):
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


class NewsCategory(_BaseCategory):
    # Locations
    IN_MOSCOW = (8, "В Москве")
    IN_RUSSIA = (9, "В России")

    # Other
    MISCELLANEOUS = (7, "Разное")


class _ParseCompetitionFrom(Enum):
    CATEGORY_PAGE = auto()
    COMPETITION_PAGE = auto()


class ParsedContentLineType(Enum):
    TITLE = auto()
    SUBTITLE = auto()
    FULL_LINE_OR_LINE_BEGINNING = auto()
    LINE_CONTINUATION_OR_TEXT = auto()
    TITLE_UNDERLINE = auto()  # "=====..." line
