"""src/bot/states/announcement.py."""

from aiogram.fsm.state import State, StatesGroup

# pylint: disable=too-few-public-methods


class CreateAnnouncementSG(StatesGroup):
    """
    Finite State Machine (FSM) states for creating a new announcement.
    """

    InputAddress = State()
    InputApartmentNumber = State()
    InputPrice = State()
    InputArea = State()
    InputDescription = State()
    InputLocation = State()
    InputImages = State()
