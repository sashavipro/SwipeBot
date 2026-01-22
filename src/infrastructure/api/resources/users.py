"""src/infrastructure/api/resources/users.py."""

from typing import Dict, Any


# pylint: disable=too-few-public-methods
class UsersResource:
    """
    Handles user profile-related API calls.
    """

    def __init__(self, client):
        self.client = client

    async def get_my_profile(self) -> Dict[str, Any]:
        """Retrieves current user profile."""
        # Token is handled automatically by the client
        return await self.client.make_request("GET", "/users/me")
