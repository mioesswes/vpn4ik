from dataclasses import dataclass

from sqlalchemy.ext.asyncio import async_sessionmaker

from database.repositories import StatsRepository, SupportRepository


@dataclass(slots=True)
class AdminStats:
    total_users: int
    active_subscriptions: int
    new_today: int
    revenue_day: float
    revenue_month: float


class AdminService:
    def __init__(self, session_factory: async_sessionmaker) -> None:
        self.session_factory = session_factory

    async def get_stats(self) -> AdminStats:
        async with self.session_factory() as session:
            repo = StatsRepository(session)
            return AdminStats(
                total_users=await repo.user_count(),
                active_subscriptions=await repo.active_subscriptions_count(),
                new_today=await repo.today_new_users_count(),
                revenue_day=await repo.revenue_sum(days=1),
                revenue_month=await repo.revenue_sum(days=30),
            )

    async def list_open_tickets(self) -> list[str]:
        async with self.session_factory() as session:
            repo = SupportRepository(session)
            tickets = await repo.list_open(limit=20)
            return [f"{ticket.ticket_code}: {ticket.message_text[:80]}" for ticket in tickets]
