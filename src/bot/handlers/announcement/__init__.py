"""src/bot/handlers/announcement/__init__.py."""

from aiogram import Router
from .get_announcement import router as get_announcement_router
from .create_announcement import router as create_announcement_router


router = Router()

router.include_router(get_announcement_router)
router.include_router(create_announcement_router)

__all__ = ["router"]
