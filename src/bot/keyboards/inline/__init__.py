"""src/bot/keyboards/inline/__init__.py."""

from .language import get_language_keyboard
from .start import get_start_keyboard
from .main_menu import get_main_menu_keyboard

__all__ = [
    "get_start_keyboard",
    "get_language_keyboard",
    "get_main_menu_keyboard",
]
