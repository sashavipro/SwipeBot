"""src/bot/keyboards/inline/start.py."""

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.i18n import gettext as _
from src.bot.callbacks import MenuCallback


def get_start_keyboard() -> InlineKeyboardMarkup:
    """
    Creates the main menu inline keyboard.
    Includes options for Login, Registration, and Language selection.
    """
    builder = InlineKeyboardBuilder()
    builder.button(text=_("Login"), callback_data=MenuCallback(action="login"))
    builder.button(
        text=_("Registration"), callback_data=MenuCallback(action="registration")
    )
    builder.button(
        text=_("Язык / Language"), callback_data=MenuCallback(action="language")
    )
    builder.adjust(2, 1)
    return builder.as_markup()
