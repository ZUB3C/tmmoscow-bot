import logging
from datetime import datetime
from types import TracebackType
from typing import Any, Final
from urllib.parse import parse_qs, urljoin, urlparse

import aiohttp
from selectolax.parser import HTMLParser
from tmmoscow_api.types import BASE_URL, INDEX_PATH, Competition, NewsCategory

logger: Final[logging.Logger] = logging.getLogger(name=__name__)


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
        if category in (NewsCategory.IN_MOSCOW, NewsCategory.IN_RUSSIA):
            raise ValueError("NewsCategory.IN_MOSCOW, NewsCategory.IN_RUSSIA aren't supported yet")
        params = {"go": "News", "in": "cat", "id": category.value.id}
        html = await self._get(INDEX_PATH, params=params)
        parser = HTMLParser(html)
        news_tag = parser.css(
            "body > table:nth-child(4) > tbody > tr > td:nth-child(3) > table:nth-child(8) > tbody"
        )[0]
        competitions: list[Competition] = []
        tr_tags = news_tag.css("tr")
        for i in range(0, len(tr_tags), 5):
            chunk = tr_tags[i : i + 5]
            title_tag = chunk[0]
            metadata_tag = chunk[1]
            views_tag = chunk[2]

            title = title_tag.text(strip=True)

            updated_at_tags = metadata_tag.css("b")
            if len(updated_at_tags) >= 2:
                updated_at_tag = None
                for tag in updated_at_tags:
                    if tag.text(strip=True):
                        updated_at_tag = tag
                        break
                date_str = (
                    updated_at_tag
                    .text(strip=True, separator=" ")
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
                updated_at_tags[1].decompose()
            else:
                updated_at = None
            logo_url_tag = metadata_tag.css_first("a > img")
            logo_url = logo_url_tag.attributes.get("src") if logo_url_tag else None
            for link_tag in metadata_tag.css("a"):
                link_tag.decompose()
            date, location = map(str.strip, metadata_tag.text(strip=True).split(",", maxsplit=1))

            competition_url = title_tag.css_first("td > a").attributes.get("href")
            parsed_url = urlparse(competition_url)
            query_params = parse_qs(parsed_url.query)
            id_value = int(query_params.get("id", [None])[0])

            views = (
                int(views_tag.text(strip=True).removeprefix("Прочитана:")) if views_tag else None
            )

            event = Competition(
                title=title,
                id=id_value,
                date=date,
                location=location,
                views=views,
                updated_at=updated_at,
                logo_url=logo_url,
            )
            competitions.append(event)
        return competitions

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
        await self._session.close()
