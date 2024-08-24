from typing import cast

from selectolax.parser import HTMLParser, Node
from yarl import URL


def get_url_parameter_value(url: str, parameter: str) -> str:
    return URL(url).query.get(parameter, "")


def get_body_html(parser: HTMLParser) -> str:
    # Remove "<body>" and "</body>"
    return cast(str, parser.body.html)[6:-7]  # type: ignore[union-attr]


def node_with_text(html: str | Node, strip: bool = True) -> bool:
    node: HTMLParser | Node = HTMLParser(html=html) if isinstance(html, str) else html
    return bool(node.text(strip=strip))
