"""src/main.py."""

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.utils.i18n import I18n
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from src.bot.handlers import main_router
from src.bot.middlewares import LanguageMiddleware
from src.config import settings
from src.database import BotUser, get_redis_client


async def on_startup():
    """
    Performs startup actions for the bot application.
    """
    logging.info("Connecting to MongoDB...")
    client = AsyncIOMotorClient(settings.MONGO_URL)

    await init_beanie(
        database=client[settings.MONGO_DB_NAME],
        document_models=[BotUser],
    )
    logging.info("MongoDB connected successfully.")


async def main():
    """
    Entry point for the Telegram bot application.
    """
    logging.basicConfig(
        level=settings.LOG_LEVEL,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    logger = logging.getLogger(__name__)
    logger.info("Starting Swipe Bot...")

    redis = get_redis_client()
    storage = RedisStorage(redis=redis)

    bot = Bot(
        token=settings.BOT_TOKEN.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    i18n = I18n(path="src/locales", default_locale="en", domain="messages")
    dp = Dispatcher(storage=storage)

    dp.update.outer_middleware(LanguageMiddleware(i18n))

    dp.include_router(main_router)

    dp.startup.register(on_startup)

    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await redis.aclose()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped!")
        raise
