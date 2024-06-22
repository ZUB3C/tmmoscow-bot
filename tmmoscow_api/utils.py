from datetime import datetime
from typing import cast

from selectolax.parser import HTMLParser
from yarl import URL

from .const import TIMEZONE


def get_current_time() -> datetime:
    return datetime.now(tz=TIMEZONE)


def get_url_parameter_value(url: str, parameter: str) -> str:
    return URL(url).query.get(parameter, "")


def get_body_html(parser: HTMLParser) -> str:
    # Remove "<body>" and "</body>"
    return cast(str, parser.body.html)[6:-7]  # type: ignore[union-attr]
