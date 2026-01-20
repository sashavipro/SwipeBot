"""src/infrastructure/api/base.py."""

import logging
from typing import Any, Dict, Optional
import httpx
from src.config import settings

logger = logging.getLogger(__name__)


class SwipeAPIError(Exception):
    """Base exception for API-related errors."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"API Error {status_code}: {message}")


class BaseAPIClient:
    """
    Low-level HTTP client handling connection and error logic.
    """

    # pylint: disable=too-few-public-methods
    def __init__(self):
        self.base_url = settings.SWIPE_API_BASE_URL
        self.timeout = httpx.Timeout(10.0, connect=5.0)

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    async def make_request(
        self,
        method: str,
        endpoint: str,
        token: Optional[str] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Executes a generic HTTP request.
        """
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        url = f"{self.base_url}{endpoint}"

        logger.debug("API Request: %s %s", method, url)

        async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=json,
                    data=data,
                    files=files,
                )

                logger.debug(
                    "API Response: %s %s -> Status: %s",
                    method,
                    url,
                    response.status_code,
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
