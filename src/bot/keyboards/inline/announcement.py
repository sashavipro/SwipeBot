"""src/bot/keyboards/inline/create_announcement.py."""

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.i18n import gettext as _
from src.bot.callbacks import ListingCallback


def get_listings_nav_keyboard(has_prev: bool, has_next: bool) -> InlineKeyboardMarkup:
    """
    Creates navigation buttons (Prev, Geo, Next).
    """
    builder = InlineKeyboardBuilder()

    if has_prev:
        builder.button(text="⬅️", callback_data=ListingCallback(action="prev"))

    builder.button(text=_("Location"), callback_data=ListingCallback(action="geo"))

    if has_next:
        builder.button(text="➡️", callback_data=ListingCallback(action="next"))

    builder.adjust(3)
    return builder.as_markup()
