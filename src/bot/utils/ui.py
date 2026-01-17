"""src/bot/utils/ui.py."""

from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.utils.i18n import gettext as _
from src.bot.keyboards.inline import get_start_keyboard


async def remove_reply_keyboard(message: Message):
    """
    Silently removes the ReplyKeyboard by sending a temporary message and deleting it.
    """
    msg = await message.answer("...", reply_markup=ReplyKeyboardRemove())
    await msg.delete()


async def handle_cancel(message: Message, state: FSMContext) -> bool:
    """
    Checks if the message is a 'Cancel' command.
    """
    if message.text == _("Cancel") or message.text == _("Cancel Registration"):
        await state.clear()
        await remove_reply_keyboard(message)
        await message.answer(_("Main Menu:"), reply_markup=get_start_keyboard())
        return True
    return False


async def cleanup_last_step(state: FSMContext, message: Message = None):
    """
    Deletes the previous bot message stored in state and the user's message.
    """
    data = await state.get_data()
    last_msg_id = data.get("last_bot_msg_id")

    if last_msg_id and message:
        try:
            await message.bot.delete_message(
                chat_id=message.chat.id, message_id=last_msg_id
            )
        except Exception:  # pylint: disable=broad-exception-caught
            pass

    if message:
        try:
            await message.delete()
        except Exception:  # pylint: disable=broad-exception-caught
            pass
