from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import NamedTuple


class NewsType(NamedTuple):
    id: int
    title: str


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


@dataclass(frozen=True)
class Competition:
    title: str
    id: int
    date: str
    location: str
    views: int | None
    updated_at: datetime | str | None
    logo_url: str | None

    @property
    def url(self) -> str:
        return f"{INDEX_URL}?go=News&in=view&id={self.id}"


@dataclass(frozen=True)
class ContentLine:
    html: str
    comment: str | None


@dataclass(frozen=True)
class ContentBlock:
    title: str
    lines: list[ContentLine]


@dataclass(frozen=True)
class CompetitionInfo(Competition):
    author: str | None
    content_blocks: list[ContentBlock]


BASE_URL = "http://www.tmmoscow.ru"
INDEX_PATH = "/index.php"
INDEX_URL = f"{BASE_URL}{INDEX_PATH}"
