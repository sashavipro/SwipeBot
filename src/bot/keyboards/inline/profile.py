"""src/bot/keyboards/inline/profile.py."""

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.i18n import gettext as _
from src.bot.callbacks import MenuCallback


def get_profile_keyboard() -> InlineKeyboardMarkup:
    """
    Creates inline keyboard for Profile view.
    """
    builder = InlineKeyboardBuilder()

    builder.button(
        text=_("My Listings"), callback_data=MenuCallback(action="my_listings")
    )

    builder.adjust(1)
    return builder.as_markup()
