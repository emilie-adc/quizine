import functools

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    ANTHROPIC_API_KEY: str
    DATABASE_URL: str
    UPLOADS_DIR: str
    CORS_ORIGINS: str


@functools.lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
