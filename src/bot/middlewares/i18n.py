"""src/bot/middlewares/i18n.py."""

from typing import Any, Dict, Awaitable, Callable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User
from aiogram.utils.i18n import I18n
from src.database.models import BotUser


class LanguageMiddleware(BaseMiddleware):
    """
    Middleware for determining and setting the user's language.
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
        """
        tg_user: User | None = data.get("event_from_user")

        user: BotUser | None = data.get("user")

        if not user and tg_user:
            user = await BotUser.find_one(BotUser.telegram_id == tg_user.id)

        locale = "en"

        if user and user.language_code:
            locale = user.language_code
        elif tg_user and tg_user.language_code:
            if tg_user.language_code in ["en", "ru"]:
                locale = tg_user.language_code

        data["i18n"] = self.i18n

        with self.i18n.context(), self.i18n.use_locale(locale):
            return await handler(event, data)
