"""src/bot/handlers/menu.py."""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _, lazy_gettext as __
from src.bot.callbacks import MenuCallback
from src.bot.keyboards.inline import (
    get_start_keyboard,
    get_profile_keyboard,
    get_main_menu_keyboard,
)
from src.bot.keyboards.reply import get_back_to_menu_keyboard
from src.bot.states import ProfileSG
from src.bot.utils import execute_with_refresh
from src.database import BotUser
from src.infrastructure.api import SwipeApiClient, SwipeAPIError

router = Router()
logger = logging.getLogger(__name__)


async def _show_profile_logic(message: Message, user: BotUser, state: FSMContext):
    """
    Reusable logic for fetching and showing profile with navigation.
    """
    if not user or not user.api_access_token:
        logger.warning(
            "User %s attempted to view profile without login", message.from_user.id
        )
        await message.answer(
            _("You are not logged in. Please login first."),
            reply_markup=get_start_keyboard(),
        )
        return

    api = SwipeApiClient()

    try:
        logger.info("Fetching profile for user %s", user.telegram_id)
        profile_data = await execute_with_refresh(user, api.users.get_my_profile)

        await state.set_state(ProfileSG.Viewing)

        await message.answer(
            text=_("**My Profile Mode**"), reply_markup=get_back_to_menu_keyboard()
        )

        await message.answer(
            text=_(
                "**Personal Info:**\n\n"
                "Name: {first} {last}\n"
                "Email: {email}\n"
                "Phone: {phone}"
            ).format(
                first=profile_data["first_name"],
                last=profile_data["last_name"],
                email=profile_data["email"],
                phone=profile_data["phone"],
            ),
            reply_markup=get_profile_keyboard(),
        )

    except SwipeAPIError as e:
        logger.error("Failed to fetch profile for user %s: %s", user.telegram_id, e)
        if e.status_code == 401:
            await message.answer(_("Your session has expired. Please log in again."))
        else:
            await message.answer(
                _("An error occurred: {error}").format(error=e.message)
            )


@router.callback_query(MenuCallback.filter(F.action == "profile"))
async def show_profile_callback(query: CallbackQuery, user: BotUser, state: FSMContext):
    """
    Handles 'My Profile' button click from Main Menu.
    """
    await query.message.delete()
    await _show_profile_logic(query.message, user, state)
    await query.answer()


@router.message(Command("profile"))
async def show_profile_command(message: Message, state: FSMContext):
    """
    Handles /profile command.
    """
    user = await BotUser.find_one(BotUser.telegram_id == message.from_user.id)
    await _show_profile_logic(message, user, state)


@router.message(ProfileSG.Viewing, F.text == __("Back to Menu"))
async def back_from_profile(message: Message, state: FSMContext):
    """
    Returns from Profile to Main Menu.
    """
    logger.info("User %s returning to main menu from profile", message.from_user.id)
    await state.clear()

    msg = await message.answer("...", reply_markup=ReplyKeyboardRemove())
    await msg.delete()

    await message.answer(
        text=_("Select an action:"), reply_markup=get_main_menu_keyboard()
    )
