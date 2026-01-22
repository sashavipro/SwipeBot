"""src/bot/callbacks/listings.py."""

from typing import Optional
from aiogram.filters.callback_data import CallbackData


class ListingCallback(CallbackData, prefix="lst"):
    """
    Callback for listing navigation.
    action: next, prev, geo
    """

    action: str
    id: Optional[int] = None
