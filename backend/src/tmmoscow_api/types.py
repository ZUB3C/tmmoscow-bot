from dataclasses import dataclass
from datetime import datetime
from typing import NamedTuple

from tmmoscow_api.const import INDEX_URL


@dataclass(frozen=True)
class CompetitionSummary:
    id: int
    title: str
    event_dates: str | None
    event_begins_at: datetime | None
    event_ends_at: datetime | None
    location: str | None
    views: int | None
    updated_at: datetime | None
    logo_url: str | None

    @property
    def url(self) -> str:
        return f"{INDEX_URL}?go=News&in=view&id={self.id}"


@dataclass(frozen=True)
class ContentLine:
    html: str
    comment: str | None


@dataclass(frozen=True)
class ContentSubtitle:
    html: str


@dataclass(frozen=True)
class ContentBlock:
    title: str
    lines: list[ContentLine | ContentSubtitle]


@dataclass(frozen=True)
class CompetitionDetail(CompetitionSummary):
    author: str | None
    content_blocks: list[ContentBlock]
    created_at: (
        datetime | None
    )  # None only if parse_created_at=False, otherwise it always will be parsed


@dataclass(frozen=True)
class File:
    filename: str
    content: bytes | None
    url: str
    sha256_hash: str


class CompetitionDetailFiles(NamedTuple):
    competition: CompetitionDetail
    files: list[File]
