"""src/infrastructure/api/resources/announcement.py."""

from typing import Dict, Any, List


class AnnouncementsResource:
    """
    Handles announcements API calls.
    """

    def __init__(self, client):
        self.client = client

    async def get_announcements(
        self, limit: int = 10, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Fetches paginated announcements.
        """
        params = f"?limit={limit}&offset={offset}"
        return await self.client.make_request("GET", f"/announcements/{params}")

    async def get_my_announcements(
        self, limit: int = 10, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Fetches announcements created by the current user.
        """
        params = f"?limit={limit}&offset={offset}"
        return await self.client.make_request("GET", f"/announcements/my{params}")

    async def create_announcement(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Creates a new announcement."""
        return await self.client.make_request("POST", "/announcements/", json=data)
