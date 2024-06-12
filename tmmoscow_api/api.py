import logging
import re
from datetime import datetime
from enum import Enum
from types import TracebackType
from typing import Any, Final
from urllib.parse import parse_qs, urljoin, urlparse

import aiohttp
from selectolax.parser import HTMLParser, Node
from tmmoscow_api.types import (
    BASE_URL,
    INDEX_PATH,
    Competition,
    CompetitionInfo,
    ContentBlock,
    ContentLine,
    NewsCategory,
)

logger: Final[logging.Logger] = logging.getLogger(name=__name__)


class _CompetitionParseType(Enum):
    FROM_NEWS = 0
    FROM_COMPETITION = 1


class TmMoscowAPI:
    def __init__(self, timeout: int = 5, max_requests_per_second: int = 10) -> None:
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(timeout),
            connector=aiohttp.TCPConnector(limit=max_requests_per_second),
        )

    async def close(self) -> None:
        if not self._session.closed:
            await self._session.close()

    async def get_recent_competitions(self, category: NewsCategory) -> list[Competition]:
        """Get 30 recent competitions"""
        if category in (NewsCategory.IN_MOSCOW, NewsCategory.IN_RUSSIA):
            raise ValueError("NewsCategory.IN_MOSCOW, NewsCategory.IN_RUSSIA aren't supported yet")

        params = {"go": "News", "in": "cat", "id": category.value.id}
        html = await self._get(INDEX_PATH, params=params)
        parser = HTMLParser(html)

        news_tag = parser.css_first(
            "body > table:nth-child(4) > tbody > tr > td:nth-child(3) > table:nth-child(8) > tbody"
        )
        competitions: list[Competition] = []
        tr_tags = news_tag.css("tr")
        for i in range(0, len(tr_tags), 5):
            tags_chunk = tr_tags[i : i + 5]
            competition = self._parse_competition(tags_chunk, _CompetitionParseType.FROM_NEWS)
            competitions.append(competition)
        return competitions

    async def get_competition_data(self, id: int) -> CompetitionInfo:
        params = {"go": "News", "in": "view", "id": id}
        html = await self._get(INDEX_PATH, params=params)
        parser = HTMLParser(html)

        data_tag = parser.css_first(
            "body > table:nth-child(4) > tbody > tr > td:nth-child(3) > table:nth-child(7) > tbody"
        )
        tr_tags = data_tag.css("tr")
        competition = self._parse_competition(
            tr_tags[:9], competition_parse_type=_CompetitionParseType.FROM_COMPETITION
        )

        content_tag = tr_tags[5].css_first("td")
        content_blocks: list[ContentBlock] = []

        content_lines = list(
            filter(
                lambda html: HTMLParser(html).text(strip=True) != "",
                content_tag.html.split("<br>"),
            )
        )

        # current_content_block: ContentBlock | None = None
        current_title = ""
        current_content_lines: list[ContentLine] = []
        for line_html in content_lines:
            line_parser = HTMLParser(line_html)

            b_tag = line_parser.css_first("b")
            if b_tag:
                if set(line_parser.text(strip=True)) == {"="}:
                    continue
                text = b_tag.text(strip=True)
                if all(
                    char.isupper() or char.isspace()
                    for char in text
                    if char.isalpha() or char.isspace()
                ):
                    if current_title:
                        content_blocks.append(
                            ContentBlock(title=current_title, lines=current_content_lines)
                        )
                        current_content_lines = []
                    current_title = text
            else:
                if current_title:
                    current_content_lines.append(ContentLine(html=line_html))
        content_blocks.append(ContentBlock(title=current_title, lines=current_content_lines))

        author = tr_tags[7].css_first("td").text(strip=True, deep=False)

        return CompetitionInfo(
            title=competition.title,
            id=competition.id,
            date=competition.date,
            location=competition.location,
            views=competition.views,
            updated_at=competition.updated_at,
            logo_url=competition.logo_url,
            author=author,
            content_blocks=content_blocks,
        )

    @staticmethod
    def _parse_competition(
        tr_tags: list[Node], competition_parse_type: _CompetitionParseType
    ) -> Competition:
        if not (len(tr_tags) >= 3 and all(len(tag.css("tr")) == 1 for tag in tr_tags)):
            raise ValueError("All tags should be <tr>")
        if competition_parse_type is _CompetitionParseType.FROM_NEWS:
            title_tag, metadata_tag, views_tag = tr_tags[:3]
            title = title_tag.text(strip=True)
        elif competition_parse_type is _CompetitionParseType.FROM_COMPETITION:
            title_tag = tr_tags[0]
            metadata_tag = tr_tags[3]
            views_tag = tr_tags[8]
            title = title_tag.css_first("td > font").text(strip=True)
        else:
            raise ValueError("competition_parse_type should be _CompetitionParseType type")

        updated_at_tags = metadata_tag.css("b")
        if len(updated_at_tags) >= 1:
            updated_at_tag = None
            for tag in updated_at_tags:
                if tag.text(strip=True):
                    updated_at_tag = tag
                    break
            date_str = (
                updated_at_tag.text(strip=True, separator=" ")
                .lower()
                .removeprefix("обновлено ")
                .split(" ")[0]
                .strip()
            )
            try:
                updated_at = datetime.strptime(  # noqa: DTZ007
                    date_str, "%d.%m.%Y"
                )
            except ValueError:
                updated_at = date_str
            updated_at_tags[1 if len(updated_at_tags) >= 2 else 0].decompose()
        else:
            updated_at = None

        if competition_parse_type is _CompetitionParseType.FROM_NEWS:
            competition_url_tag = title_tag
        elif competition_parse_type is _CompetitionParseType.FROM_COMPETITION:
            competition_url_tag = metadata_tag
        else:
            raise ValueError("competition_parse_type should be _CompetitionParseType type")

        competition_url = competition_url_tag.css_first("td > a").attributes.get("href")
        parsed_url = urlparse(competition_url)
        query_params = parse_qs(parsed_url.query)
        id_value = int(query_params.get("id", [None])[0])

        logo_url_tag = metadata_tag.css_first("a > img")
        logo_url = logo_url_tag.attributes.get("src") if logo_url_tag else None
        for link_tag in metadata_tag.css("a"):
            link_tag.decompose()
        date, location = map(str.strip, metadata_tag.text(strip=True).split(",", maxsplit=1))

        views = int("".join(re.findall(r"\d", views_tag.text(strip=True)))) if views_tag else None

        return Competition(
            title=title,
            id=id_value,
            date=date,
            location=location,
            views=views,
            updated_at=updated_at,
            logo_url=logo_url,
        )

    async def _get(self, path: str = "", url: str = "", **kwargs: Any) -> str:
        """Get html from full `url` or `path` relative to base url."""
        url = url or urljoin(BASE_URL, path)
        async with self._session.request(method="GET", url=url, **kwargs) as response:
            logging.debug("Sent GET request: %d: %s", response.status, str(response.url))
            response.raise_for_status()
            return await response.text()

    async def __aenter__(self) -> "TmMoscowAPI":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.close()
