"""src/bot/handlers/auth/reset_password.py."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.utils.i18n import gettext as _
from src.bot.keyboards.inline.navigation import get_cancel_keyboard
from src.bot.keyboards.inline.start import get_start_keyboard
from src.bot.states.auth import ResetPasswordSG
from src.infrastructure import SwipeApiClient, SwipeAPIError

router = Router()


@router.message(Command("reset_password"))
async def start_reset_password(message: Message, state: FSMContext):
    """
    Starts the password reset flow.
    Transitions state to InputEmail.
    """
    await state.clear()
    await state.set_state(ResetPasswordSG.InputEmail)
    await message.answer(
        text=_("**Password Reset**\n\nEnter your **Email**:"),
        reply_markup=get_cancel_keyboard(),
    )


@router.message(ResetPasswordSG.InputEmail)
async def process_reset_email(message: Message, state: FSMContext):
    """
    Processes the email for password reset.
    Requests a reset code from the API and transitions to InputToken.
    """
    email = message.text.strip()
    api = SwipeApiClient()
    try:
        await api.auth.forgot_password(email=email)
        await state.update_data(email=email)
        await state.set_state(ResetPasswordSG.InputToken)
        await message.answer(
            text=_("Code sent. **Enter the code:**"), reply_markup=get_cancel_keyboard()
        )
    except SwipeAPIError as e:
        await message.answer(_("Error: {error}").format(error=e.message))


@router.message(ResetPasswordSG.InputToken)
async def process_reset_token(message: Message, state: FSMContext):
    """
    Saves the reset token and transitions to InputNewPassword.
    """
    await state.update_data(token=message.text.strip())
    await state.set_state(ResetPasswordSG.InputNewPassword)
    await message.answer(
        text=_("Code accepted. **Enter NEW password:**"),
        reply_markup=get_cancel_keyboard(),
    )


@router.message(ResetPasswordSG.InputNewPassword)
async def process_new_password(message: Message, state: FSMContext):
    """
    Submits the new password to the API.
    Clears state upon success.
    """
    new_pass = message.text
    data = await state.get_data()
    api = SwipeApiClient()
    try:
        await api.auth.reset_password(token=data["token"], new_password=new_pass)
        await message.answer(
            text=_("Password updated! Login now."), reply_markup=get_start_keyboard()
        )
        await state.clear()
    except SwipeAPIError as e:
        await message.answer(
            text=_("Error: {error}").format(error=e.message),
            reply_markup=get_cancel_keyboard(),
        )
