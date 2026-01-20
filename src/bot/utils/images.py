"""src/bot/utils/images.py."""

import base64
import io
import logging
from aiogram import Bot

logger = logging.getLogger(__name__)


async def encode_image_to_base64(bot: Bot, file_id: str) -> str:
    """
    Downloads an image from Telegram servers by file_id and converts it to a Base64 string.
    """
    logger.debug("Downloading image with file_id: %s", file_id)
    file_io = io.BytesIO()

    await bot.download(file_id, destination=file_io)

    image_bytes = file_io.getvalue()
    base64_str = base64.b64encode(image_bytes).decode("utf-8")

    logger.debug("Image converted to base64 (length: %d)", len(base64_str))
    return base64_str
