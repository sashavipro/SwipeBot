"""src/bot/utils/ui.py."""

import logging
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.utils.i18n import gettext as _
from src.bot.keyboards.inline import get_start_keyboard

logger = logging.getLogger(__name__)


async def remove_reply_keyboard(message: Message):
    """
    Silently removes the ReplyKeyboard by sending a temporary message and deleting it.
    """
    try:
        msg = await message.answer("...", reply_markup=ReplyKeyboardRemove())
        await msg.delete()
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.debug("Failed to remove reply keyboard: %s", e)


async def handle_cancel(message: Message, state: FSMContext) -> bool:
    """
    Checks if the message is a 'Cancel' command.
    """
    if message.text == _("Cancel") or message.text == _("Cancel Registration"):
        logger.info("User %s canceled action via UI", message.from_user.id)
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
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Debug level because deleting old messages often fails and it's not critical
            logger.debug("Failed to delete bot message %s: %s", last_msg_id, e)

    if message:
        try:
            await message.delete()
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.debug("Failed to delete user message %s: %s", message.message_id, e)
