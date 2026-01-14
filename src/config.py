"""src/config.py."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr


class Settings(BaseSettings):
    """
    Application configuration settings loaded from environment variables.
    """

    BOT_TOKEN: SecretStr

    MONGO_URL: str
    MONGO_DB_NAME: str

    REDIS_URL: str

    SWIPE_API_BASE_URL: str

    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )


settings = Settings()
