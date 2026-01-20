"""src/bot/ui_commands.py."""

import logging
from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeAllPrivateChats

logger = logging.getLogger(__name__)


async def set_ui_commands(bot: Bot):
    """
    Sets bot commands (Menu button) for different languages.
    """
    logger.info("Setting up UI commands...")

    commands_en = [
        BotCommand(command="start", description="Main Menu"),
        BotCommand(command="profile", description="My Profile"),
        BotCommand(command="help", description="Help"),
    ]

    await bot.set_my_commands(
        commands=commands_en, scope=BotCommandScopeAllPrivateChats()
    )
    logger.debug("Default (English) commands set.")

    commands_ru = [
        BotCommand(command="start", description="Главное меню"),
        BotCommand(command="profile", description="Мой профиль"),
        BotCommand(command="help", description="Помощь"),
    ]

    await bot.set_my_commands(
        commands=commands_ru, scope=BotCommandScopeAllPrivateChats(), language_code="ru"
    )
    logger.debug("Russian commands set.")
