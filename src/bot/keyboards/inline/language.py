"""src/bot/keyboards/inline/language.py."""

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.i18n import gettext as _
from src.bot.callbacks.language import LanguageCallback
from src.bot.callbacks.menu import MenuCallback


def get_language_keyboard() -> InlineKeyboardMarkup:
    """
    Creates an inline keyboard for interface language selection.
    Includes options for English and Russian, plus a navigation back button.
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="English", callback_data=LanguageCallback(code="en"))
    builder.button(text="Русский", callback_data=LanguageCallback(code="ru"))
    builder.button(text=_("Back"), callback_data=MenuCallback(action="back"))
    builder.adjust(1)
    return builder.as_markup()
