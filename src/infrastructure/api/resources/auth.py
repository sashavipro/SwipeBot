"""src/infrastructure/api/resources/auth.py."""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class AuthResource:
    """
    Handles authentication-related API calls.
    """

    def __init__(self, client):
        self.client = client

    async def login(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticates a user."""
        logger.info("Authenticating user: %s", email)
        return await self.client.make_request(
            "POST", "/auth/login", json={"email": email, "password": password}
        )

    async def register(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Initiates user registration."""
        logger.info("Initiating registration for user")
        return await self.client.make_request("POST", "/auth/register", json=user_data)

    async def verify_registration(self, email: str, code: str) -> Dict[str, Any]:
        """Verifies registration code."""
        logger.info("Verifying registration code for: %s", email)
        return await self.client.make_request(
            "POST", "/auth/verify", json={"email": email, "code": code}
        )

    async def forgot_password(self, email: str) -> Dict[str, Any]:
        """Requests password reset."""
        logger.info("Requesting password reset for: %s", email)
        return await self.client.make_request(
            "POST", "/auth/forgot-password", json={"email": email}
        )

    async def reset_password(self, token: str, new_password: str) -> Dict[str, Any]:
        """Sets new password."""
        logger.info("Resetting password with token")
        return await self.client.make_request(
            "POST",
            "/auth/reset-password",
            json={"token": token, "new_password": new_password},
        )

    async def refresh_tokens(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refreshes the access token using the refresh token.
        Endpoint: POST /auth/refresh
        """
        logger.debug("Refreshing access token")
        return await self.client.make_request(
            "POST", "/auth/refresh", json={"refresh_token": refresh_token}
        )
