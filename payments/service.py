from datetime import UTC, datetime, timedelta
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import async_sessionmaker

from backend.config import Settings
from backend.enums import PaymentProvider, SubscriptionPlan, SubscriptionStatus
from database.repositories import PaymentRepository, UserRepository
from payments.catalog import PLANS, PlanDefinition


@dataclass(slots=True)
class TopUpRequest:
    public_id: str
    amount_rub: int
    duration_months: int
    status: str
    provider: PaymentProvider


class PaymentService:
    def __init__(self, settings: Settings, session_factory: async_sessionmaker) -> None:
        self.settings = settings
        self.session_factory = session_factory

    def get_plan(self, plan: SubscriptionPlan) -> PlanDefinition:
        return PLANS[plan]

    async def create_topup_request(
        self,
        telegram_id: int,
        plan: SubscriptionPlan,
        provider: PaymentProvider = PaymentProvider.PENDING_INTEGRATION,
    ) -> TopUpRequest:
        plan_def = self.get_plan(plan)
        async with self.session_factory() as session:
            user_repo = UserRepository(session)
            payment_repo = PaymentRepository(session)
            user = await user_repo.get_required_by_telegram_id(telegram_id)
            payment = await payment_repo.create_topup(
                user_id=user.id,
                amount_rub=plan_def.amount_rub,
                duration_months=plan_def.months,
                provider=provider,
            )
            await session.commit()
            return TopUpRequest(
                public_id=payment.public_id,
                amount_rub=plan_def.amount_rub,
                duration_months=plan_def.months,
                status=payment.status.value,
                provider=payment.provider,
            )

    async def list_recent_topups(self, telegram_id: int) -> list[TopUpRequest]:
        async with self.session_factory() as session:
            user_repo = UserRepository(session)
            payment_repo = PaymentRepository(session)
            user = await user_repo.get_required_by_telegram_id(telegram_id)
            payments = await payment_repo.list_by_user(user.id)
            return [
                TopUpRequest(
                    public_id=payment.public_id,
                    amount_rub=int(payment.amount_rub),
                    duration_months=payment.duration_months,
                    status=payment.status.value,
                    provider=payment.provider,
                )
                for payment in payments
            ]

    async def confirm_topup(self, public_id: str) -> bool:
        async with self.session_factory() as session:
            payment_repo = PaymentRepository(session)
            user_repo = UserRepository(session)
            payment = await payment_repo.mark_paid(public_id)
            if payment is None:
                return False

            user = await user_repo.get_by_id(payment.user_id)
            if user is None:
                return False

            now = datetime.now(UTC)
            base = user.subscription_expires_at if user.subscription_expires_at and user.subscription_expires_at > now else now
            user.subscription_expires_at = base + timedelta(days=payment.duration_months * 30)
            user.subscription_status = SubscriptionStatus.ACTIVE
            user.updated_at = now
            await session.commit()
            return True

    async def activate_user_subscription(self, telegram_id: int, months: int) -> bool:
        async with self.session_factory() as session:
            user_repo = UserRepository(session)
            user = await user_repo.get_required_by_telegram_id(telegram_id)
            now = datetime.now(UTC)
            base = (
                user.subscription_expires_at
                if user.subscription_expires_at and user.subscription_expires_at > now
                else now
            )
            user.subscription_expires_at = base + timedelta(days=months * 30)
            user.subscription_status = SubscriptionStatus.ACTIVE
            user.updated_at = now
            await session.commit()
            return True

    async def reconcile_pending_payments(self) -> None:
        return None
