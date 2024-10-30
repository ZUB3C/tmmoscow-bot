from typing import cast, overload

from selectolax.parser import HTMLParser, Node
from yarl import URL


def get_url_parameter_value(url: str, parameter: str) -> str:
    return URL(url).query.get(parameter, "")


def get_body_html(parser: HTMLParser) -> str:
    # Remove "<body>" and "</body>"
    return cast(str, parser.body.html)[6:-7]  # type: ignore[union-attr]


def get_html_text(html: str, strip: bool = True) -> str:
    return HTMLParser(html=html).text(strip=strip)


@overload
def node_with_text(*, html: str, node: None = None, strip: bool = True) -> bool: ...


@overload
def node_with_text(*, node: Node | HTMLParser, html: None = None, strip: bool = True) -> bool: ...


def node_with_text(
    *, html: str | None = None, node: Node | HTMLParser | None = None, strip: bool = True
) -> bool:
    if (html is None) and (node is None):
        raise ValueError("Either html or node must be provided")
    if html:
        node = HTMLParser(html=html)

    return bool(node.text(strip=strip)) if node else False
