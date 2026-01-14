"""src/bot/handlers/auth/login.py."""

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.i18n import gettext as _
from src.bot.callbacks.menu import MenuCallback
from src.bot.handlers.auth.reset_password import start_reset_password
from src.bot.keyboards.inline.login import get_login_password_keyboard
from src.bot.keyboards.inline.navigation import get_cancel_keyboard
from src.bot.keyboards.inline.start import get_start_keyboard
from src.bot.states.auth import LoginSG
from src.database.models import BotUser
from src.infrastructure import SwipeApiClient, SwipeAPIError

router = Router()


@router.callback_query(MenuCallback.filter(F.action == "login"))
async def start_login(query: CallbackQuery, state: FSMContext):
    """
    Initiates the login process by requesting the user's email.
    """
    await state.set_state(LoginSG.InputEmail)
    await query.message.edit_text(
        text=_("Please enter your **Email**:"), reply_markup=get_cancel_keyboard()
    )


@router.message(LoginSG.InputEmail)
async def process_email(message: Message, state: FSMContext):
    """
    Validates the provided email address and transitions to the password input state.
    """
    email = message.text.strip()
    if "@" not in email:
        await message.answer(
            _("Invalid email format. Try again:"), reply_markup=get_cancel_keyboard()
        )
        return

    await state.update_data(email=email)
    await state.set_state(LoginSG.InputPassword)

    await message.answer(
        text=_("Enter your **Password**:"),
        reply_markup=get_login_password_keyboard(
            back_callback_data="back_to_email_login"
        ),
    )


@router.callback_query(F.data == "back_to_email_login")
async def back_to_email(query: CallbackQuery, state: FSMContext):
    """
    Handles the 'Back' button, returning the user to the email input state.
    """
    await state.set_state(LoginSG.InputEmail)
    await query.message.edit_text(
        text=_("Please enter your **Email**:"), reply_markup=get_cancel_keyboard()
    )


@router.callback_query(MenuCallback.filter(F.action == "forgot_password"))
async def on_forgot_password_btn(query: CallbackQuery, state: FSMContext):
    """
    Switches the user from the login flow to the password reset flow.
    """
    await state.clear()

    await start_reset_password(query.message, state)

    await query.answer()


@router.message(LoginSG.InputPassword)
async def process_password(message: Message, state: FSMContext):
    """
    Validates the password, performs authentication via the API client,
    and stores the resulting tokens in the database.
    """
    data = await state.get_data()
    email = data.get("email")
    password = message.text

    api = SwipeApiClient()
    wait_msg = await message.answer(_("Logging in..."))

    try:
        response = await api.auth.login(email=email, password=password)

        user = await BotUser.find_one(BotUser.telegram_id == message.from_user.id)
        if user:
            user.api_access_token = response["access_token"]
            user.api_refresh_token = response["refresh_token"]
            await user.save()

        await wait_msg.delete()
        await message.answer(
            text=_("**Successfully logged in!**"), reply_markup=get_start_keyboard()
        )
        await state.clear()

    except SwipeAPIError as e:
        await wait_msg.delete()
        await message.answer(
            text=_("Login failed: {error}").format(error=e.message),
            reply_markup=get_login_password_keyboard(
                back_callback_data="back_to_email_login"
            ),
        )
