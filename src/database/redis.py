"""src/database/redis.py."""

from redis.asyncio import Redis
from src.config import settings


def get_redis_client() -> Redis:
    """
    Creates and returns an asynchronous Redis client instance.
    """
    return Redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )
