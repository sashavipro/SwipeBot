"""src/infrastructure/api/base.py."""

import logging
from typing import Any, Dict, Optional
import httpx
from src.config import settings
from src.database.models import BotUser

logger = logging.getLogger(__name__)


class SwipeAPIError(Exception):
    """
    Base exception for API-related errors.
    """

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"API Error {status_code}: {message}")


class BaseAPIClient:
    """
    Base client handling HTTP transport, error parsing, and token management.
    """

    def __init__(self, user: Optional[BotUser] = None):
        self.base_url = settings.SWIPE_API_BASE_URL
        self.timeout = httpx.Timeout(10.0, connect=5.0)
        self.user = user

    async def _perform_request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        json: Optional[Dict] = None,
        data: Optional[Dict] = None,
        files: Optional[Dict] = None,
    ) -> Any:
        """
        Internal method to execute the raw HTTP request using httpx.
        """
        # verify=False is used for IP-based access without SSL certificate
        async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
            try:
                logger.debug("API Request: %s %s", method, url)
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=json,
                    data=data,
                    files=files,
                )

                if response.is_error:
                    logger.error(
                        "API Request failed: %s %s -> %s %s",
                        method,
                        url,
                        response.status_code,
                        response.text,
                    )
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("message", response.text)
                    except Exception:  # pylint: disable=broad-exception-caught
                        error_msg = response.text

                    raise SwipeAPIError(response.status_code, error_msg)

                return response.json()

            except httpx.RequestError as e:
                logger.critical("Failed to connect to Swipe API: %s", e)
                raise SwipeAPIError(503, "Service temporarily unavailable") from e

    async def make_request(
        self,
        method: str,
        endpoint: str,
        token: Optional[str] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        is_retry: bool = False,
    ) -> Any:
        """
        Executes a request with automatic token injection and refresh logic.
        """
        headers = {}

        current_token = token
        if not current_token and self.user:
            current_token = self.user.api_access_token

        if current_token:
            headers["Authorization"] = f"Bearer {current_token}"

        url = f"{self.base_url}{endpoint}"

        try:
            return await self._perform_request(method, url, headers, json, data, files)

        except SwipeAPIError as e:
            if (
                e.status_code == 401
                and not is_retry
                and self.user
                and self.user.api_refresh_token
            ):
                logger.info(
                    "Token expired for user %s. Refreshing...", self.user.telegram_id
                )

                try:
                    refresh_url = f"{self.base_url}/auth/refresh"
                    refresh_response = await self._perform_request(
                        "POST",
                        refresh_url,
                        headers={},
                        json={"refresh_token": self.user.api_refresh_token},
                    )

                    new_access = refresh_response["access_token"]
                    new_refresh = refresh_response["refresh_token"]

                    self.user.api_access_token = new_access
                    self.user.api_refresh_token = new_refresh
                    await self.user.save()

                    logger.info("Token refreshed successfully. Retrying request...")

                    return await self.make_request(
                        method,
                        endpoint,
                        token=None,
                        json=json,
                        data=data,
                        files=files,
                        is_retry=True,
                    )

                except Exception as refresh_error:
                    logger.error("Token refresh failed: %s", refresh_error)
                    raise SwipeAPIError(
                        401, "Session expired. Please login again."
                    ) from refresh_error

            raise e
