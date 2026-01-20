"""src/bot/keyboards/reply/login.py."""

import logging
from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.utils.i18n import gettext as _

logger = logging.getLogger(__name__)


def get_login_password_keyboard() -> ReplyKeyboardMarkup:
    """
    Creates a reply keyboard for the password input stage.
    """
    logger.debug("Generating login password keyboard")
    builder = ReplyKeyboardBuilder()
    builder.button(text=_("Forgot Password?"))
    builder.button(text=_("Back"))
    builder.button(text=_("Cancel"))

    builder.adjust(1, 2)
    return builder.as_markup(resize_keyboard=True)
