import logging
from typing import Final

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram_i18n import I18nContext
from tmmoscow_api import TmMoscowAPI
from tmmoscow_api.types import CompetitionSummary

from ..const import MAX_COMPETITIONS_LIST_LEN
from ..database import DBUser, UoW
from ..keyboards.inline import get_competitions_kb, get_distance_types_kb, get_go_back_kb
from ..utils import get_distance_type

router: Final[Router] = Router(name=__name__)
logger: Final[logging.Logger] = logging.getLogger(name=__name__)


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext, i18n: I18nContext, user: DBUser) -> None:
    await state.clear()
    await message.answer(i18n.messages.start(name=user.mention))


async def get_competitions(
    tmmoscow: TmMoscowAPI,
    user: DBUser,
) -> list[CompetitionSummary]:
    user_distance_type = get_distance_type(user.distance_type_id)
    competitions = await tmmoscow.get_recent_competitions(distance_type=user_distance_type)
    if len(competitions) > MAX_COMPETITIONS_LIST_LEN:
        competitions = competitions[:MAX_COMPETITIONS_LIST_LEN]
    return competitions


@router.message(Command("competitions"))
async def cmd_competitions(
    message: Message, i18n: I18nContext, tmmoscow: TmMoscowAPI, user: DBUser
) -> None:
    user_distance_type = get_distance_type(user.distance_type_id)
    competitions = await get_competitions(tmmoscow=tmmoscow, user=user)
    await message.answer(
        i18n.messages.choose_competition(distance_type_title=user_distance_type.title.lower()),
        reply_markup=get_competitions_kb(competitions),
    )


@router.message(Command("distance_type"))
async def cmd_distance_type(message: Message, i18n: I18nContext, user: DBUser) -> None:
    await message.answer(
        text=i18n.messages.choose_distance_type(),
        reply_markup=get_distance_types_kb(current_distance_type_id=user.distance_type_id),
    )


@router.callback_query(F.data.startswith("competition:"))
async def handle_competition(
    callback: CallbackQuery, i18n: I18nContext, tmmoscow: TmMoscowAPI
) -> None:
    _, competition_id_str = callback.data.split(":")
    competition_id = int(competition_id_str)
    if callback.message is not None:
        info = await tmmoscow.get_competition_data(id=competition_id)
        await callback.message.edit_text(
            text=i18n.messages.competition_info(
                url=info.url,
                title=info.title,
                date=info.event_dates,
                location=info.location,
                views=str(info.views),
            ),
            disable_web_page_preview=True,
            reply_markup=get_go_back_kb(menu="choose_competition"),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("distance_type:"))
async def handle_distance_type(
    callback: CallbackQuery, i18n: I18nContext, uow: UoW, user: DBUser
) -> None:
    _, previous_distance_type_id_str, new_distance_type_id_str = callback.data.split(":")
    previous_distance_type_id, new_distance_type_id = (
        int(previous_distance_type_id_str),
        int(new_distance_type_id_str),
    )
    user.distance_type_id = new_distance_type_id
    await uow.commit(user)
    logger.info(
        "Changed distance_type_id from %d to %d for user %d",
        previous_distance_type_id,
        new_distance_type_id,
        user.id,
    )
    if previous_distance_type_id != new_distance_type_id:
        await callback.message.edit_text(
            text=i18n.messages.choosed_distance_type(
                new_distance_type_title=get_distance_type(new_distance_type_id).title
            ),
            reply_markup=get_go_back_kb(menu="choose_distance_type"),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("open_menu:"))
async def handle_open_menu(
    callback: CallbackQuery, i18n: I18nContext, user: DBUser, tmmoscow: TmMoscowAPI
) -> None:
    _, menu = callback.data.split(":")
    match menu:
        case "choose_distance_type":
            await callback.message.edit_text(
                text=i18n.messages.choose_distance_type(),
                reply_markup=get_distance_types_kb(current_distance_type_id=user.distance_type_id),
            )
        case "choose_competition":
            competitions = await get_competitions(tmmoscow=tmmoscow, user=user)
            await callback.message.edit_text(
                i18n.messages.choose_competition(
                    distance_type_title=get_distance_type(user.distance_type_id).title.lower()
                ),
                reply_markup=get_competitions_kb(competitions),
            )
        case _:
            pass
    await callback.answer()


@router.callback_query(F.data.startswith("close_menu"))
async def handle_close_menu(callback: CallbackQuery) -> None:
    if callback.message is not None:
        await callback.message.delete()
