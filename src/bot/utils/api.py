"""src/bot/utils/api.py."""

import logging
from typing import Callable, Any
from src.database import BotUser
from src.infrastructure.api import SwipeAPIError
from src.infrastructure.api import SwipeApiClient

logger = logging.getLogger(__name__)


async def execute_with_refresh(user: BotUser, func: Callable, **kwargs) -> Any:
    """
    Executes an API call with automatic token refresh on 401 error.
    If the access token is invalid, it attempts to use the refresh token
    to get new credentials and retry the original request.
    """
    api = SwipeApiClient()
    try:
        return await func(token=user.api_access_token, **kwargs)

    except SwipeAPIError as e:
        if e.status_code != 401:
            raise e

        if not user.api_refresh_token:
            logger.warning("User %s has no refresh token", user.telegram_id)
            raise e

        logger.info(
            "Access token expired for user %s. Attempting refresh...", user.telegram_id
        )

        try:
            new_tokens = await api.auth.refresh_tokens(user.api_refresh_token)

            user.api_access_token = new_tokens["access_token"]
            user.api_refresh_token = new_tokens["refresh_token"]
            await user.save()

            logger.info("Token refresh successful for user %s", user.telegram_id)
            return await func(token=user.api_access_token, **kwargs)

        except SwipeAPIError as refresh_error:
            logger.error(
                "Token refresh failed for user %s: %s",
                user.telegram_id,
                refresh_error,
            )
            raise SwipeAPIError(401, "Session expired completely") from refresh_error
