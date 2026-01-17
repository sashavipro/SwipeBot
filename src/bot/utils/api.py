"""src/bot/utils/api.py."""

from typing import Callable, Any
from src.database import BotUser
from src.infrastructure.api import SwipeAPIError
from src.infrastructure.api import SwipeApiClient


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
            raise e

        try:
            new_tokens = await api.auth.refresh_tokens(user.api_refresh_token)

            user.api_access_token = new_tokens["access_token"]
            user.api_refresh_token = new_tokens["refresh_token"]
            await user.save()

            return await func(token=user.api_access_token, **kwargs)

        except SwipeAPIError as refresh_error:
            raise SwipeAPIError(401, "Session expired completely") from refresh_error
