"""src/bot/handlers/menu.py."""

from aiogram.types import Message
from src.database.models import BotUser
from src.infrastructure import SwipeApiClient, SwipeAPIError


async def show_profile(message: Message, user: BotUser):
    """
    Fetches and displays the user's profile information from the API.
    """
    api = SwipeApiClient()
    try:
        profile_data = await api.users.get_my_profile(token=user.api_access_token)

        await message.answer(f"Hello, {profile_data['first_name']}!")
    except SwipeAPIError as e:
        if e.status_code == 401:
            await message.answer("Your session has expired. Please log in again.")
        else:
            await message.answer("An error occurred while receiving data.")
