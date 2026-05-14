from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from admin.handlers.panel import router as admin_router
from backend.runtime import get_container
from bot.handlers.support import router as support_router
from bot.handlers.user import router as user_router


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    dp.include_router(user_router)
    dp.include_router(support_router)
    dp.include_router(admin_router)
    return dp


async def create_bot() -> Bot:
    container = get_container()
    await container.database.create_schema()
    return Bot(
        token=container.settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
