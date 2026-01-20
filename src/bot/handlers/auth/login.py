"""src/bot/handlers/auth/login.py."""

import logging
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.utils.i18n import gettext as _, lazy_gettext as __
from src.bot.callbacks import MenuCallback
from src.bot.keyboards.reply import (
    get_cancel_keyboard,
    get_login_password_keyboard,
)
from src.bot.keyboards.inline import get_main_menu_keyboard
from src.bot.states import LoginSG
from src.bot.utils import handle_cancel, remove_reply_keyboard, cleanup_last_step
from src.database import BotUser
from src.infrastructure.api import SwipeApiClient, SwipeAPIError
from src.bot.handlers.auth.reset_password import start_reset_password

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(MenuCallback.filter(F.action == "login"))
async def start_login(query: CallbackQuery, state: FSMContext):
    """
    Initiates the login process by transitioning state and showing the keyboard.
    """
    logger.info("User %s started login process", query.from_user.id)
    await state.set_state(LoginSG.InputEmail)
    await query.message.delete()

    msg = await query.message.answer(
        text=_("Please enter your **Email**:"), reply_markup=get_cancel_keyboard()
    )
    await state.update_data(last_bot_msg_id=msg.message_id)


@router.message(LoginSG.InputEmail)
async def process_email(message: Message, state: FSMContext):
    """
    Validates the email address.
    """
    if await handle_cancel(message, state):
        return

    email = message.text.strip()
    if "@" not in email:
        logger.debug("User %s entered invalid email: %s", message.from_user.id, email)
        msg = await message.answer(
            _("Invalid email format. Try again:"), reply_markup=get_cancel_keyboard()
        )
        await state.update_data(last_bot_msg_id=msg.message_id)
        return

    await cleanup_last_step(state, message)

    await state.update_data(email=email)
    await state.set_state(LoginSG.InputPassword)

    msg = await message.answer(
        text=_("Enter your **Password**:"), reply_markup=get_login_password_keyboard()
    )
    await state.update_data(last_bot_msg_id=msg.message_id)


@router.message(LoginSG.InputPassword, F.text == __("Back"))
async def back_to_email(message: Message, state: FSMContext):
    """
    Handles the 'Back' button, returning to email input.
    """
    await cleanup_last_step(state, message)

    await state.set_state(LoginSG.InputEmail)
    msg = await message.answer(
        text=_("Please enter your **Email**:"), reply_markup=get_cancel_keyboard()
    )
    await state.update_data(last_bot_msg_id=msg.message_id)


@router.message(LoginSG.InputPassword, F.text == __("Forgot Password?"))
async def on_forgot_password_btn(message: Message, state: FSMContext):
    """
    Handles the 'Forgot Password' button, switching to the reset flow.
    """

    logger.info("User %s clicked Forgot Password during login", message.from_user.id)
    await state.clear()
    await cleanup_last_step(state, message)
    await remove_reply_keyboard(message)

    await start_reset_password(message, state)


@router.message(LoginSG.InputPassword)
async def process_password(message: Message, state: FSMContext):
    """
    Validates password and performs API authentication.
    """
    if await handle_cancel(message, state):
        return

    if message.text in [_("Back"), _("Forgot Password?")]:
        return

    await cleanup_last_step(state, message)

    data = await state.get_data()
    email = data.get("email")
    password = message.text

    api = SwipeApiClient()
    wait_msg = await message.answer(
        _("Logging in..."), reply_markup=ReplyKeyboardRemove()
    )

    try:
        response = await api.auth.login(email=email, password=password)

        user = await BotUser.find_one(BotUser.telegram_id == message.from_user.id)
        if user:
            user.api_access_token = response["access_token"]
            user.api_refresh_token = response["refresh_token"]
            await user.save()

        await wait_msg.delete()
        await message.answer(
            text=_("**Successfully logged in!**"), reply_markup=get_main_menu_keyboard()
        )
        await state.clear()
        logger.info("User %s successfully logged in", message.from_user.id)

    except SwipeAPIError as e:
        logger.warning("Login failed for user %s: %s", message.from_user.id, e)
        await wait_msg.delete()
        msg = await message.answer(
            text=_("Login failed: {error}").format(error=e.message),
            reply_markup=get_login_password_keyboard(),
        )
        await state.update_data(last_bot_msg_id=msg.message_id)
