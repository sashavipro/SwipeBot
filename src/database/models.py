"""src/database/models.py."""

from typing import Optional
from beanie import Document
from pydantic import Field


# pylint: disable=too-many-ancestors
class BotUser(Document):
    """
    MongoDB document model representing a Telegram bot user.
    """

    telegram_id: int = Field(index=True, unique=True)
    username: Optional[str] = None
    full_name: str
    language_code: str = "ru"

    api_access_token: Optional[str] = None
    api_refresh_token: Optional[str] = None
    api_user_id: Optional[int] = None

    class Settings:
        """
        Beanie ODM settings for the BotUser document.
        """

        # pylint: disable=too-few-public-methods
        name = "users"
