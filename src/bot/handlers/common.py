"""src/bot/handlers/common.py."""

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.i18n import gettext as _
from src.bot.callbacks.language import LanguageCallback
from src.bot.callbacks.menu import MenuCallback
from src.bot.keyboards.inline.language import get_language_keyboard
from src.bot.keyboards.inline.start import get_start_keyboard
from src.database.models import BotUser

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    """
    Handles the /start command.
    Creates a new user in MongoDB if they don't exist.
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
    await query.message.edit_text(
        text=_("Welcome to Swipe! Select an action:"), reply_markup=get_start_keyboard()
    )


@router.callback_query(MenuCallback.filter(F.action == "cancel"))
async def cancel_action(query: CallbackQuery, state: FSMContext):
    """
    Universal state cancellation handler.
    Clears the current FSM state and returns to the main menu.
    """
    current_state = await state.get_state()
    if current_state is None:
        await query.answer(_("Nothing to cancel."))
        return
    await state.clear()
    await query.message.edit_text(
        text=_("Action canceled. Main menu:"), reply_markup=get_start_keyboard()
    )
