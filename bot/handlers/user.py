from html import escape

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from backend.enums import NodeLocation
from backend.runtime import get_container
from bot.keyboards.main import config_actions_keyboard, locations_keyboard, main_menu_keyboard
from bot.qr import build_qr_file

router = Router(name="user")


def _profile_text(
    telegram_id: int,
    status: str,
    expires_text: str,
    location: str,
    traffic: str,
) -> str:
    return (
        "Профиль\n"
        f"Telegram ID: {telegram_id}\n"
        f"Статус подписки: {status}\n"
        f"Подписка до: {expires_text}\n"
        f"Текущая локация: {location}\n"
        f"Трафик: {traffic}\n\n"
        "Инструкция:\n"
        "1. Скачать Hiddify\n"
        "2. Открыть раздел Конфиг\n"
        "3. Импортировать конфиг\n"
        "4. Подключиться"
    )


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    container = get_container()
    await container.users.ensure_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
    )
    await message.answer(
        "Добро пожаловать в бот управления VPN\n\nВыберите действие:",
        reply_markup=main_menu_keyboard(),
    )


@router.message(F.text == "Конфиг")
async def config_handler(message: Message) -> None:
    container = get_container()
    try:
        profile = await container.users.get_profile(message.from_user.id)
        config = await container.users.get_config(message.from_user.id)
    except ValueError as exc:
        await message.answer(str(exc), reply_markup=main_menu_keyboard())
        return

    await message.answer(
        "Ваш VPN конфиг готов.\n"
        f"Локация: {profile.active_location.value.capitalize()}\n\n"
        f"<code>{escape(config)}</code>",
        reply_markup=main_menu_keyboard(),
    )
    await message.answer_photo(
        build_qr_file(config),
        caption="QR код для Hiddify",
        reply_markup=config_actions_keyboard(),
    )


@router.message(F.text == "Профиль")
async def profile_handler(message: Message) -> None:
    container = get_container()
    try:
        profile = await container.users.get_profile(message.from_user.id)
    except ValueError as exc:
        await message.answer(str(exc), reply_markup=main_menu_keyboard())
        return

    expires_text = (
        profile.subscription_expires_at.strftime("%Y-%m-%d %H:%M UTC")
        if profile.subscription_expires_at
        else "не задано"
    )
    await message.answer(
        _profile_text(
            telegram_id=profile.telegram_id,
            status=profile.subscription_status.value,
            expires_text=expires_text,
            location=profile.active_location.value.capitalize(),
            traffic=container.users.format_traffic(profile.traffic_used_bytes),
        ),
        reply_markup=main_menu_keyboard(),
    )


@router.message(F.text == "Продлить")
async def renew_handler(message: Message) -> None:
    await message.answer(
        "Продление подписки\n"
        "1 месяц - 150 RUB\n"
        "3 месяца - 400 RUB\n\n"
        "Платежный провайдер будет подключен отдельно.\n"
        "Сейчас продление можно делать вручную через администратора.",
        reply_markup=main_menu_keyboard(),
    )


@router.callback_query(F.data == "config:switch")
async def config_switch_handler(callback: CallbackQuery) -> None:
    await callback.message.answer(
        "Выберите новую локацию.",
        reply_markup=locations_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "config:reset")
async def config_reset_handler(callback: CallbackQuery) -> None:
    container = get_container()
    try:
        config = await container.users.reset_config(callback.from_user.id)
    except ValueError as exc:
        await callback.message.answer(str(exc), reply_markup=main_menu_keyboard())
        await callback.answer("Сброс недоступен", show_alert=True)
        return
    await callback.message.answer(
        "Конфиг сброшен и перевыпущен.\n\n"
        f"<code>{escape(config)}</code>",
        reply_markup=main_menu_keyboard(),
    )
    await callback.message.answer_photo(
        build_qr_file(config),
        caption="Новый QR код для Hiddify",
        reply_markup=config_actions_keyboard(),
    )
    await callback.answer("Конфиг обновлен")


@router.callback_query(F.data.startswith("config:set_location:"))
async def set_location_handler(callback: CallbackQuery) -> None:
    container = get_container()
    location_raw = callback.data.split(":")[-1]
    location = NodeLocation(location_raw)
    try:
        config = await container.users.switch_location(callback.from_user.id, location)
    except ValueError as exc:
        await callback.message.answer(str(exc), reply_markup=main_menu_keyboard())
        await callback.answer("Смена локации недоступна", show_alert=True)
        return
    await callback.message.answer(
        f"Локация изменена на {location.value.capitalize()}.\n\n"
        f"<code>{escape(config)}</code>",
        reply_markup=main_menu_keyboard(),
    )
    await callback.message.answer_photo(
        build_qr_file(config),
        caption="QR код для новой локации",
        reply_markup=config_actions_keyboard(),
    )
    await callback.answer("Локация обновлена")
