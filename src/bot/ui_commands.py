"""src/bot/ui_commands.py."""

from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeAllPrivateChats


async def set_ui_commands(bot: Bot):
    """
    Sets bot commands (Menu button) for different languages.
    """

    commands_en = [
        BotCommand(command="start", description="Main Menu"),
        BotCommand(command="profile", description="My Profile"),
        BotCommand(command="help", description="Help"),
    ]

    await bot.set_my_commands(
        commands=commands_en, scope=BotCommandScopeAllPrivateChats()
    )

    commands_ru = [
        BotCommand(command="start", description="Главное меню"),
        BotCommand(command="profile", description="Мой профиль"),
        BotCommand(command="help", description="Помощь"),
    ]

    await bot.set_my_commands(
        commands=commands_ru, scope=BotCommandScopeAllPrivateChats(), language_code="ru"
    )
