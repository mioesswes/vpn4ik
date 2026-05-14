from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.enums import PaymentProvider, PaymentStatus, SubscriptionStatus, TicketStatus
from database.models import Payment, SupportTicket, User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()

    async def get_required_by_telegram_id(self, telegram_id: int) -> User:
        user = await self.get_by_telegram_id(telegram_id)
        if user is None:
            user = await self.get_or_create(telegram_id=telegram_id, username=None)
        return user

    async def get_or_create(self, telegram_id: int, username: str | None) -> User:
        existing = await self.get_by_telegram_id(telegram_id)
        if existing is not None:
            if username and existing.username != username:
                existing.username = username
            existing.updated_at = datetime.now(UTC)
            return existing

        user = User(
            telegram_id=telegram_id,
            username=username,
            subscription_status=SubscriptionStatus.TRIAL,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self.session.add(user)
        await self.session.flush()
        return user


class PaymentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_topup(
        self,
        user_id: int,
        amount_rub: int,
        duration_months: int,
        provider: PaymentProvider = PaymentProvider.PENDING_INTEGRATION,
    ) -> Payment:
        payment = Payment(
            user_id=user_id,
            public_id=f"TOPUP-{uuid4().hex[:10].upper()}",
            provider=provider,
            status=PaymentStatus.DRAFT,
            amount_rub=amount_rub,
            duration_months=duration_months,
            payment_method_code=None,
            payment_url=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self.session.add(payment)
        await self.session.flush()
        return payment

    async def list_by_user(self, user_id: int, limit: int = 5) -> list[Payment]:
        result = await self.session.execute(
            select(Payment)
            .where(Payment.user_id == user_id)
            .order_by(Payment.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars())

    async def mark_paid(self, public_id: str) -> Payment | None:
        result = await self.session.execute(select(Payment).where(Payment.public_id == public_id))
        payment = result.scalar_one_or_none()
        if payment is None:
            return None
        payment.status = PaymentStatus.PAID
        payment.updated_at = datetime.now(UTC)
        return payment


class SupportRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_ticket(self, user_id: int, message_text: str) -> SupportTicket:
        ticket = SupportTicket(
            ticket_code=f"TCK-{uuid4().hex[:8].upper()}",
            user_id=user_id,
            message_text=message_text,
            status=TicketStatus.OPEN,
            created_at=datetime.now(UTC),
        )
        self.session.add(ticket)
        await self.session.flush()
        return ticket

    async def list_by_user(self, user_id: int) -> list[SupportTicket]:
        result = await self.session.execute(
            select(SupportTicket)
            .where(SupportTicket.user_id == user_id)
            .order_by(SupportTicket.created_at.desc())
        )
        return list(result.scalars())

    async def list_open(self, limit: int = 20) -> list[SupportTicket]:
        result = await self.session.execute(
            select(SupportTicket)
            .where(SupportTicket.status == TicketStatus.OPEN)
            .order_by(SupportTicket.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars())

    async def get_by_code(self, ticket_code: str) -> SupportTicket | None:
        result = await self.session.execute(
            select(SupportTicket).where(SupportTicket.ticket_code == ticket_code)
        )
        return result.scalar_one_or_none()

    async def close_stale(self, before: datetime) -> None:
        result = await self.session.execute(
            select(SupportTicket).where(
                SupportTicket.status == TicketStatus.OPEN,
                SupportTicket.created_at < before,
            )
        )
        for ticket in result.scalars():
            ticket.status = TicketStatus.CLOSED
            ticket.closed_at = datetime.now(UTC)


class StatsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def user_count(self) -> int:
        result = await self.session.execute(select(func.count()).select_from(User))
        return int(result.scalar_one())

    async def active_subscriptions_count(self) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(User)
            .where(User.subscription_status == SubscriptionStatus.ACTIVE)
        )
        return int(result.scalar_one())

    async def today_new_users_count(self) -> int:
        today = datetime.now(UTC).date()
        result = await self.session.execute(
            select(func.count()).select_from(User).where(func.date(User.created_at) == today)
        )
        return int(result.scalar_one())

    async def revenue_sum(self, days: int) -> float:
        since = datetime.now(UTC) - timedelta(days=days)
        result = await self.session.execute(
            select(func.coalesce(func.sum(Payment.amount_rub), 0))
            .select_from(Payment)
            .where(Payment.status == PaymentStatus.PAID, Payment.created_at >= since)
        )
        return float(result.scalar_one())
