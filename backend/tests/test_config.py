import pytest
from pydantic import ValidationError


def test_settings_loads_from_env(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
    monkeypatch.setenv("UPLOADS_DIR", "./uploads")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:5173")

    from app.core.config import Settings

    s = Settings()
    assert s.ANTHROPIC_API_KEY == "sk-ant-test"
    assert s.DATABASE_URL == "postgresql+asyncpg://user:pass@localhost/db"
    assert s.UPLOADS_DIR == "./uploads"
    assert s.CORS_ORIGINS == "http://localhost:5173"


def test_cors_origins_is_plain_string(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
    monkeypatch.setenv("UPLOADS_DIR", "./uploads")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")

    from app.core.config import Settings

    s = Settings()
    origins = s.CORS_ORIGINS.split(",")
    assert origins == ["http://localhost:5173", "http://localhost:3000"]


def test_settings_missing_required_field(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
    monkeypatch.setenv("UPLOADS_DIR", "./uploads")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:5173")

    # Import the class directly; instantiation reads env at call time.
    # Pass _env_file=None so pydantic-settings doesn't fall back to the .env file
    # (which may contain a real key and would mask the missing-field error).
    from app.core.config import Settings

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_cors_origins_normalisation(monkeypatch):
    """parse_cors_origins() strips whitespace and drops empty entries."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
    monkeypatch.setenv("UPLOADS_DIR", "./uploads")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:5173, http://localhost:3000, ")

    from app.core.config import Settings, parse_cors_origins

    s = Settings()
    origins = parse_cors_origins(s.CORS_ORIGINS)
    assert origins == ["http://localhost:5173", "http://localhost:3000"]


def test_get_settings_is_cached(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
    monkeypatch.setenv("UPLOADS_DIR", "./uploads")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:5173")

    from app.core.config import get_settings

    get_settings.cache_clear()
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2
    get_settings.cache_clear()
