"""src/bot/callbacks/menu.py."""

from aiogram.filters.callback_data import CallbackData


class MenuCallback(CallbackData, prefix="menu"):
    """
    Callback Data factory for main menu navigation buttons.
    """

    action: str
