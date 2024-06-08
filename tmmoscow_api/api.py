import logging
from types import TracebackType
from typing import Any, Final
from urllib.parse import urljoin

import aiohttp

logger: Final[logging.Logger] = logging.getLogger(name=__name__)


class TmMoscowAPI:
    BASE_URL = "http://www.tmmoscow.ru"

    def __init__(self, timeout: int = 5, max_requests_per_second: int = 10) -> None:
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(timeout),
            connector=aiohttp.TCPConnector(limit=max_requests_per_second),
        )

    async def close(self) -> None:
        if not self._session.closed:
            await self._session.close()

    async def _get(self, path: str = "", url: str = "", **kwargs: Any) -> str:
        """Get html from full `url` or `path` relative to base url."""
        url = url or urljoin(self.BASE_URL, path)
        async with self._session.request(method="GET", url=url, **kwargs) as response:
            logging.debug("Sent GET request: %d: %s", response.status, response.url)
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
