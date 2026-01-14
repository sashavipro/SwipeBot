"""src/bot/states/auth.py."""

from aiogram.fsm.state import State, StatesGroup

# pylint: disable=too-few-public-methods


class LoginSG(StatesGroup):
    """
    Finite State Machine (FSM) states for the User Login flow.
    """

    InputEmail = State()
    InputPassword = State()


class ResetPasswordSG(StatesGroup):
    """
    Finite State Machine (FSM) states for the Password Reset flow.
    """

    InputEmail = State()
    InputToken = State()
    InputNewPassword = State()


class RegistrationSG(StatesGroup):
    """
    Finite State Machine (FSM) states for the User Registration flow.
    """

    InputFirstName = State()
    InputLastName = State()
    InputEmail = State()
    InputPhone = State()
    InputPassword = State()
    InputCode = State()
