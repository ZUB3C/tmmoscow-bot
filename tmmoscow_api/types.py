from dataclasses import dataclass
from datetime import datetime
from typing import NamedTuple


class NewsType(NamedTuple):
    id: int
    title: str


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
