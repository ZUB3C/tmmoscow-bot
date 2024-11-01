import asyncio
import contextlib
import hashlib
import logging
import re
import typing
from collections.abc import Generator
from datetime import datetime
from pathlib import Path
from types import TracebackType
from typing import Any, Final, Literal, cast, overload
from urllib.parse import urljoin

import aiohttp
from selectolax.parser import HTMLParser, Node
from yarl import URL

from .const import (
    AUTHOR_PATTERN,
    BASE_URL,
    CONTENT_LINE_DASH_PATTERN,
    CONTENT_LINE_PATTERN,
    DEFAULT_HEADERS,
    EVENT_DATES_LOCATION_NODE_PATTERN,
    EVENT_DATES_PATTERN,
    HOST,
    HTML_ENCODING,
    ID_TO_DISTANCE_TYPE,
    INDEX_PATH,
    MONTH_NAME_TO_NUMBER,
    VIEWS_PATTERN,
)
from .enums import DistanceType, ParsedContentLineType, _ParseCompetitionFrom
from .types import (
    CompetitionDetail,
    CompetitionDetailFiles,
    CompetitionSummary,
    ContentBlock,
    ContentLine,
    ContentSubtitle,
    File,
)
from .utils import get_body_html, get_html_text, get_url_parameter_value, node_with_text

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
    ) -> list[CompetitionSummary]:
        """Get data on 30 (or less) latest competitions with offset"""
        params = {"go": "News", "in": "cat", "id": distance_type.id, "page": offset}
        html = await self._get(INDEX_PATH, params=params)
        parser = HTMLParser(html)

        news_node = parser.css_first(
            "body > table:nth-child(4) > tbody > tr > td:nth-child(3) > table:nth-child(8) > tbody"
        )
        if news_node is None:
            return []  # offset is too big
        competitions: list[CompetitionSummary] = []
        tr_nodes = news_node.css("tr")
        for i in range(0, len(tr_nodes), 5):
            nodes_chunk = tr_nodes[i : i + 5]
            competition = self._parse_competition_summary(
                tr_nodes=nodes_chunk,
                distance_type=distance_type,
                parse_competition_from=_ParseCompetitionFrom.CATEGORY_PAGE,
            )
            competitions.append(competition)
        return competitions

    @overload
    async def get_competition_data(
        self, id: int, *, parse_created_at: bool = False, with_files: Literal[False] = False
    ) -> CompetitionDetail: ...

    @overload
    async def get_competition_data(
        self, id: int, *, parse_created_at: bool = False, with_files: Literal[True] = False
    ) -> CompetitionDetailFiles: ...

    async def get_competition_data(
        self, id: int, *, parse_created_at: bool = False, with_files: bool = False
    ) -> CompetitionDetail | CompetitionDetailFiles:
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
                parser_created_at.css_first("body > div > b")
                .text(strip=True)
                .split(" | ", maxsplit=1)
            )
            created_at = datetime.strptime(created_at_str, "%d.%m.%Y %H:%M")
        parser = HTMLParser(html)

        content_node = parser.css_first(
            "body > table:nth-child(4) > tbody > tr > td:nth-child(3) > table:nth-child(7) > tbody"
        )
        tr_nodes = content_node.css("tr")
        competition_summary = self._parse_competition_summary(
            content_node=content_node,
            parse_competition_from=_ParseCompetitionFrom.COMPETITION_PAGE,
            competition_id=id,
        )
        content_blocks = []
        for node in tr_nodes[5:]:
            content_node = node.css_first("td")
            content_blocks = self._parse_content(content_html=cast(str, content_node.html))
            if content_blocks:
                break

        try:
            author = tr_nodes[7].css_first("td").text(strip=True, deep=False)
        except IndexError:
            # Legacy article formatting support
            for tr_tag in reversed(tr_nodes):
                text = tr_tag.text(strip=True)
                match = AUTHOR_PATTERN.match(text)
                if match:
                    author = match.group("author")
                    break
            else:
                author = None

        competition = CompetitionDetail(
            title=competition_summary.title,
            id=competition_summary.id,
            event_dates=competition_summary.event_dates,
            event_begins_at=competition_summary.event_begins_at,
            event_ends_at=competition_summary.event_ends_at,
            location=competition_summary.location,
            views=competition_summary.views,
            updated_at=competition_summary.updated_at,
            logo_url=competition_summary.logo_url,
            author=author,
            content_blocks=content_blocks,
            created_at=created_at,
        )
        if not with_files:
            return competition

        file_nodes = list(self._file_nodes_generator(competition.content_blocks))
        file_urls = [URL(file_node.attributes["href"]) for file_node in file_nodes]
        # Allow only pdf files (reference: https://tmmoscow.ru/news/publish_info.pdf)
        file_urls = [
            url for url in file_urls if url.host == HOST and Path(url.path).suffix == ".pdf"
        ]
        file_urls = list(dict.fromkeys(file_urls))  # make file urls list unique
        async with asyncio.TaskGroup() as tg:
            tasks = [tg.create_task(self._get(url=url, raw=True)) for url in file_urls]
        file_contents = [task.result() for task in tasks]
        files: list[File] = []
        for url, content in zip(file_urls, file_contents, strict=False):
            filename = Path(url.path).name
            if content is None:
                files.append(File(filename=filename, content=None, url=str(url), sha256_hash=""))
                continue
            m = hashlib.sha256()
            m.update(content)
            files.append(
                File(filename=filename, content=content, url=str(url), sha256_hash=m.hexdigest())
            )

        return CompetitionDetailFiles(competition=competition, files=files)

    @staticmethod
    @overload
    def _parse_competition_summary(
        parse_competition_from: Literal[_ParseCompetitionFrom.CATEGORY_PAGE],
        distance_type: DistanceType | None = None,
        content_node: Node | None = None,
        tr_nodes: list[Node] | None = None,
        clear_title: bool = True,
        *,
        competition_id: None = None,
    ) -> CompetitionSummary: ...

    @staticmethod
    @overload
    def _parse_competition_summary(
        parse_competition_from: Literal[_ParseCompetitionFrom.COMPETITION_PAGE],
        distance_type: None = None,
        content_node: Node | None = None,
        tr_nodes: list[Node] | None = None,
        clear_title: bool = True,
        *,
        competition_id: int,
    ) -> CompetitionSummary: ...

    @staticmethod
    def _parse_competition_summary(
        parse_competition_from: _ParseCompetitionFrom,
        distance_type: DistanceType | None = None,
        content_node: Node | None = None,
        tr_nodes: list[Node] | None = None,
        clear_title: bool = True,
        *,
        competition_id: int | None = None,
    ) -> CompetitionSummary:
        if tr_nodes is None and content_node is None:
            raise ValueError
        if tr_nodes is None:
            if content_node is None:
                raise ValueError
            tr_nodes = content_node.css("tr")
        match parse_competition_from:
            case _ParseCompetitionFrom.CATEGORY_PAGE:
                if distance_type is None:
                    raise ValueError("Give category argument of type NewsCategory")
                title_node, metadata_node = tr_nodes[:2]
                title = title_node.text(strip=True)
            case _ParseCompetitionFrom.COMPETITION_PAGE:
                title_node, metadata_node = tr_nodes[0], tr_nodes[3]

                title = title_node.css_first("td > font").text(strip=True)

                category_url = cast(str, title_node.css_first("td > a").attributes.get("href", ""))
                category_id = int(get_url_parameter_value(url=category_url, parameter="id"))
                distance_type = ID_TO_DISTANCE_TYPE.get(category_id)
                if distance_type is None:
                    raise RuntimeError(f"Couldn't convert {category_id=} to DistanceType")
            case _ as unreachable:
                typing.assert_never(unreachable)
        if clear_title:
            title = TmMoscowAPI._clear_title(title, distance_type)
        else:
            title = title.removesuffix(".")

        metadata_text = metadata_node.text(strip=True, separator="\n")

        metadata_lines: list[str] = list(
            filter(lambda html: node_with_text(html=html), metadata_text.split("\n"))
        )
        updated_at = None
        if len(metadata_lines) >= 2:
            updated_at_str = metadata_lines[1]
            updated_at_parser = HTMLParser(html=updated_at_str)
            updated_at_node = updated_at_parser.css_first("b")
            if updated_at_node:
                updated_at_str = updated_at_node.text(strip=True).lower()
            for updated_at_format in "обновлено %d.%m.%Y", "обновлено: %d.%m.%Y":
                with contextlib.suppress(ValueError):
                    updated_at = datetime.strptime(updated_at_str, updated_at_format)

        match parse_competition_from:
            case _ParseCompetitionFrom.CATEGORY_PAGE:
                competition_url = cast(
                    str, title_node.css_first("td > a").attributes.get("href", "")
                )
                id_value = int(get_url_parameter_value(url=competition_url, parameter="id"))
            case _ParseCompetitionFrom.COMPETITION_PAGE:
                if not isinstance(competition_id, int):
                    raise ValueError(f"competition_id should be int, not {competition_id}")
                id_value = competition_id
            case _ as unreachable:
                typing.assert_never(unreachable)

        logo_url_node = metadata_node.css_first("a > img")
        logo_url = logo_url_node.attributes.get("src") if logo_url_node else None
        if logo_url and BASE_URL not in logo_url:
            logo_url = urljoin(BASE_URL, logo_url)
        for link_node in metadata_node.css("a"):
            link_node.decompose()

        event_dates, location, event_begins_at, event_ends_at = None, None, None, None
        for i, node in enumerate(tr_nodes):
            match = re.search(EVENT_DATES_LOCATION_NODE_PATTERN, cast(str, node.html))
            if match:
                new_node_html = re.sub(EVENT_DATES_LOCATION_NODE_PATTERN, "", cast(str, node.html))
                new_node = HTMLParser(
                    html=f"<table><tbody><tr><td>{new_node_html}</td></tr><table><tbody>"
                )
                tr_nodes[i] = cast(Node, new_node)
                event_dates_location_str = match.group("event_dates_location_str")
                event_dates, location = list(
                    map(str.strip, event_dates_location_str.split(",", maxsplit=1))
                )
                event_begins_at, event_ends_at = TmMoscowAPI._parse_date_range(
                    event_dates_location_str
                )
                break

        for node in tr_nodes[2:]:
            text = node.text(strip=True)
            match = VIEWS_PATTERN.match(text)
            if match:
                views = int(match.group("views"))
                break
        else:
            views = None

        return CompetitionSummary(
            id=id_value,
            title=title,
            event_dates=event_dates,
            event_begins_at=event_begins_at,
            event_ends_at=event_ends_at,
            location=location,
            views=views,
            updated_at=updated_at,
            logo_url=logo_url,
        )

    @staticmethod
    def _parse_content(content_html: str) -> list[ContentBlock]:
        content_lines_html: list[str] = list(
            map(
                str.strip,
                filter(
                    lambda html: node_with_text(html=html),
                    content_html.replace("\n", "<br>").split("<br>"),
                ),
            )
        )
        if not content_lines_html:
            return []
        parsed_content_line_types = [TmMoscowAPI._detect_line_type(i) for i in content_lines_html]
        content_lines_data: list[ContentBlock] = []

        current_title = ""
        current_lines: list[ContentLine | ContentSubtitle] = []

        for i, parsed_content_line_type in enumerate(parsed_content_line_types):
            current_type = parsed_content_line_type
            next_type = (
                parsed_content_line_types[i + 1]
                if i < len(parsed_content_line_types) - 1
                else None
            )

            current_parser = HTMLParser(html=content_lines_html[i])
            # Remove all attributes except href
            for node in current_parser.tags("a"):
                for attr in node.attributes:
                    if attr != "href":
                        del node.attrs[attr]
                    else:
                        node.attrs["href"] = urljoin(BASE_URL, node.attributes["href"])  # pyright: ignore[reportIndexIssue]
            current_html = get_body_html(current_parser)
            current_html = re.sub(CONTENT_LINE_DASH_PATTERN, "", current_html, count=1)

            match current_type:
                case ParsedContentLineType.TITLE:
                    if current_title or current_lines:
                        content_lines_data.append(
                            ContentBlock(title=current_title, lines=current_lines)
                        )
                        current_lines = []

                    current_title = get_html_text(current_html)

                case ParsedContentLineType.SUBTITLE:
                    current_lines.append(ContentSubtitle(html=current_html))

                case ParsedContentLineType.FULL_LINE_OR_LINE_BEGINNING:
                    line_parser = HTMLParser(html=current_html)
                    comment_node = line_parser.css_first("font")
                    if comment_node:
                        if comment_node.text(strip=True) != "":
                            comment = comment_node.text(strip=True)
                        else:
                            comment = None
                        comment_node.decompose()
                    else:
                        comment = None

                    combined_html = get_body_html(line_parser)
                    # Combining all subsequent lines of type LINE_CONTINUATION_OR_TEXT
                    while next_type is ParsedContentLineType.LINE_CONTINUATION_OR_TEXT:
                        i += 1
                        combined_html += "\n" + content_lines_html[i]
                        next_type = (
                            parsed_content_line_types[i + 1]
                            if i < len(parsed_content_line_types) - 1
                            else None
                        )

                    current_lines.append(ContentLine(html=combined_html, comment=comment))

                case (
                    ParsedContentLineType.LINE_CONTINUATION_OR_TEXT
                    | ParsedContentLineType.TITLE_UNDERLINE
                ):
                    continue
                case _ as unreachable:
                    typing.assert_never(unreachable)

        if current_title or current_lines:
            content_lines_data.append(ContentBlock(title=current_title, lines=current_lines))

        return content_lines_data

    @staticmethod
    def _detect_line_type(line_html: str) -> ParsedContentLineType:
        parser = HTMLParser(html=line_html)
        text = parser.text(strip=True)
        if parser.css_first("b > font"):
            if set(text) == {"="}:
                return ParsedContentLineType.TITLE_UNDERLINE
            if all(i.isupper() for i in text if i.islower()):
                return ParsedContentLineType.TITLE
        if parser.css_first("b"):
            if not CONTENT_LINE_PATTERN.match(text) and "href" not in text:
                return ParsedContentLineType.SUBTITLE
            return ParsedContentLineType.FULL_LINE_OR_LINE_BEGINNING
        if CONTENT_LINE_PATTERN.match(text):
            return ParsedContentLineType.FULL_LINE_OR_LINE_BEGINNING
        return ParsedContentLineType.LINE_CONTINUATION_OR_TEXT

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
                    r"Дистанции\s*пешеходные\s*в\s*закрытых\s*помещениях",
                    r"Дистанции\s*пешеходные",
                ]
            case DistanceType.WALKING:
                title_suffixes = [
                    r"Дистанции\s*пешеходные",
                    r"Дистанции\s*-\s*пешеходные",
                    r"Дистанции\s*пешеходные",
                ]
            case (
                DistanceType.SKI
                | DistanceType.MOUNTAIN
                | DistanceType.SPELEO
                | DistanceType.AQUATIC
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
                title_suffixes = TmMoscowAPI._get_suffixes_distances_on_vehicles("Авто", "авто")
            case DistanceType.EQUESTRIAN:
                title_suffixes = TmMoscowAPI._get_suffixes_distances_on_vehicles(
                    r"Конные\s*(дистанции)?", "кони|конные"
                )
            case DistanceType.SAILING:
                title_suffixes = [r"Дистанции\s*парусные", r"Дистанция\s*-?\s*парусная"]
            case DistanceType.NORDIC_WALKING:
                title_suffixes = [r"Северная\s*ходьба"]
            case _ as unreachable:
                typing.assert_never(unreachable)

        suffixes_pattern = "|".join([rf"{suffix}\.?" for suffix in title_suffixes])
        title_pattern = rf"\s*({suffixes_pattern})(?=.*)?"
        return re.sub(
            title_pattern,
            "",
            title,
            flags=re.IGNORECASE,
        ).removesuffix(".")

    @staticmethod
    def _parse_date_range(event_dates: str) -> tuple[datetime, datetime] | tuple[None, None]:
        match = EVENT_DATES_PATTERN.search(event_dates)
        if not match:
            return None, None

        start_day = int(match.group("start_day"))
        end_day = match.group("end_day") or start_day
        start_month = match.group("start_month")
        end_month = match.group("end_month")
        year = int(match.group("end_year"))

        if not start_month:
            start_month = end_month
        if not end_month:
            end_month = start_month
        start_month_number = MONTH_NAME_TO_NUMBER[start_month.lower()]
        end_month_number = MONTH_NAME_TO_NUMBER[end_month.lower()]

        event_begins_at = datetime(year=year, month=start_month_number, day=start_day)
        event_ends_at = datetime(year=year, month=end_month_number, day=int(end_day))

        return event_begins_at, event_ends_at

    @staticmethod
    def _file_nodes_generator(content_blocks: list[ContentBlock]) -> Generator[Node]:
        for content_block in content_blocks:
            for content_line in content_block.lines:
                if isinstance(content_line, ContentLine):
                    file_nodes = [
                        i for i in HTMLParser(content_line.html).css("a") if "href" in i.attributes
                    ]
                    yield from file_nodes

    @overload
    async def _get(
        self, path: str = "", url: str | URL = "", raw: Literal[False] = False, **kwargs: Any
    ) -> str: ...

    @overload
    async def _get(
        self, path: str = "", url: str | URL = "", raw: Literal[True] = False, **kwargs: Any
    ) -> bytes | None: ...

    async def _get(
        self, path: str = "", url: str | URL = "", raw: bool = False, **kwargs: Any
    ) -> str | bytes | None:
        """Get html or file content from full `url` or `path` relative to base url."""
        url = url or urljoin(BASE_URL, path)
        async with self._session.request(method="GET", url=url, **kwargs) as response:
            logger.debug("Sent GET request: %d: %s", response.status, str(response.url))
            if not response.ok:
                if raw:
                    return None
                response.raise_for_status()
            if raw:
                return await response.content.read()
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
