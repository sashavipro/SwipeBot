"""src/infrastructure/api/resources/__init__.py."""

from .announcement import AnnouncementsResource
from .auth import AuthResource
from .users import UsersResource

__all__ = ["AnnouncementsResource", "AuthResource", "UsersResource"]
