"""src/bot/keyboards/inline/main_menu.py."""

import logging
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.i18n import gettext as _
from src.bot.callbacks import MenuCallback

logger = logging.getLogger(__name__)


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Creates the main menu keyboard for authorized users.
    Includes: Listings, Create Listing, Profile.
    """
    logger.debug("Generating main menu keyboard")
    builder = InlineKeyboardBuilder()

    builder.button(text=_("Listings"), callback_data=MenuCallback(action="listings"))
    builder.button(
        text=_("Create Listing"), callback_data=MenuCallback(action="create_listing")
    )
    builder.button(text=_("My Profile"), callback_data=MenuCallback(action="profile"))
    builder.button(text=_("Logout"), callback_data=MenuCallback(action="logout"))

    builder.adjust(1)
    return builder.as_markup()
