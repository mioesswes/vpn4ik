from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from backend.runtime import get_container
from bot.keyboards.main import main_menu_keyboard
from bot.states import SupportStates

router = Router(name="support")
MENU_TEXTS = {"Конфиг", "Профиль", "Продлить", "Поддержка"}


@router.message(F.text == "Поддержка")
async def support_entry_handler(message: Message, state: FSMContext) -> None:
    container = get_container()
    tickets = await container.support.list_user_tickets(message.from_user.id)
    lines = [
        f"{ticket.ticket_code} [{ticket.status}] - {ticket.message_text[:60]}"
        for ticket in tickets[:5]
    ]
    text = "Поддержка\n"
    if lines:
        text += "Ваши последние тикеты:\n" + "\n".join(lines) + "\n\n"
    else:
        text += "У вас пока нет тикетов.\n\n"
    text += "Опишите проблему следующим сообщением."
    await state.set_state(SupportStates.waiting_for_ticket_message)
    await message.answer(text, reply_markup=main_menu_keyboard())


@router.message(SupportStates.waiting_for_ticket_message)
async def incoming_ticket_message_handler(message: Message, state: FSMContext) -> None:
    if not message.text:
        return
    if message.text in MENU_TEXTS:
        await state.clear()
        await message.answer(
            "Создание обращения отменено. Выберите действие из меню.",
            reply_markup=main_menu_keyboard(),
        )
        return

    container = get_container()
    ticket = await container.support.create_ticket(message.from_user.id, message.text)
    await state.clear()
    await message.answer(
        f"Обращение принято.\nTicket ID: {ticket.ticket_code}\nАдминистратор ответит вам в Telegram.",
        reply_markup=main_menu_keyboard(),
    )
    recipients = []
    if container.settings.support_chat_id:
        recipients.append(container.settings.support_chat_id)
    else:
        recipients.extend(container.settings.admin_ids)
    for recipient_id in recipients:
        await message.bot.send_message(
            recipient_id,
            "Новое обращение\n"
            f"Ticket: {ticket.ticket_code}\n"
            f"User ID: {message.from_user.id}\n"
            f"Username: @{message.from_user.username or 'unknown'}\n\n"
            f"{message.text}",
        )
