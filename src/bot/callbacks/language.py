"""src/bot/callbacks/language.py."""

from aiogram.filters.callback_data import CallbackData


class LanguageCallback(CallbackData, prefix="lang"):
    """
    Callback Data factory for language selection buttons.
    """

    code: str
