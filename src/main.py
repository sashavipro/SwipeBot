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
from src.bot.ui_commands import set_ui_commands


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
        format="%(asctime)s - [%(levelname)s] - %(name)s - (%(filename)s)"
        ".%(funcName)s(%(lineno)d) - %(message)s",
    )
    logger = logging.getLogger(__name__)
    logger.info("Starting Swipe Bot...")

    logger.info("Initializing Redis storage...")
    redis = get_redis_client()
    storage = RedisStorage(redis=redis)

    bot = Bot(
        token=settings.BOT_TOKEN.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    logger.info("Configuring i18n...")
    i18n = I18n(path="src/locales", default_locale="en", domain="messages")
    dp = Dispatcher(storage=storage)

    logger.info("Registering middlewares...")
    dp.update.outer_middleware(LanguageMiddleware(i18n))

    logger.info("Registering routers...")
    dp.include_router(main_router)

    dp.startup.register(on_startup)

    logger.info("Setting up UI commands...")
    await set_ui_commands(bot)

    await bot.delete_webhook(drop_pending_updates=True)
    try:
        logger.info("Bot started polling.")
        await dp.start_polling(bot)
    finally:
        logger.info("Shutting down bot...")
        await bot.session.close()
        await redis.aclose()
        logger.info("Bot stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot execution interrupted.")
        raise
