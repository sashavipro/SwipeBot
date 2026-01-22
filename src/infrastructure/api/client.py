"""src/infrastructure/api/client.py."""

from typing import Optional
from src.database.models import BotUser
from src.infrastructure.api.base import BaseAPIClient
from src.infrastructure.api.resources import (
    AuthResource,
    UsersResource,
    AnnouncementsResource,
)


class SwipeApiClient(BaseAPIClient):
    """
    Main entry point for Swipe API interactions.
    Aggregates specific resources (auth, users, announcements) and
    inherits base logic (http, token refresh) from BaseAPIClient.
    """

    # pylint: disable=too-few-public-methods
    def __init__(self, user: Optional[BotUser] = None):
        super().__init__(user)
        self.auth = AuthResource(self)
        self.users = UsersResource(self)
        self.announcements = AnnouncementsResource(self)
