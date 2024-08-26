from tmmoscow_api.const import ID_TO_DISTANCE_TYPE
from tmmoscow_api.enums import DistanceType

from bot.const import DEFAULT_DISTANCE_TYPE


def get_distance_type(id: int) -> DistanceType:
    return ID_TO_DISTANCE_TYPE.get(id, DEFAULT_DISTANCE_TYPE)
