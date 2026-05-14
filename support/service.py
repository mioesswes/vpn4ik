from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import async_sessionmaker

from backend.config import Settings
from database.repositories import SupportRepository, UserRepository


class TicketDTO:
    def __init__(
        self,
        ticket_code: str,
        message_text: str,
        status: str,
        user_telegram_id: int | None = None,
    ) -> None:
        self.ticket_code = ticket_code
        self.message_text = message_text
        self.status = status
        self.user_telegram_id = user_telegram_id


class SupportService:
    def __init__(self, settings: Settings, session_factory: async_sessionmaker) -> None:
        self.settings = settings
        self.session_factory = session_factory

    async def create_ticket(self, telegram_id: int, text: str) -> TicketDTO:
        async with self.session_factory() as session:
            user_repo = UserRepository(session)
            support_repo = SupportRepository(session)
            user = await user_repo.get_required_by_telegram_id(telegram_id)
            ticket = await support_repo.create_ticket(user_id=user.id, message_text=text)
            await session.commit()
            return TicketDTO(
                ticket_code=ticket.ticket_code,
                message_text=ticket.message_text,
                status=ticket.status.value,
            )

    async def list_user_tickets(self, telegram_id: int) -> list[TicketDTO]:
        async with self.session_factory() as session:
            user_repo = UserRepository(session)
            support_repo = SupportRepository(session)
            user = await user_repo.get_required_by_telegram_id(telegram_id)
            tickets = await support_repo.list_by_user(user.id)
            return [
                TicketDTO(
                    ticket_code=ticket.ticket_code,
                    message_text=ticket.message_text,
                    status=ticket.status.value,
                )
                for ticket in tickets
            ]

    async def reply_to_ticket(self, ticket_code: str, reply_text: str) -> TicketDTO | None:
        async with self.session_factory() as session:
            repo = SupportRepository(session)
            user_repo = UserRepository(session)
            ticket = await repo.get_by_code(ticket_code)
            if ticket is None:
                return None
            ticket.admin_reply_text = reply_text
            user = await user_repo.get_by_id(ticket.user_id)
            await session.commit()
            return TicketDTO(
                ticket_code=ticket.ticket_code,
                message_text=ticket.message_text,
                status=ticket.status.value,
                user_telegram_id=user.telegram_id if user else None,
            )

    async def close_stale_tickets(self) -> None:
        async with self.session_factory() as session:
            repo = SupportRepository(session)
            await repo.close_stale(before=datetime.utcnow() - timedelta(days=30))
            await session.commit()
