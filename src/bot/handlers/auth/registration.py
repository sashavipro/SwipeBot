"""src/bot/handlers/auth/registration.py."""

import re
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.utils.i18n import gettext as _
from src.bot.callbacks.menu import MenuCallback
from src.bot.keyboards.inline.navigation import get_cancel_keyboard, get_back_keyboard
from src.bot.keyboards.inline.start import get_start_keyboard
from src.bot.keyboards.reply.get_contact import get_contact_keyboard
from src.bot.states.auth import RegistrationSG
from src.database.models import BotUser
from src.infrastructure import SwipeApiClient, SwipeAPIError

router = Router()


@router.callback_query(MenuCallback.filter(F.action == "registration"))
async def start_reg(query: CallbackQuery, state: FSMContext):
    """
    Starts the registration process.
    Transitions state to InputFirstName.
    """
    await state.set_state(RegistrationSG.InputFirstName)
    await query.message.edit_text(
        text=_("**Registration Step 1/5**\n\nEnter your **First Name**:"),
        reply_markup=get_cancel_keyboard(),
    )


@router.message(RegistrationSG.InputFirstName)
async def input_first_name(message: Message, state: FSMContext):
    """
    Validates and saves the first name.
    Transitions state to InputLastName.
    """
    if len(message.text) < 2:
        await message.answer(_("Too short. Please enter real First Name:"))
        return
    await state.update_data(first_name=message.text)
    await state.set_state(RegistrationSG.InputLastName)
    await message.answer(
        text=_("**Step 2/5**\n\nEnter your **Last Name**:"),
        reply_markup=get_back_keyboard("back_to_firstname"),
    )


@router.callback_query(F.data == "back_to_firstname")
async def back_to_firstname(query: CallbackQuery, state: FSMContext):
    """
    Returns to the First Name input step.
    """
    await state.set_state(RegistrationSG.InputFirstName)
    await query.message.edit_text(
        text=_("Enter your **First Name**:"), reply_markup=get_cancel_keyboard()
    )


@router.message(RegistrationSG.InputLastName)
async def input_last_name(message: Message, state: FSMContext):
    """
    Saves the last name.
    Transitions state to InputEmail.
    """
    await state.update_data(last_name=message.text)
    await state.set_state(RegistrationSG.InputEmail)
    await message.answer(
        text=_("**Step 3/5**\n\nEnter your **Email**:"),
        reply_markup=get_back_keyboard("back_to_lastname"),
    )


@router.callback_query(F.data == "back_to_lastname")
async def back_to_lastname(query: CallbackQuery, state: FSMContext):
    """
    Returns to the Last Name input step.
    """
    await state.set_state(RegistrationSG.InputLastName)
    await query.message.edit_text(
        text=_("Enter your **Last Name**:"),
        reply_markup=get_back_keyboard("back_to_firstname"),
    )


@router.message(RegistrationSG.InputEmail)
async def input_email(message: Message, state: FSMContext):
    """
    Validates and saves the email.
    Transitions state to InputPhone.
    """
    email = message.text.strip()
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        await message.answer(_("Invalid email format. Try again:"))
        return
    await state.update_data(email=email)
    await state.set_state(RegistrationSG.InputPhone)
    await message.answer(
        text=_(
            "**Step 4/5**\n\nShare your **Phone Number** using the button below or "
            "type it manually (+123...):"
        ),
        reply_markup=get_contact_keyboard(),
    )


@router.callback_query(F.data == "back_to_email")
async def back_to_email(query: CallbackQuery, state: FSMContext):
    """
    Returns to the Email input step.
    """
    await state.set_state(RegistrationSG.InputEmail)
    msg = await query.message.answer("...", reply_markup=ReplyKeyboardRemove())
    await msg.delete()
    await query.message.edit_text(
        text=_("Enter your **Email**:"),
        reply_markup=get_back_keyboard("back_to_lastname"),
    )


@router.message(RegistrationSG.InputPhone)
@router.message(RegistrationSG.InputPhone, F.contact)
async def input_phone(message: Message, state: FSMContext):
    """
    Validates and saves the phone number (from text or contact).
    Transitions state to InputPassword.
    """
    if message.text and message.text == _("Cancel Registration"):
        await state.clear()
        await message.answer(
            _("Registration canceled."), reply_markup=ReplyKeyboardRemove()
        )
        await message.answer(_("Main Menu:"), reply_markup=get_start_keyboard())
        return
    if message.contact:
        phone = message.contact.phone_number
    else:
        phone = message.text
        if not re.match(r"^\+?\d{7,15}$", phone):
            await message.answer(_("Invalid phone format. Please use +123456789."))
            return
    if not phone.startswith("+"):
        phone = "+" + phone
    await state.update_data(phone=phone)
    await state.set_state(RegistrationSG.InputPassword)
    await message.answer(
        text=_("**Step 5/5**\n\nCreate a **Password** for your account:"),
        reply_markup=ReplyKeyboardRemove(),
    )
    await message.answer(
        text=_("Type password:"), reply_markup=get_back_keyboard("back_to_phone")
    )


@router.callback_query(F.data == "back_to_phone")
async def back_to_phone(query: CallbackQuery, state: FSMContext):
    """
    Returns to the Phone input step.
    """
    await state.set_state(RegistrationSG.InputPhone)
    await query.message.answer(
        text=_("Share your **Phone Number**:"), reply_markup=get_contact_keyboard()
    )
    await query.message.delete()


@router.message(RegistrationSG.InputPassword)
async def input_password(message: Message, state: FSMContext):
    """
    Saves the password and submits registration data to the API.
    Transitions state to InputCode upon success.
    """
    if len(message.text) < 6:
        await message.answer(_("Password must be at least 6 characters."))
        return
    await state.update_data(password=message.text)
    user_data = await state.get_data()
    api = SwipeApiClient()
    wait_msg = await message.answer(_("Sending data to server..."))
    try:
        await api.auth.register(user_data)
        await wait_msg.delete()
        await state.set_state(RegistrationSG.InputCode)
        await message.answer(
            text=_(
                "Data accepted!\n\n"
                "We sent a verification code to **{email}**.\n\n"
                "**Enter the code below:**"
            ).format(email=user_data["email"]),
            reply_markup=get_cancel_keyboard(),
        )
    except SwipeAPIError as e:
        await wait_msg.delete()
        await message.answer(
            text=_(
                "Registration failed: {error}\n\nPlease try changing data or cancel."
            ).format(error=e.message),
            reply_markup=get_back_keyboard("back_to_password"),
        )


@router.message(RegistrationSG.InputCode)
async def input_code(message: Message, state: FSMContext):
    """
    Verifies the email code via API.
    Logs the user in and saves the token to MongoDB.
    """
    code = message.text.strip()
    data = await state.get_data()
    api = SwipeApiClient()
    try:
        await api.auth.verify_registration(email=data["email"], code=code)
        login_resp = await api.auth.login(
            email=data["email"], password=data["password"]
        )
        user = await BotUser.find_one(BotUser.telegram_id == message.from_user.id)
        if user:
            user.api_access_token = login_resp["access_token"]
            user.api_refresh_token = login_resp["refresh_token"]
            await user.save()
        await state.clear()
        await message.answer(
            text=_(
                "**Registration Successful!**\n\n"
                "User:\n{first} {last}\n{email}\n{phone}\n\n"
                "You are now logged in!"
            ).format(
                first=data["first_name"],
                last=data["last_name"],
                email=data["email"],
                phone=data["phone"],
            ),
            reply_markup=get_start_keyboard(),
        )
    except SwipeAPIError as e:
        await message.answer(
            text=_(
                "Code verification failed: {error}.\nCheck code and try again:"
            ).format(error=e.message),
            reply_markup=get_cancel_keyboard(),
        )
