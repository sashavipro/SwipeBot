"""src/bot/handlers/__init__.py"""

from aiogram import Router
from src.bot.handlers.common import router as common_router
from src.bot.handlers.auth.registration import router as reg_router
from src.bot.handlers.auth.login import router as login_router
from src.bot.handlers.auth.reset_password import router as reset_router

main_router = Router()

main_router.include_router(common_router)
main_router.include_router(reg_router)
main_router.include_router(login_router)
main_router.include_router(reset_router)
