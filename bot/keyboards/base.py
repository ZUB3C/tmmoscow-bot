from typing import cast

from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram_i18n import LazyProxy
from aiogram_i18n.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def common_keyboard(
    *texts: str | LazyProxy,
    is_persistent: bool = False,
    resize_keyboard: bool = True,
    one_time_keyboard: bool = False,
    input_field_placeholder: str | None = None,
    selective: bool = False,
    row_width: int = 2,
) -> ReplyKeyboardMarkup:
    """
    Common reply keyboards build helper.
    """
    builder: ReplyKeyboardBuilder = ReplyKeyboardBuilder()
    builder.row(*[KeyboardButton(text=text) for text in texts], width=row_width)
    return cast(
        ReplyKeyboardMarkup,
        builder.as_markup(
            is_persistent=is_persistent,
            resize_keyboard=resize_keyboard,
            one_time_keyboard=one_time_keyboard,
            input_field_placeholder=input_field_placeholder,
            selective=selective,
        ),
    )
