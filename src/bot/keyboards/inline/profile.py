"""src/bot/keyboards/inline/profile.py."""

import logging
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.i18n import gettext as _
from src.bot.callbacks import MenuCallback

logger = logging.getLogger(__name__)


def get_profile_keyboard() -> InlineKeyboardMarkup:
    """
    Creates inline keyboard for Profile view.
    """
    logger.debug("Generating profile keyboard")
    builder = InlineKeyboardBuilder()

    builder.button(
        text=_("My Listings"), callback_data=MenuCallback(action="my_listings")
    )

    builder.adjust(1)
    return builder.as_markup()
