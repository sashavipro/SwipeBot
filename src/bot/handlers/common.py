"""src/bot/handlers/common.py."""

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.i18n import gettext as _, lazy_gettext as __
from src.bot.callbacks import MenuCallback, LanguageCallback
from src.bot.keyboards.inline import (
    get_start_keyboard,
    get_language_keyboard,
    get_main_menu_keyboard,
)
from src.bot.utils import handle_cancel
from src.database import BotUser

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    """
    Handles the /start command.
    Checks auth status and shows appropriate menu.
    """
    user = await BotUser.find_one(BotUser.telegram_id == message.from_user.id)
    if not user:
        user = BotUser(
            telegram_id=message.from_user.id,
            full_name=message.from_user.full_name,
            username=message.from_user.username,
            language_code=message.from_user.language_code or "en",
        )
        await user.create()

    if user.api_access_token:
        await message.answer(
            text=_("Welcome back, {name}! Select an action:").format(
                name=user.full_name
            ),
            reply_markup=get_main_menu_keyboard(),
        )
    else:
        await message.answer(
            text=_("Welcome to Swipe! Select:"),
            reply_markup=get_start_keyboard(),
        )


@router.callback_query(MenuCallback.filter(F.action == "language"))
async def open_language_menu(query: CallbackQuery):
    """
    Opens the language selection menu.
    """
    await query.message.edit_text(
        text=_("Select the interface language:"), reply_markup=get_language_keyboard()
    )


@router.callback_query(MenuCallback.filter(F.action == "back"))
async def back_to_main_menu(query: CallbackQuery):
    """
    Returns the user to the main menu.
    """
    await query.message.edit_text(
        text=_("Welcome to Swipe! Select an action:"), reply_markup=get_start_keyboard()
    )


@router.callback_query(LanguageCallback.filter())
async def set_language(query: CallbackQuery, callback_data: LanguageCallback, i18n):
    """
    Updates the user's language preference in the database and the current session.
    """
    user = await BotUser.find_one(BotUser.telegram_id == query.from_user.id)
    if user:
        user.language_code = callback_data.code
        await user.save()

    await query.answer(_("Language changed!"))
    i18n.ctx_locale.set(callback_data.code)

    if user and user.api_access_token:
        keyboard = get_main_menu_keyboard()
    else:
        keyboard = get_start_keyboard()

    await query.message.edit_text(text=_("Select an action:"), reply_markup=keyboard)


@router.message(F.text == __("Cancel"))
async def cancel_action_reply(message: Message, state: FSMContext):
    """
    Handles the 'Cancel' text button (Global).
    """
    await handle_cancel(message, state)


@router.callback_query(MenuCallback.filter(F.action == "logout"))
async def logout_user(query: CallbackQuery, state: FSMContext):
    """
    Logs out the user by clearing tokens from MongoDB.
    """
    user = await BotUser.find_one(BotUser.telegram_id == query.from_user.id)
    if user:
        user.api_access_token = None
        user.api_refresh_token = None
        await user.save()

    await state.clear()

    await query.message.edit_text(
        text=_("You have successfully logged out."), reply_markup=get_start_keyboard()
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """
    Handles the /help command.
    """
    await message.answer(
        text=_(
            "**Swipe Bot Help**\n\n"
            "/start - Main Menu\n"
            "/profile - My Profile\n\n"
            "If you found a bug, please contact support."
        )
    )
