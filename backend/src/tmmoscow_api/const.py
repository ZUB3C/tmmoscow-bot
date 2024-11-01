import re

from .enums import DistanceType

HOST = "www.tmmoscow.ru"
SCHEME = "http"
BASE_URL = f"{SCHEME}://{HOST}"
INDEX_PATH = "/index.php"
INDEX_URL = f"{BASE_URL}{INDEX_PATH}"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    )
}

HTML_ENCODING = "cp1251"

ID_TO_DISTANCE_TYPE = {distance_type.id: distance_type for distance_type in DistanceType}

EVENT_DATES_REGEX = (
    r"(?P<start_day>\d{1,2})\s*"
    r"(?:(?P<start_month>[а-яА-Я]+)?)\s*"
    r"(?:[-–]\s*"
    r"(?P<end_day>\d{1,2})?\s*"
    r"(?P<end_month>[а-яА-Я]+)?)\s*"
    r"(?P<end_year>\d{4})\s*"
    r"(?:г?)(?:\.?)(?:од)?(?:а?)"
)
EVENT_DATES_PATTERN = re.compile(EVENT_DATES_REGEX, flags=re.IGNORECASE)
EVENT_DATES_LOCATION_NODE_REGEX = (
    rf"(?:\<br\>)?\s*(?P<event_dates_location_str>{EVENT_DATES_REGEX}.*?)(?=\<br\>)"
)
EVENT_DATES_LOCATION_NODE_PATTERN = re.compile(
    EVENT_DATES_LOCATION_NODE_REGEX, flags=re.IGNORECASE
)
MONTH_NAME_TO_NUMBER = {
    "января": 1,
    "февраля": 2,
    "марта": 3,
    "апреля": 4,
    "мая": 5,
    "июня": 6,
    "июля": 7,
    "августа": 8,
    "сентября": 9,
    "октября": 10,
    "ноября": 11,
    "декабря": 12,
}
VIEWS_PATTERN = re.compile(r"Прочита(на|но|ли):\s*(?P<views>\d*)", flags=re.IGNORECASE)
AUTHOR_PATTERN = re.compile(r"Автор:\s*(?P<author>[а-яА-Яa-zA-Z]+)", flags=re.IGNORECASE)
CONTENT_LINE_PATTERN = re.compile(r"\s*-\s*.*$")
CONTENT_LINE_DASH_PATTERN = re.compile(r"\s*-\s*")
