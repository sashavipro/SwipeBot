"""src/bot/keyboards/reply/create_announcement.py."""

from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.utils.i18n import gettext as _


def get_location_keyboard() -> ReplyKeyboardMarkup:
    """
    Creates a reply keyboard with a button to share geolocation.
    """
    builder = ReplyKeyboardBuilder()
    builder.button(text=_("Share Location"), request_location=True)
    builder.button(text=_("Cancel"))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def get_done_keyboard() -> ReplyKeyboardMarkup:
    """
    Creates a reply keyboard with a 'Done' button for image upload step.
    """
    builder = ReplyKeyboardBuilder()
    builder.button(text=_("Done"))
    builder.button(text=_("Cancel"))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)
