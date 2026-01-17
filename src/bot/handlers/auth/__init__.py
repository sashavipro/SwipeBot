"""src/bot/handlers/auth/__init__.py."""

from aiogram import Router
from .login import router as login_router
from .registration import router as registration_router
from .reset_password import router as reset_password_router


router = Router()

router.include_router(login_router)
router.include_router(registration_router)
router.include_router(reset_password_router)

__all__ = ["router"]
