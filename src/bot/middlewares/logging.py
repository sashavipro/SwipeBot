"""src/bot/middlewares/logging.py."""

import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseMiddleware):
    """
    Middleware for logging incoming updates (Messages and Callbacks).
    """

    # pylint: disable=too-few-public-methods
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """
        Logs the event and passes control to the next handler.
        """
        user = data.get("event_from_user")
        user_id = user.id if user else "unknown"

        if isinstance(event, Message):
            logger.info("User %s sent message: %s", user_id, event.text)
        elif isinstance(event, CallbackQuery):
            logger.info("User %s clicked callback: %s", user_id, event.data)

        return await handler(event, data)
