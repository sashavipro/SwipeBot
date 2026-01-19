"""src/bot/states/profile.py."""

from aiogram.fsm.state import State, StatesGroup

# pylint: disable=too-few-public-methods


class ProfileSG(StatesGroup):
    """
    FSM states for Profile viewing.
    """

    Viewing = State()
