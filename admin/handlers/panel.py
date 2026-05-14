import re
from html import escape

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from backend.runtime import get_container

router = Router(name="admin")
TICKET_CODE_RE = re.compile(r"Ticket:\s*(TCK-[A-Z0-9]+)")
GRANT_COMMAND_RE = re.compile(r"^/grant\s+(\d+)\s+(\d+)$")
RESET_COMMAND_RE = re.compile(r"^/vpnreset\s+(\d+)$")
NODES_COMMAND_RE = re.compile(r"^/nodes$")


def admin_menu_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Статистика", callback_data="admin:stats")
    builder.button(text="Серверы", callback_data="admin:servers")
    builder.button(text="Пользователи", callback_data="admin:users")
    builder.button(text="Тикеты", callback_data="admin:tickets")
    builder.button(text="Рассылки", callback_data="admin:broadcast")
    builder.adjust(2, 2, 1)
    return builder.as_markup()


def is_admin(user_id: int) -> bool:
    return user_id in get_container().settings.admin_ids


@router.message(F.text == "/admin")
async def admin_entry(message: Message) -> None:
    if not is_admin(message.from_user.id):
        return
    await message.answer("Админ панель", reply_markup=admin_menu_keyboard())


@router.message(F.text.regexp(GRANT_COMMAND_RE))
async def grant_subscription(message: Message) -> None:
    if not is_admin(message.from_user.id):
        return
    match = GRANT_COMMAND_RE.match(message.text or "")
    if not match:
        return
    telegram_id = int(match.group(1))
    months = int(match.group(2))
    await get_container().payments.activate_user_subscription(telegram_id=telegram_id, months=months)
    await message.answer(f"Подписка активирована: user={telegram_id}, months={months}")


@router.message(F.text.regexp(RESET_COMMAND_RE))
async def reset_user_vpn(message: Message) -> None:
    if not is_admin(message.from_user.id):
        return
    match = RESET_COMMAND_RE.match(message.text or "")
    if not match:
        return
    telegram_id = int(match.group(1))
    config = await get_container().users.reset_config(telegram_id=telegram_id)
    await message.answer(
        f"VPN конфиг перевыпущен для {telegram_id}.\n\n<code>{escape(config)}</code>"
    )


@router.message(F.text.regexp(NODES_COMMAND_RE))
async def admin_nodes_message(message: Message) -> None:
    if not is_admin(message.from_user.id):
        return
    summaries = await get_container().monitoring.node_summary()
    await message.answer("Ноды:\n" + "\n".join(summaries))


@router.callback_query(F.data == "admin:stats")
async def admin_stats(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    stats = await get_container().admin.get_stats()
    await callback.message.edit_text(
        "Статистика\n"
        f"Пользователей всего: {stats.total_users}\n"
        f"Активных подписок: {stats.active_subscriptions}\n"
        f"Новых за день: {stats.new_today}\n"
        f"Доход за день: {stats.revenue_day:.0f} RUB\n"
        f"Доход за месяц: {stats.revenue_month:.0f} RUB"
    )
    await callback.answer()


@router.callback_query(F.data == "admin:servers")
async def admin_servers(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    summaries = await get_container().monitoring.node_summary()
    await callback.message.edit_text("Серверы:\n" + "\n".join(summaries))
    await callback.answer()


@router.callback_query(F.data == "admin:tickets")
async def admin_tickets(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    tickets = await get_container().admin.list_open_tickets()
    text = "Открытые тикеты:\n" + ("\n".join(tickets) if tickets else "Нет открытых тикетов.")
    await callback.message.edit_text(text)
    await callback.answer()


@router.message(F.reply_to_message)
async def admin_ticket_reply(message: Message) -> None:
    if not is_admin(message.from_user.id):
        return
    if not message.reply_to_message or not message.reply_to_message.text or not message.text:
        return
    match = TICKET_CODE_RE.search(message.reply_to_message.text)
    if not match:
        return
    ticket_code = match.group(1)
    ticket = await get_container().support.reply_to_ticket(ticket_code=ticket_code, reply_text=message.text)
    if ticket is None:
        await message.answer("Тикет не найден.")
        return
    if ticket.user_telegram_id:
        await message.bot.send_message(
            ticket.user_telegram_id,
            "Ответ от тех поддержки\n"
            f"{message.text}",
        )
    await message.answer(f"Ответ сохранен для {ticket_code}.")
