"""src/bot/keyboards/inline/announcement.py."""

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.i18n import gettext as _
from src.bot.callbacks import ListingCallback


def get_item_keyboard(announcement_id: int) -> InlineKeyboardMarkup:
    """
    Keyboard attached to each listing item (Location button).
    """
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_("Location"),
        callback_data=ListingCallback(action="geo", id=announcement_id),
    )

    return builder.as_markup()
