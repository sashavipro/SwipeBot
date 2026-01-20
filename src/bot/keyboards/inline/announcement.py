"""src/bot/keyboards/inline/announcement.py."""

import logging
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.i18n import gettext as _
from src.bot.callbacks import ListingCallback

logger = logging.getLogger(__name__)


def get_listings_nav_keyboard(has_prev: bool, has_next: bool) -> InlineKeyboardMarkup:
    """
    Creates navigation buttons (Prev, Geo, Next).
    """
    logger.debug(
        "Generating listings nav keyboard: prev=%s, next=%s", has_prev, has_next
    )
    builder = InlineKeyboardBuilder()

    if has_prev:
        builder.button(text="⬅️", callback_data=ListingCallback(action="prev"))

    builder.button(text=_("Location"), callback_data=ListingCallback(action="geo"))

    if has_next:
        builder.button(text="➡️", callback_data=ListingCallback(action="next"))

    builder.adjust(3)
    return builder.as_markup()
