"""src/bot/handlers/auth/registration.py."""

import re
import logging
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.utils.i18n import gettext as _, lazy_gettext as __

from src.bot.callbacks import MenuCallback
from src.bot.keyboards.inline import get_start_keyboard, get_main_menu_keyboard
from src.bot.keyboards.reply import (
    get_contact_keyboard,
    get_cancel_keyboard,
    get_back_keyboard,
)
from src.bot.states import RegistrationSG
from src.bot.utils import handle_cancel, remove_reply_keyboard, cleanup_last_step
from src.database import BotUser
from src.infrastructure.api import SwipeApiClient, SwipeAPIError

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(MenuCallback.filter(F.action == "registration"))
async def start_reg(query: CallbackQuery, state: FSMContext):
    """Starts registration."""
    logger.info("User %s started registration", query.from_user.id)
    await state.set_state(RegistrationSG.InputFirstName)
    await query.message.delete()

    msg = await query.message.answer(
        text=_("**Registration Step 1/5**\n\nEnter your **First Name**:"),
        reply_markup=get_cancel_keyboard(),
    )
    await state.update_data(last_bot_msg_id=msg.message_id)


@router.message(RegistrationSG.InputFirstName, F.text == __("Back"))
async def back_to_start(message: Message, state: FSMContext):
    """Back from Step 1 -> Menu."""
    logger.info("User %s went back to start menu", message.from_user.id)
    await state.clear()
    await message.answer(_("Registration canceled."), reply_markup=get_start_keyboard())


@router.message(RegistrationSG.InputLastName, F.text == __("Back"))
async def back_to_firstname(message: Message, state: FSMContext):
    """Back from Step 2 -> Step 1."""
    await cleanup_last_step(state, message)
    await state.set_state(RegistrationSG.InputFirstName)
    msg = await message.answer(
        text=_("Enter your **First Name**:"), reply_markup=get_cancel_keyboard()
    )
    await state.update_data(last_bot_msg_id=msg.message_id)


@router.message(RegistrationSG.InputEmail, F.text == __("Back"))
async def back_to_lastname(message: Message, state: FSMContext):
    """Back from Step 3 -> Step 2."""
    await cleanup_last_step(state, message)
    await state.set_state(RegistrationSG.InputLastName)
    msg = await message.answer(
        text=_("Enter your **Last Name**:"), reply_markup=get_back_keyboard()
    )
    await state.update_data(last_bot_msg_id=msg.message_id)


@router.message(RegistrationSG.InputPassword, F.text == __("Back"))
async def back_to_phone_reply(message: Message, state: FSMContext):
    """Back from Step 5 -> Step 4."""
    await cleanup_last_step(state, message)
    await state.set_state(RegistrationSG.InputPhone)
    msg = await message.answer(
        text=_(
            "**Step 4/5**\n\nShare your **Phone Number** using the button below or "
            "type it manually (+123...):"
        ),
        reply_markup=get_contact_keyboard(),
    )
    await state.update_data(last_bot_msg_id=msg.message_id)


@router.message(RegistrationSG.InputFirstName)
async def input_first_name(message: Message, state: FSMContext):
    """Validates and saves the first name."""
    if await handle_cancel(message, state):
        return

    if len(message.text) < 2:
        msg = await message.answer(_("Too short. Please enter real First Name:"))
        await state.update_data(last_bot_msg_id=msg.message_id)
        return

    await cleanup_last_step(state, message)
    await state.update_data(first_name=message.text)
    await state.set_state(RegistrationSG.InputLastName)

    msg = await message.answer(
        text=_("**Step 2/5**\n\nEnter your **Last Name**:"),
        reply_markup=get_back_keyboard(),
    )
    await state.update_data(last_bot_msg_id=msg.message_id)


@router.message(RegistrationSG.InputLastName)
async def input_last_name(message: Message, state: FSMContext):
    """Saves the last name and prompts for email."""
    if await handle_cancel(message, state):
        return

    await cleanup_last_step(state, message)
    await state.update_data(last_name=message.text)
    await state.set_state(RegistrationSG.InputEmail)

    msg = await message.answer(
        text=_("**Step 3/5**\n\nEnter your **Email**:"),
        reply_markup=get_back_keyboard(),
    )
    await state.update_data(last_bot_msg_id=msg.message_id)


@router.message(RegistrationSG.InputEmail)
async def input_email(message: Message, state: FSMContext):
    """
    Validates email format and prompts for phone number.
    """
    if await handle_cancel(message, state):
        return

    email = message.text.strip()
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        msg = await message.answer(_("Invalid email format. Try again:"))
        await state.update_data(last_bot_msg_id=msg.message_id)
        return

    await cleanup_last_step(state, message)

    await state.update_data(email=email)
    await state.set_state(RegistrationSG.InputPhone)

    msg = await message.answer(
        text=_(
            "**Step 4/5**\n\nShare your **Phone Number** using the button below or "
            "type it manually (+123...):"
        ),
        reply_markup=get_contact_keyboard(),
    )
    await state.update_data(last_bot_msg_id=msg.message_id)


@router.message(RegistrationSG.InputPhone, F.text == __("Back"))
async def back_to_email_reply(message: Message, state: FSMContext):
    """
    Returns to Email input step (Step 4 -> Step 3).
    """
    await cleanup_last_step(state, message)

    await state.set_state(RegistrationSG.InputEmail)
    msg = await message.answer(
        text=_("**Step 3/5**\n\nEnter your **Email**:"),
        reply_markup=get_back_keyboard(),
    )
    await state.update_data(last_bot_msg_id=msg.message_id)


@router.message(RegistrationSG.InputPhone)
@router.message(RegistrationSG.InputPhone, F.contact)
async def input_phone(message: Message, state: FSMContext):
    """
    Validates and saves the phone number.
    """
    if await handle_cancel(message, state):
        return

    if message.text == _("Back"):
        await back_to_email_reply(message, state)
        return

    if message.contact:
        phone = message.contact.phone_number
    else:
        phone = message.text
        if not re.match(r"^\+?\d{7,15}$", phone):
            logger.debug(
                "User %s entered invalid phone: %s", message.from_user.id, phone
            )
            msg = await message.answer(
                _("Invalid phone format. Please use +123456789."),
                reply_markup=get_contact_keyboard(),
            )
            await state.update_data(last_bot_msg_id=msg.message_id)
            return

    if not phone.startswith("+"):
        phone = "+" + phone

    await cleanup_last_step(state, message)

    await state.update_data(phone=phone)
    await state.set_state(RegistrationSG.InputPassword)

    msg = await message.answer(
        text=_("**Step 5/5**\n\nCreate a **Password** for your account:"),
        reply_markup=get_back_keyboard(),
    )
    await state.update_data(last_bot_msg_id=msg.message_id)


@router.message(RegistrationSG.InputPassword)
async def input_password(message: Message, state: FSMContext):
    """Validates password, submits registration data, and requests OTP."""
    if await handle_cancel(message, state):
        return

    if len(message.text) < 6:
        msg = await message.answer(_("Password must be at least 6 characters."))
        await state.update_data(last_bot_msg_id=msg.message_id)
        return

    await cleanup_last_step(state, message)

    await state.update_data(password=message.text)
    user_data = await state.get_data()

    api = SwipeApiClient()
    wait_msg = await message.answer(
        _("Sending data to server..."), reply_markup=ReplyKeyboardRemove()
    )

    try:
        logger.info("Submitting registration for user %s", message.from_user.id)
        await api.auth.register(user_data)

        await wait_msg.delete()
        await state.set_state(RegistrationSG.InputCode)

        msg = await message.answer(
            text=_(
                "Data accepted!\n\n"
                "We sent a verification code to **{email}**.\n\n"
                "**Enter the code below:**"
            ).format(email=user_data["email"]),
            reply_markup=get_cancel_keyboard(),
        )
        await state.update_data(last_bot_msg_id=msg.message_id)

    except SwipeAPIError as e:
        logger.error("Registration failed for user %s: %s", message.from_user.id, e)
        await wait_msg.delete()

        if e.status_code == 409:
            await state.clear()
            await message.answer(
                _("**You are already registered!**\n\nPlease log in."),
                reply_markup=get_start_keyboard(),
            )
            return

        msg = await message.answer(
            text=_(
                "Registration failed: {error}\n\nPlease try changing data or cancel."
            ).format(error=e.message),
            reply_markup=get_back_keyboard(),
        )
        await state.update_data(last_bot_msg_id=msg.message_id)


@router.message(RegistrationSG.InputCode)
async def input_code(message: Message, state: FSMContext):
    """Verifies the confirmation code and completes the registration."""
    if await handle_cancel(message, state):
        return

    code = message.text.strip()
    data = await state.get_data()
    api = SwipeApiClient()

    try:
        logger.info("Verifying code for user %s", message.from_user.id)
        await api.auth.verify_registration(email=data["email"], code=code)
        login_resp = await api.auth.login(
            email=data["email"], password=data["password"]
        )

        user = await BotUser.find_one(BotUser.telegram_id == message.from_user.id)
        if user:
            user.api_access_token = login_resp["access_token"]
            user.api_refresh_token = login_resp["refresh_token"]
            await user.save()

        await cleanup_last_step(state, message)
        await remove_reply_keyboard(message)

        await message.answer(
            text=_(
                "**Registration Successful!**\n\n"
                "User:\n{first} {last}\n{email}\n{phone}\n"
                "Password: <tg-spoiler>{password}</tg-spoiler>\n\n"
                "You are now logged in!"
            ).format(
                first=data["first_name"],
                last=data["last_name"],
                email=data["email"],
                phone=data["phone"],
                password=data["password"],
            ),
            reply_markup=get_main_menu_keyboard(),
        )

        await state.clear()
        logger.info(
            "User %s successfully registered and logged in", message.from_user.id
        )

    except SwipeAPIError as e:
        logger.warning(
            "Code verification failed for user %s: %s", message.from_user.id, e
        )
        if e.status_code == 409:
            await state.clear()
            await message.answer(
                _("**You are already registered!**\n\nPlease log in."),
                reply_markup=get_start_keyboard(),
            )
            return

        msg = await message.answer(
            text=_(
                "Code verification failed: {error}.\nCheck code and try again:"
            ).format(error=e.message),
            reply_markup=get_cancel_keyboard(),
        )
        await state.update_data(last_bot_msg_id=msg.message_id)
