from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from backend.enums import NodeLocation, SubscriptionPlan


def main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Конфиг", callback_data="menu:config")
    builder.button(text="Профиль", callback_data="menu:profile")
    builder.button(text="Продлить", callback_data="menu:renew")
    builder.button(text="Поддержка", callback_data="menu:support")
    builder.adjust(1, 2, 1)
    return builder.as_markup()


def config_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Скопировать конфиг", callback_data="config:copy")
    builder.button(text="QR код", callback_data="config:qr")
    builder.button(text="Сменить локацию", callback_data="config:switch")
    builder.button(text="Сбросить конфиг", callback_data="config:reset")
    builder.adjust(1)
    return builder.as_markup()


def support_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Мои тикеты", callback_data="support:list")
    builder.button(text="Создать обращение", callback_data="support:create")
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


def renewal_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="1 месяц - 150 RUB", callback_data=f"renew:plan:{SubscriptionPlan.MONTH_1.value}")
    builder.button(text="3 месяца - 400 RUB", callback_data=f"renew:plan:{SubscriptionPlan.MONTH_3.value}")
    builder.adjust(1)
    return builder.as_markup()
