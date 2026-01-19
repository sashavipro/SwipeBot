"""src/bot/states/listings.py."""

from aiogram.fsm.state import State, StatesGroup

# pylint: disable=too-few-public-methods


class ListingsSG(StatesGroup):
    """
    FSM states for browsing listings.
    """

    Browsing = State()
