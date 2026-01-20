"""src/infrastructure/api/resources/announcement.py."""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class AnnouncementsResource:
    """
    Handles announcements API calls.
    """

    def __init__(self, client):
        self.client = client

    async def get_announcements(
        self, token: str, limit: int = 10, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Fetches paginated announcements.
        """
        logger.debug("Fetching announcements: limit=%s, offset=%s", limit, offset)
        params = f"?limit={limit}&offset={offset}"
        return await self.client.make_request(
            "GET", f"/announcements/{params}", token=token
        )

    async def create_announcement(
        self, token: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Creates a new announcement.
        """
        logger.info("Creating new announcement")
        return await self.client.make_request(
            "POST", "/announcements/", token=token, json=data
        )

    async def get_my_announcements(
        self, token: str, limit: int = 10, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Fetches announcements created by the current user.
        """
        logger.debug(
            "Fetching user's announcements: limit=%s, offset=%s", limit, offset
        )
        params = f"?limit={limit}&offset={offset}"
        return await self.client.make_request(
            "GET", f"/announcements/my{params}", token=token
        )
