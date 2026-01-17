"""src/bot/handlers/menu.py."""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.i18n import gettext as _

from src.bot.callbacks import MenuCallback
from src.bot.utils.api import execute_with_refresh
from src.database import BotUser
from src.infrastructure.api import SwipeApiClient, SwipeAPIError

router = Router()


@router.callback_query(MenuCallback.filter(F.action == "profile"))
async def show_profile_callback(query: CallbackQuery, user: BotUser):
    """
    Handles 'My Profile' button click.
    """
    await _show_profile_logic(query.message, user)
    await query.answer()


@router.message(Command("profile"))
async def show_profile_command(message: Message, user: BotUser):
    """
    Handles /profile command.
    """
    await _show_profile_logic(message, user)


async def _show_profile_logic(message: Message, user: BotUser):
    """
    Reusable logic for fetching and showing profile.
    """
    api = SwipeApiClient()
    try:
        profile_data = await execute_with_refresh(user, api.users.get_my_profile)
        await message.answer(
            text=_(
                "**Your Profile:**\n\n"
                "Name: {first} {last}\nEmail: {email}\nPhone: {phone}"
            ).format(
                first=profile_data["first_name"],
                last=profile_data["last_name"],
                email=profile_data["email"],
                phone=profile_data["phone"],
            )
        )
    except SwipeAPIError as e:
        if e.status_code == 401:
            await message.answer(_("Your session has expired. Please log in again."))
        else:
            await message.answer(
                _("An error occurred: {error}").format(error=e.message)
            )


@router.callback_query(MenuCallback.filter(F.action == "listings"))
async def show_listings(query: CallbackQuery):
    """
    Handles 'Listings' button click.
    """
    await query.answer()
    await query.message.answer(_("Listings feature is under construction!"))


@router.callback_query(MenuCallback.filter(F.action == "create_listing"))
async def create_listing(query: CallbackQuery):
    """
    Handles 'Create Listing' button click.
    """
    await query.answer()
    await query.message.answer(_("Create Listing feature is under construction!"))
