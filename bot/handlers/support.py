from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from backend.runtime import get_container
from bot.states import SupportStates

router = Router(name="support")


@router.callback_query(F.data == "support:list")
async def list_tickets_handler(callback: CallbackQuery) -> None:
    container = get_container()
    tickets = await container.support.list_user_tickets(callback.from_user.id)
    if not tickets:
        await callback.message.edit_text("У вас пока нет тикетов.")
    else:
        lines = [
            f"{ticket.ticket_code} [{ticket.status}] - {ticket.message_text[:80]}"
            for ticket in tickets
        ]
        await callback.message.edit_text("Ваши тикеты:\n" + "\n".join(lines))
    await callback.answer()


@router.callback_query(F.data == "support:create")
async def create_ticket_prompt_handler(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SupportStates.waiting_for_ticket_message)
    await callback.message.edit_text(
        "Опишите проблему одним сообщением. Бот создаст ticket ID и отправит обращение администратору."
    )
    await callback.answer()


@router.message(SupportStates.waiting_for_ticket_message)
async def incoming_ticket_message_handler(message: Message, state: FSMContext) -> None:
    if not message.text:
        return
    container = get_container()
    ticket = await container.support.create_ticket(message.from_user.id, message.text)
    await state.clear()
    await message.answer(
        f"Обращение принято.\nTicket ID: {ticket.ticket_code}\nАдминистратор получит уведомление и ответит вам в Telegram."
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
