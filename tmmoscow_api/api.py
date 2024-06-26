import asyncio
import logging
import re
import typing
from datetime import datetime
from types import TracebackType
from typing import Any, Final, cast
from urllib.parse import urljoin

import aiohttp
from selectolax.parser import HTMLParser, Node

from .const import BASE_URL, DEFAULT_HEADERS, HTML_ENCODING, ID_TO_DISTANCE_TYPE, INDEX_PATH
from .enums import DistanceType, _ParseCompetitionFrom
from .types import (
    Competition,
    CompetitionInfo,
    ContentBlock,
    ContentLine,
    ContentSubtitle,
)
from .utils import get_body_html, get_url_parameter_value

logger: Final[logging.Logger] = logging.getLogger(name=__name__)


class TmMoscowAPI:
    def __init__(self, timeout: int = 5, max_requests_per_second: int = 10) -> None:
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(timeout),
            connector=aiohttp.TCPConnector(limit=max_requests_per_second),
            headers=DEFAULT_HEADERS,
        )

    async def get_recent_competitions(
        self, distance_type: DistanceType, *, offset: int = 0
    ) -> list[Competition]:
        """Get data on 30 (or less) latest competitions with offset"""

        params = {"go": "News", "in": "cat", "id": distance_type.id, "page": offset}
        html = await self._get(INDEX_PATH, params=params)
        parser = HTMLParser(html)

        news_tag = parser.css_first(
            "body > table:nth-child(4) > tbody > tr > td:nth-child(3) > table:nth-child(8) > tbody"
        )
        if news_tag is None:
            return []  # offset is too big
        competitions: list[Competition] = []
        tr_tags = news_tag.css("tr")
        for i in range(0, len(tr_tags), 5):
            tags_chunk = tr_tags[i : i + 5]
            competition = self._parse_competition(
                tr_tags=tags_chunk,
                distance_type=distance_type,
                parse_competition_from=_ParseCompetitionFrom.CATEGORY_PAGE,
            )
            competitions.append(competition)
        return competitions

    async def get_competition_data(
        self, id: int, parse_created_at: bool = False
    ) -> CompetitionInfo:
        """Get detailed information about competition"""
        params = {"go": "News", "in": "view", "id": id}
        if not parse_created_at:
            html = await self._get(INDEX_PATH, params=params)
            created_at = None
        else:
            params_created_at = {"go": "News", "file": "print", "id": id}
            html, created_at_html = await asyncio.gather(
                asyncio.create_task(self._get(INDEX_PATH, params=params)),
                asyncio.create_task(self._get(INDEX_PATH, params=params_created_at)),
            )
            parser_created_at = HTMLParser(created_at_html)
            _, created_at_str = (
                parser_created_at.css_first("body > div > b").text(strip=True).split(" | ", 1)
            )
            created_at = datetime.strptime(created_at_str, "%d.%m.%Y %H:%M")  # noqa: DTZ007
        parser = HTMLParser(html)

        data_tag = parser.css_first(
            "body > table:nth-child(4) > tbody > tr > td:nth-child(3) > table:nth-child(7) > tbody"
        )
        tr_tags = data_tag.css("tr")
        competition = self._parse_competition(
            tr_tags=tr_tags[:9],
            parse_competition_from=_ParseCompetitionFrom.COMPETITION_PAGE,
            competition_id=id,
        )

        content_tag = tr_tags[5].css_first("td")
        content_blocks: list[ContentBlock] = []

        content_lines = list(
            map(
                str.strip,
                filter(
                    lambda html: HTMLParser(html).text(strip=True) != "",
                    cast(str, content_tag.html).split("<br>"),
                ),
            )
        )

        current_title = ""
        current_content_lines: list[ContentLine | ContentSubtitle] = []
        for line_html in content_lines:
            line_parser = HTMLParser(line_html)

            title_tag = line_parser.css_first("b > font")
            if (
                title_tag
                and title_tag.text(strip=True)
                and title_tag.attributes.get("color") == "green"
            ):
                if set(line_parser.text(strip=True)) == {"="}:
                    continue
                text = title_tag.text(strip=True)
                if all(char.isupper() for char in text if char.isalpha()):
                    if current_title:
                        content_blocks.append(
                            ContentBlock(title=current_title, lines=current_content_lines)
                        )
                        current_content_lines = []
                    current_title = text
            else:
                comment_tag = line_parser.css_first("font")
                if comment_tag:
                    if comment_tag.text(strip=True) != "":
                        comment = comment_tag.text(strip=True)
                    else:
                        comment = None
                    comment_tag.decompose()
                else:
                    comment = None
                # Remove all attributes except href
                for node in line_parser.tags("a"):
                    for attr in node.attributes:
                        if attr != "href":
                            del node.attrs[attr]  # type: ignore[attr-defined]
                        else:
                            node.attrs["href"] = urljoin(BASE_URL, node.attributes["href"])  # type: ignore[index]
                # Check if line is a subtitle or content line
                if typing.TYPE_CHECKING:
                    content_line: ContentLine | ContentSubtitle
                content_line_pattern = r"\s*-\s.*"
                body_html = get_body_html(line_parser)
                if re.match(content_line_pattern, body_html):
                    body_html = re.sub(r"^\s*-\s", "", body_html)
                    content_line = ContentLine(html=body_html, comment=comment)
                else:
                    subtitle_tag = line_parser.css_first("b")
                    if subtitle_tag and subtitle_tag.text(strip=True):
                        content_line = ContentSubtitle(
                            html=line_parser.body.child.child.html,  # type: ignore[union-attr,arg-type]
                            comment=comment,
                        )
                    else:
                        content_line = ContentLine(html=body_html, comment=comment)
                current_content_lines.append(content_line)
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
            created_at=created_at,
        )

    @staticmethod
    def _parse_competition(
        tr_tags: list[Node],
        parse_competition_from: _ParseCompetitionFrom,
        distance_type: DistanceType | None = None,
        clear_title: bool = True,
        *,
        competition_id: int | None = None,
    ) -> Competition:
        if not (len(tr_tags) >= 3 and all(len(tag.css("tr")) == 1 for tag in tr_tags)):
            raise ValueError("All tags should be <tr>")
        if not isinstance(parse_competition_from, _ParseCompetitionFrom):
            raise ValueError("competition_parse_type should be _CompetitionParseType type")
        if parse_competition_from is _ParseCompetitionFrom.CATEGORY_PAGE:
            if distance_type is None:
                raise ValueError("Give category argument of type NewsCategory")
            title_tag, metadata_tag, views_tag = tr_tags[:3]
            title = title_tag.text(strip=True)
        elif parse_competition_from is _ParseCompetitionFrom.COMPETITION_PAGE:
            title_tag = tr_tags[0]
            metadata_tag = tr_tags[3]
            views_tag = tr_tags[8]
            title = title_tag.css_first("td > font").text(strip=True)

            category_url = cast(str, title_tag.css_first("td > a").attributes.get("href", ""))
            category_id = int(get_url_parameter_value(url=category_url, parameter="id"))
            distance_type = ID_TO_DISTANCE_TYPE.get(category_id)
            if distance_type is None:
                raise RuntimeError(f"Couldn't convert {category_id=} to DistanceType")
        if clear_title:
            title = TmMoscowAPI._clear_title(title, distance_type)
        else:
            title = title.removesuffix(".")

        updated_at_tags = metadata_tag.css("b")
        if len(updated_at_tags) >= 1:
            updated_at_tag = None
            for tag in updated_at_tags:
                if "обновлено" in tag.text(strip=True):
                    updated_at_tag = tag
                    break
            if updated_at_tag is None:
                updated_at = None
            else:
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
                    updated_at = date_str  # type: ignore[assignment]
                updated_at_tags[1 if len(updated_at_tags) >= 2 else 0].decompose()
        else:
            updated_at = None

        if parse_competition_from is _ParseCompetitionFrom.CATEGORY_PAGE:
            competition_url = cast(str, title_tag.css_first("td > a").attributes.get("href", ""))
            id_value = int(get_url_parameter_value(url=competition_url, parameter="id"))
        elif parse_competition_from is _ParseCompetitionFrom.COMPETITION_PAGE:
            if not isinstance(competition_id, int):
                raise ValueError(f"competition_id should be int, not {competition_id}")
            id_value = competition_id

        logo_url_tag = metadata_tag.css_first("a > img")
        logo_url = logo_url_tag.attributes.get("src") if logo_url_tag else None
        for link_tag in metadata_tag.css("a"):
            link_tag.decompose()

        metadata_parts = metadata_tag.text(strip=True).split(",", maxsplit=1)
        if len(metadata_parts) == 2:
            date, location = map(str.strip, metadata_parts)
        elif len(metadata_parts) == 1:
            date, location = metadata_parts[0], metadata_parts[0]
        else:
            raise RuntimeError(f"metadata_parts len is {len(metadata_parts)}, not 2 or 1")

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

    @staticmethod
    def _get_suffixes_distances_on_vehicles(word: str, in_parentheses: str) -> list[str]:
        """Generate title suffixes for distances on vehicles"""
        return [
            r"Дистанции\s*на\s*средствах\s*передвижения",
            rf"Дистанции\s*-?\s*на\s*средствах\s*передвижения\s*\({in_parentheses}\)",
            rf"Дистанции\s*на\s*средствах\s*передвижения.\s*{word}",
        ]

    @staticmethod
    def _clear_title(title: str, distance_type: DistanceType) -> str:
        if typing.TYPE_CHECKING:
            title_suffixes: list[str]
        match distance_type:
            case DistanceType.INDOORS:
                title_suffixes = [
                    "Дистанции пешеходные",
                    "Дистанции пешеходные в закрытых помещения",
                ]
            case DistanceType.WALKING:
                title_suffixes = [
                    r"Дистанции\s*пешеходные",
                    r"Дистанции\s?-\s?пешеходные",
                    r"Дистанции\s?пешеходные",
                ]
            case (
                DistanceType.SKI,
                DistanceType.MOUNTAIN,
                DistanceType.SPELEO,
                DistanceType.AQUATIC,
            ):
                title_suffixes = [rf"Дистанции\s*{distance_type.title.lower()}"]
            case DistanceType.COMBINED_SRW:
                title_suffixes = [
                    r"Дистанции\s*комбинированные",
                    r"Дистанция\s*-\s*комбинированная",
                ]
            case DistanceType.BICYCLE:
                title_suffixes = [
                    *TmMoscowAPI._get_suffixes_distances_on_vehicles("Вело(сипед)?", "вело"),
                    "Дистанции\\s*велосипедные",
                ]
            case DistanceType.AUTO_MOTO:
                title_suffixes = TmMoscowAPI._get_suffixes_distances_on_vehicles(
                    "Авто", "авто"
                )
            case DistanceType.EQUESTRIAN:
                title_suffixes = TmMoscowAPI._get_suffixes_distances_on_vehicles(
                    r"Конные\s*(дистанции)?", "кони|конные"
                )
            case DistanceType.SAILING:
                title_suffixes = [r"Дистанции\s*парусные", r"Дистанция\s*-?\s*парусная"]
            case DistanceType.NORDIC_WALKING:
                title_suffixes = [r"Северная\s*ходьба"]
            case _:
                raise ValueError

        suffixes_pattern = "|".join([rf"{suffix}\.?" for suffix in title_suffixes])
        title_pattern = rf"\s*({suffixes_pattern})(?=.*)?"
        return re.sub(
            title_pattern,
            "",
            title,
            flags=re.IGNORECASE,
        ).removesuffix(".")

    async def _get(self, path: str = "", url: str = "", **kwargs: Any) -> str:
        """Get html from full `url` or `path` relative to base url."""
        url = url or urljoin(BASE_URL, path)
        async with self._session.request(method="GET", url=url, **kwargs) as response:
            logger.debug("Sent GET request: %d: %s", response.status, str(response.url))
            response.raise_for_status()
            return await response.text(encoding=HTML_ENCODING)

    async def close(self) -> None:
        if not self._session.closed:
            await self._session.close()

    async def __aenter__(self) -> "TmMoscowAPI":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.close()
