"""src/bot/handlers/__init__.py"""

from aiogram import Router

from .common import router as common_router
from .auth import router as auth_router
from .menu import router as menu_router
from .announcement import router as announcement_router

main_router = Router()

main_router.include_router(auth_router)
main_router.include_router(common_router)
main_router.include_router(menu_router)
main_router.include_router(announcement_router)

__all__ = ["main_router"]
