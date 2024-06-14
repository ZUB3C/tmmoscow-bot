from datetime import datetime
from typing import cast
from urllib.parse import parse_qs, urlparse

from selectolax.parser import HTMLParser

from .consts import TIMEZONE


def get_current_time() -> datetime:
    return datetime.now(tz=TIMEZONE)


def get_url_parameter_value(url: str, parameter: str) -> str:
    parsed_url = urlparse(url)
    query_params: dict[str, list[str]] = parse_qs(str(parsed_url.query))
    return query_params.get(parameter)[0]


def get_body_html(parser: HTMLParser) -> str:
    # Remove "<body>" and "</body>"
    return cast(str, parser.body.html)[6:-7]  # type: ignore[union-attr]
