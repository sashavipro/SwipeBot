"""src/bot/keyboards/reply/get_contact.py."""

from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.utils.i18n import gettext as _


def get_contact_keyboard() -> ReplyKeyboardMarkup:
    """
    Creates a reply keyboard with a button to share the user's contact information.
    Also includes a cancellation button.
    """
    builder = ReplyKeyboardBuilder()
    builder.button(text=_("Share my contact"), request_contact=True)
    builder.button(text=_("Cancel Registration"))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
