"""src/bot/middlewares/i18n.py."""

import logging
from typing import Any, Dict, Awaitable, Callable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User
from aiogram.utils.i18n import I18n
from src.database import BotUser

logger = logging.getLogger(__name__)


class LanguageMiddleware(BaseMiddleware):
    """
    Middleware for determining and setting the user's language.
    Also injects the 'user' (BotUser) into the handler arguments.
    """

    # pylint: disable=too-few-public-methods
    def __init__(self, i18n: I18n):
        """
        Initializes the middleware.
        """
        self.i18n = i18n

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """
        Processes the incoming update.
        Determines locale based on DB -> Telegram -> Default priority.
        """
        tg_user: User | None = data.get("event_from_user")
        user: BotUser | None = data.get("user")

        if not user and tg_user:
            user = await BotUser.find_one(BotUser.telegram_id == tg_user.id)

        if user:
            data["user"] = user

        locale = "en"
        if user and user.language_code:
            locale = user.language_code
        elif tg_user and tg_user.language_code:
            if tg_user.language_code in ["en", "ru"]:
                locale = tg_user.language_code

        if tg_user:
            logger.debug(
                "Selected locale '%s' for user %s (DB found: %s)",
                locale,
                tg_user.id,
                bool(user),
            )

        data["i18n"] = self.i18n

        with self.i18n.context(), self.i18n.use_locale(locale):
            return await handler(event, data)
