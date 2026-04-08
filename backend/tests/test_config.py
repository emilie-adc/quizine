import pytest
from pydantic import ValidationError


def test_settings_loads_from_env(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
    monkeypatch.setenv("UPLOADS_DIR", "./uploads")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:5173")

    from importlib import reload
    import backend.app.core.config as config_module
    reload(config_module)

    s = config_module.Settings()
    assert s.ANTHROPIC_API_KEY == "sk-ant-test"
    assert s.DATABASE_URL == "postgresql+asyncpg://user:pass@localhost/db"
    assert s.UPLOADS_DIR == "./uploads"
    assert s.CORS_ORIGINS == "http://localhost:5173"


def test_cors_origins_is_plain_string(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
    monkeypatch.setenv("UPLOADS_DIR", "./uploads")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")

    from importlib import reload
    import backend.app.core.config as config_module
    reload(config_module)

    s = config_module.Settings()
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
    from backend.app.core.config import Settings

    with pytest.raises(ValidationError):
        Settings(_env_file=None)
