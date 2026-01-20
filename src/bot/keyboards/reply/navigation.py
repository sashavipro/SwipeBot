"""src/bot/keyboards/reply/navigation.py."""

import logging
from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.utils.i18n import gettext as _

logger = logging.getLogger(__name__)


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """
    Creates a reply keyboard with a single 'Cancel' button.
    """
    logger.debug("Generating cancel keyboard")
    builder = ReplyKeyboardBuilder()
    builder.button(text=_("Cancel"))
    return builder.as_markup(resize_keyboard=True)


def get_back_keyboard() -> ReplyKeyboardMarkup:
    """
    Creates a reply keyboard with 'Back' and 'Cancel' buttons.
    """
    logger.debug("Generating back/cancel keyboard")
    builder = ReplyKeyboardBuilder()
    builder.button(text=_("Back"))
    builder.button(text=_("Cancel"))
    builder.adjust(1, 1)
    return builder.as_markup(resize_keyboard=True)


def get_back_to_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    Creates a reply keyboard with a single 'Back to Menu' button.
    """
    logger.debug("Generating back to menu keyboard")
    builder = ReplyKeyboardBuilder()
    builder.button(text=_("Back to Menu"))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)
