from zoneinfo import ZoneInfo

from .enums import DistanceType

TIMEZONE = ZoneInfo("Europe/Moscow")
BASE_URL = "http://www.tmmoscow.ru"
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
