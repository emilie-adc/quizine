import functools
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding="utf-8")

    ANTHROPIC_API_KEY: str
    DATABASE_URL: str
    UPLOADS_DIR: str
    CORS_ORIGINS: str


@functools.lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
