from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram_i18n import L
from aiogram_i18n.types import InlineKeyboardButton
from tmmoscow_api.enums import DistanceType
from tmmoscow_api.types import CompetitionSummary


def get_distance_types_kb(current_distance_type_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        *[
            InlineKeyboardButton(
                text=distance_type.title
                if distance_type.id != current_distance_type_id
                else f"✅ {distance_type.title}",
                callback_data=f"distance_type:{current_distance_type_id}:{distance_type.id}",
            )
            for distance_type in DistanceType
        ],
        width=2,
    )
    return builder.as_markup()


def get_competitions_kb(competitions: list[CompetitionSummary]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        *[
            InlineKeyboardButton(text=c.title, callback_data=f"competition:{c.id}")
            for c in competitions
        ],
        InlineKeyboardButton(text=L.buttons.close_menu(), callback_data="close_menu"),
        width=1,
    )
    return builder.as_markup()


def get_go_back_kb(menu: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=L.buttons.go_back(), callback_data=f"open_menu:{menu}"),
    )
    return builder.as_markup()
