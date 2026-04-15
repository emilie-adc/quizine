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


def parse_cors_origins(origins_str: str) -> list[str]:
    """Split a comma-separated CORS origins string, stripping whitespace and empty entries."""
    return [o.strip() for o in origins_str.split(",") if o.strip()]
