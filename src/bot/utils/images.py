"""src/bot/utils/images.py."""

import base64
import io
from aiogram import Bot


async def encode_image_to_base64(bot: Bot, file_id: str) -> str:
    """
    Downloads an image from Telegram servers by file_id and converts it to a Base64 string.
    """
    file_io = io.BytesIO()
    await bot.download(file_id, destination=file_io)
    image_bytes = file_io.getvalue()
    base64_str = base64.b64encode(image_bytes).decode("utf-8")
    return base64_str
