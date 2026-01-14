"""src/bot/keyboards/inline/login.py."""

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.i18n import gettext as _
from src.bot.callbacks.menu import MenuCallback


def get_login_password_keyboard(back_callback_data: str) -> InlineKeyboardMarkup:
    """
    Creates an inline keyboard for the password input stage of the login flow.
    Includes a 'Forgot Password' option, as well as navigation buttons.
    """
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_("Forgot Password?"), callback_data=MenuCallback(action="forgot_password")
    )
    builder.button(text=_("Back"), callback_data=back_callback_data)
    builder.button(text=_("Cancel"), callback_data=MenuCallback(action="cancel"))
    builder.adjust(1, 2)
    return builder.as_markup()
