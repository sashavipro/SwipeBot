"""src/bot/keyboards/reply/announcement.py."""

import logging
from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.utils.i18n import gettext as _

logger = logging.getLogger(__name__)


def get_location_keyboard() -> ReplyKeyboardMarkup:
    """
    Creates a reply keyboard with a button to share geolocation.
    """
    logger.debug("Generating location request keyboard")
    builder = ReplyKeyboardBuilder()
    builder.button(text=_("Share Location"), request_location=True)
    builder.button(text=_("Cancel"))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def get_done_keyboard() -> ReplyKeyboardMarkup:
    """
    Creates a reply keyboard with a 'Done' button for image upload step.
    """
    logger.debug("Generating 'Done' keyboard")
    builder = ReplyKeyboardBuilder()
    builder.button(text=_("Done"))
    builder.button(text=_("Cancel"))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)


def get_listings_reply_keyboard(has_prev: bool, has_next: bool) -> ReplyKeyboardMarkup:
    """
    Returns the reply keyboard for the listings mode with pagination.
    """
    builder = ReplyKeyboardBuilder()

    if has_prev:
        builder.button(text="⬅️")
    if has_next:
        builder.button(text="➡️")

    builder.button(text=_("Back to Menu"))

    if has_prev and has_next:
        builder.adjust(2, 1)
    else:
        builder.adjust(1, 1)

    return builder.as_markup(resize_keyboard=True)
