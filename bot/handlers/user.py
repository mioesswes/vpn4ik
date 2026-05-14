from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from backend.enums import NodeLocation, SubscriptionPlan
from backend.runtime import get_container
from bot.keyboards.main import (
    config_menu_keyboard,
    locations_keyboard,
    main_menu_keyboard,
    renewal_keyboard,
    support_menu_keyboard,
)
from bot.qr import build_qr_file

router = Router(name="user")


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    container = get_container()
    await container.users.ensure_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
    )
    await message.answer(
        "VPN сервис в Telegram.\n\nВыберите действие в меню ниже.",
        reply_markup=main_menu_keyboard(),
    )


@router.callback_query(F.data == "menu:config")
async def config_handler(callback: CallbackQuery) -> None:
    container = get_container()
    try:
        profile = await container.users.get_profile(callback.from_user.id)
    except ValueError as exc:
        await callback.message.edit_text(str(exc))
        await callback.answer("Нода не настроена", show_alert=True)
        return
    await callback.message.edit_text(
        "Раздел конфигурации\n"
        f"Текущая локация: {profile.active_location.value.capitalize()}\n"
        "Вы можете скопировать конфиг, получить QR код или сменить локацию.",
        reply_markup=config_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "menu:profile")
async def profile_handler(callback: CallbackQuery) -> None:
    container = get_container()
    try:
        profile = await container.users.get_profile(callback.from_user.id)
    except ValueError as exc:
        await callback.message.edit_text(str(exc))
        await callback.answer("Нода не настроена", show_alert=True)
        return
    expires_text = (
        profile.subscription_expires_at.strftime("%Y-%m-%d")
        if profile.subscription_expires_at
        else "не задано"
    )
    await callback.message.edit_text(
        "Профиль\n"
        f"Telegram ID: {profile.telegram_id}\n"
        f"Статус: {profile.subscription_status.value}\n"
        f"Подписка до: {expires_text}\n"
        f"Локация: {profile.active_location.value.capitalize()}\n"
        f"Трафик: {container.users.format_traffic(profile.traffic_used_bytes)}\n\n"
        "Инструкция:\n"
        "1. Скачать Hiddify\n"
        "2. Нажать «Скопировать конфиг»\n"
        "3. Вставить конфиг\n"
        "4. Подключиться",
    )
    await callback.answer()


@router.callback_query(F.data == "menu:renew")
async def renew_handler(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "Продление подписки\n"
        "Выберите тариф. Запрос на пополнение будет создан уже сейчас,\n"
        "а конкретный метод оплаты подключим позже.",
        reply_markup=renewal_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "menu:support")
async def support_handler(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "Поддержка\nВы можете посмотреть свои тикеты или создать новое обращение.",
        reply_markup=support_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "config:copy")
async def config_copy_handler(callback: CallbackQuery) -> None:
    container = get_container()
    try:
        config = await container.users.get_config(callback.from_user.id)
    except ValueError as exc:
        await callback.message.answer(str(exc))
        await callback.answer("Нода не настроена", show_alert=True)
        return
    await callback.message.answer(f"Ваш VLESS Reality конфиг:\n\n`{config}`", parse_mode="Markdown")
    await callback.answer("Конфиг отправлен")


@router.callback_query(F.data == "config:qr")
async def config_qr_handler(callback: CallbackQuery) -> None:
    container = get_container()
    try:
        config = await container.users.get_config(callback.from_user.id)
    except ValueError as exc:
        await callback.message.answer(str(exc))
        await callback.answer("Нода не настроена", show_alert=True)
        return
    qr_file = build_qr_file(config)
    await callback.message.answer_photo(qr_file, caption="QR код для импорта в Hiddify")
    await callback.answer("QR код сформирован")


@router.callback_query(F.data == "config:switch")
async def config_switch_handler(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
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
        await callback.message.edit_text(str(exc))
        await callback.answer("Сброс недоступен", show_alert=True)
        return
    await callback.message.edit_text(
        "Конфиг сброшен и перевыпущен.\n\n"
        f"`{config}`",
        parse_mode="Markdown",
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
        await callback.message.edit_text(str(exc))
        await callback.answer("Нода не настроена", show_alert=True)
        return
    await callback.message.edit_text(
        f"Локация изменена на {location.value.capitalize()}.\n\nНовый конфиг:\n`{config}`",
        parse_mode="Markdown",
    )
    await callback.answer("Локация обновлена")


@router.callback_query(F.data.startswith("renew:plan:"))
async def create_topup_handler(callback: CallbackQuery) -> None:
    container = get_container()
    plan_raw = callback.data.split(":")[-1]
    topup = await container.payments.create_topup_request(
        telegram_id=callback.from_user.id,
        plan=SubscriptionPlan(plan_raw),
    )
    await callback.message.edit_text(
        "Запрос на пополнение создан.\n"
        f"ID: {topup.public_id}\n"
        f"Сумма: {topup.amount_rub} ₽\n"
        f"Срок: {topup.duration_months} мес.\n"
        "Статус: ожидает подключения платежного метода.\n\n"
        "Позже сюда можно будет подключить CryptoBot, YooMoney или другой провайдер без переделки сценария."
    )
    await callback.answer("Запрос создан")
