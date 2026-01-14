"""src/bot/keyboards/inline/navigation.py."""

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.i18n import gettext as _
from src.bot.callbacks.menu import MenuCallback


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """
    Creates a universal inline keyboard with a single 'Cancel' button.
    Used to return the user to the main menu.
    """
    builder = InlineKeyboardBuilder()
    builder.button(text=_("Cancel"), callback_data=MenuCallback(action="cancel"))
    return builder.as_markup()


def get_back_keyboard(callback_data: str) -> InlineKeyboardMarkup:
    """
    Creates an inline keyboard with 'Back' and 'Cancel' buttons.
    """
    builder = InlineKeyboardBuilder()
    builder.button(text=_("Back"), callback_data=callback_data)
    builder.button(text=_("Cancel"), callback_data=MenuCallback(action="cancel"))
    builder.adjust(1)
    return builder.as_markup()
