"""src/infrastructure/api/client.py."""

import logging
from src.infrastructure.api.base import BaseAPIClient
from src.infrastructure.api.resources import (
    AuthResource,
    UsersResource,
    AnnouncementsResource,
)

logger = logging.getLogger(__name__)


class SwipeApiClient(BaseAPIClient):
    """
    Main entry point for Swipe API interactions.
    Aggregates specific resources (auth, users, marketplace).
    """

    # pylint: disable=too-few-public-methods
    def __init__(self):
        logger.debug("Initializing SwipeApiClient and resources...")
        super().__init__()
        self.auth = AuthResource(self)
        self.users = UsersResource(self)
        self.announcements = AnnouncementsResource(self)
