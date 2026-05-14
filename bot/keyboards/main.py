from aiogram.types import (
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from backend.enums import NodeLocation


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Конфиг")],
            [KeyboardButton(text="Профиль"), KeyboardButton(text="Продлить")],
            [KeyboardButton(text="Поддержка")],
        ],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Выберите действие",
    )


def config_actions_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Сменить локацию", callback_data="config:switch")
    builder.button(text="Сбросить конфиг", callback_data="config:reset")
    builder.adjust(1)
    return builder.as_markup()


def locations_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for location in NodeLocation:
        builder.button(
            text=location.value.capitalize(),
            callback_data=f"config:set_location:{location.value}",
        )
    builder.adjust(2, 2)
    return builder.as_markup()
