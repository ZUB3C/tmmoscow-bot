from dataclasses import dataclass
from datetime import datetime

from tmmoscow_api.consts import INDEX_URL


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
class BaseLine:
    html: str
    comment: str | None


@dataclass(frozen=True)
class ContentLine(BaseLine): ...


@dataclass(frozen=True)
class ContentSubtitle(BaseLine): ...


@dataclass(frozen=True)
class ContentBlock:
    title: str
    lines: list[ContentLine | ContentSubtitle]


@dataclass(frozen=True)
class CompetitionInfo(Competition):
    author: str | None
    content_blocks: list[ContentBlock]
