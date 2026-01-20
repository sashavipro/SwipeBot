"""src/bot/handlers/auth/reset_password.py."""

import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.utils.i18n import gettext as _
from src.bot.keyboards.reply import get_cancel_keyboard
from src.bot.keyboards.inline import get_start_keyboard
from src.bot.states import ResetPasswordSG
from src.bot.utils import handle_cancel, remove_reply_keyboard, cleanup_last_step
from src.infrastructure.api import SwipeApiClient, SwipeAPIError

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("reset_password"))
async def start_reset_password(message: Message, state: FSMContext):
    """
    Starts the password reset flow.
    """
    logger.info("User %s started password reset", message.from_user.id)
    await state.clear()

    if message.text.startswith("/"):
        try:
            await message.delete()
        except Exception:  # pylint: disable=broad-exception-caught
            pass

    await state.set_state(ResetPasswordSG.InputEmail)
    msg = await message.answer(
        text=_("**Password Reset**\n\nEnter your **Email**:"),
        reply_markup=get_cancel_keyboard(),
    )
    await state.update_data(last_bot_msg_id=msg.message_id)


@router.message(ResetPasswordSG.InputEmail)
async def process_reset_email(message: Message, state: FSMContext):
    """
    Processes email.
    """
    if await handle_cancel(message, state):
        return

    email = message.text.strip()
    api = SwipeApiClient()

    await cleanup_last_step(state, message)

    try:
        await api.auth.forgot_password(email=email)
        await state.update_data(email=email)
        await state.set_state(ResetPasswordSG.InputToken)

        msg = await message.answer(
            text=_("Code sent. **Enter the code:**"), reply_markup=get_cancel_keyboard()
        )
        await state.update_data(last_bot_msg_id=msg.message_id)
        logger.info("Reset code sent to email for user %s", message.from_user.id)

    except SwipeAPIError as e:
        logger.error(
            "Failed to send reset code for user %s: %s", message.from_user.id, e
        )
        msg = await message.answer(_("Error: {error}").format(error=e.message))
        await state.update_data(last_bot_msg_id=msg.message_id)


# pylint: disable=duplicate-code
@router.message(ResetPasswordSG.InputToken)
async def process_reset_token(message: Message, state: FSMContext):
    """
    Processes token.
    """
    if await handle_cancel(message, state):
        return

    await cleanup_last_step(state, message)

    await state.update_data(token=message.text.strip())
    await state.set_state(ResetPasswordSG.InputNewPassword)

    msg = await message.answer(
        text=_("Code accepted. **Enter NEW password:**"),
        reply_markup=get_cancel_keyboard(),
    )
    await state.update_data(last_bot_msg_id=msg.message_id)


@router.message(ResetPasswordSG.InputNewPassword)
async def process_new_password(message: Message, state: FSMContext):
    """
    Processes new password.
    """
    if await handle_cancel(message, state):
        return

    await cleanup_last_step(state, message)

    new_pass = message.text
    data = await state.get_data()
    api = SwipeApiClient()

    try:
        await api.auth.reset_password(token=data["token"], new_password=new_pass)
        await remove_reply_keyboard(message)

        await message.answer(
            text=_("Password updated! Login now."), reply_markup=get_start_keyboard()
        )
        await state.clear()
        logger.info("User %s successfully reset password", message.from_user.id)

    except SwipeAPIError as e:
        logger.error(
            "Failed to reset password for user %s: %s", message.from_user.id, e
        )
        msg = await message.answer(
            text=_("Error: {error}").format(error=e.message),
            reply_markup=get_cancel_keyboard(),
        )
        await state.update_data(last_bot_msg_id=msg.message_id)
