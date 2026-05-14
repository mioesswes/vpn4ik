from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import async_sessionmaker

from backend.config import Settings
from backend.enums import NodeLocation, SubscriptionStatus
from database.repositories import UserRepository
from xray.service import XrayService


@dataclass(slots=True)
class UserProfile:
    telegram_id: int
    subscription_status: SubscriptionStatus
    subscription_expires_at: datetime | None
    active_location: NodeLocation
    traffic_used_bytes: int
    config_text: str | None


class UserService:
    def __init__(
        self,
        settings: Settings,
        session_factory: async_sessionmaker,
        xray: XrayService,
    ) -> None:
        self.settings = settings
        self.session_factory = session_factory
        self.xray = xray

    @staticmethod
    def _has_access(status: SubscriptionStatus, expires_at: datetime | None) -> bool:
        if status == SubscriptionStatus.BANNED:
            return False
        if status in {SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL}:
            return expires_at is None or expires_at > datetime.now(UTC)
        return False

    async def ensure_user(self, telegram_id: int, username: str | None) -> None:
        async with self.session_factory() as session:
            repo = UserRepository(session)
            user = await repo.get_or_create(telegram_id=telegram_id, username=username)
            if (
                user.subscription_expires_at is None
                and self.settings.trial_duration_days > 0
                and user.subscription_status == SubscriptionStatus.TRIAL
            ):
                user.subscription_expires_at = datetime.now(UTC) + timedelta(
                    days=self.settings.trial_duration_days
                )
            await session.commit()

    async def get_profile(self, telegram_id: int) -> UserProfile:
        async with self.session_factory() as session:
            repo = UserRepository(session)
            user = await repo.get_required_by_telegram_id(telegram_id)
            config_text = None
            if self._has_access(user.subscription_status, user.subscription_expires_at):
                config_text = await self.xray.generate_vless_reality_config(
                    user_id=user.telegram_id,
                    location=user.active_location,
                )
            return UserProfile(
                telegram_id=user.telegram_id,
                subscription_status=user.subscription_status,
                subscription_expires_at=user.subscription_expires_at,
                active_location=user.active_location,
                traffic_used_bytes=user.traffic_used_bytes,
                config_text=config_text,
            )

    async def get_config(self, telegram_id: int) -> str:
        async with self.session_factory() as session:
            repo = UserRepository(session)
            user = await repo.get_required_by_telegram_id(telegram_id)
            if not self._has_access(user.subscription_status, user.subscription_expires_at):
                raise ValueError("Подписка неактивна. Доступ к VPN закрыт.")
            await self.xray.ensure_client(
                user_id=user.telegram_id,
                location=user.active_location,
                device_limit=user.device_limit,
            )
            return await self.xray.generate_vless_reality_config(
                user_id=user.telegram_id,
                location=user.active_location,
            )

    async def switch_location(self, telegram_id: int, location: NodeLocation) -> str:
        async with self.session_factory() as session:
            repo = UserRepository(session)
            user = await repo.get_required_by_telegram_id(telegram_id)
            if not self._has_access(user.subscription_status, user.subscription_expires_at):
                raise ValueError("Подписка неактивна. Смена локации недоступна.")
            old_location = user.active_location
            user.active_location = location
            user.updated_at = datetime.now(UTC)
            await session.commit()
            return await self.xray.switch_user_location(
                user_id=user.telegram_id,
                old_location=old_location,
                location=location,
                device_limit=user.device_limit,
            )

    async def reset_config(self, telegram_id: int) -> str:
        async with self.session_factory() as session:
            repo = UserRepository(session)
            user = await repo.get_required_by_telegram_id(telegram_id)
            if not self._has_access(user.subscription_status, user.subscription_expires_at):
                raise ValueError("Подписка неактивна. Сброс конфига недоступен.")
            await self.xray.delete_client(user_id=user.telegram_id, location=user.active_location)
            await self.xray.ensure_client(
                user_id=user.telegram_id,
                location=user.active_location,
                device_limit=user.device_limit,
            )
            return await self.xray.generate_vless_reality_config(
                user_id=user.telegram_id,
                location=user.active_location,
            )

    @staticmethod
    def format_traffic(traffic_used_bytes: int) -> str:
        units = ["B", "KB", "MB", "GB", "TB"]
        value = float(traffic_used_bytes)
        for unit in units:
            if value < 1024 or unit == units[-1]:
                return f"{value:.1f} {unit}"
            value /= 1024
        return f"{traffic_used_bytes} B"
