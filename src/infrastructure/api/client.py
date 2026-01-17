"""src/infrastructure/api/client.py."""

from src.infrastructure.api.base import BaseAPIClient
from src.infrastructure.api.resources import (
    AuthResource,
    UsersResource,
    AnnouncementsResource,
)


class SwipeApiClient(BaseAPIClient):
    """
    Main entry point for Swipe API interactions.
    Aggregates specific resources (auth, users, marketplace).
    """

    # pylint: disable=too-few-public-methods
    def __init__(self):
        super().__init__()
        self.auth = AuthResource(self)
        self.users = UsersResource(self)
        self.announcements = AnnouncementsResource(self)
