"""
T14 deck endpoint tests — SQLite in-memory, no Anthropic calls.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.base import Base
import app.models  # noqa: F401


@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_engine):
    """FastAPI test client with SQLite override."""
    from app.main import app
    from app.core.database import get_db

    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ── POST /decks ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_deck_custom(client: AsyncClient):
    resp = await client.post("/decks", json={"title": "My ML Deck", "custom_cert_name": "ML Basics"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "My ML Deck"
    assert body["custom_cert_name"] == "ML Basics"
    assert body["cert_id"] is None
    assert "id" in body


@pytest.mark.asyncio
async def test_create_deck_no_cert(client: AsyncClient):
    """Deck without cert_id or custom_cert_name is allowed."""
    resp = await client.post("/decks", json={"title": "Bare Deck"})
    assert resp.status_code == 201
    assert resp.json()["cert_id"] is None
    assert resp.json()["custom_cert_name"] is None


@pytest.mark.asyncio
async def test_create_deck_both_cert_sources_rejected(client: AsyncClient):
    resp = await client.post(
        "/decks",
        json={"title": "Bad", "cert_id": 1, "custom_cert_name": "Something"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_deck_invalid_cert_id(client: AsyncClient):
    resp = await client.post("/decks", json={"title": "Ghost", "cert_id": 9999})
    assert resp.status_code == 404


# ── GET /decks ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_decks_empty(client: AsyncClient):
    resp = await client.get("/decks")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_list_decks_returns_created(client: AsyncClient):
    await client.post("/decks", json={"title": "Deck A", "custom_cert_name": "Cert A"})
    await client.post("/decks", json={"title": "Deck B", "custom_cert_name": "Cert B"})
    resp = await client.get("/decks")
    assert resp.status_code == 200
    titles = [d["title"] for d in resp.json()]
    assert "Deck A" in titles
    assert "Deck B" in titles


# ── GET /decks/{id} ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_deck_detail(client: AsyncClient):
    create_resp = await client.post(
        "/decks", json={"title": "Detail Deck", "custom_cert_name": "Some Cert"}
    )
    deck_id = create_resp.json()["id"]

    resp = await client.get(f"/decks/{deck_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == deck_id
    assert body["title"] == "Detail Deck"
    assert body["card_count"] == 0
    assert body["cert_slug"] is None


@pytest.mark.asyncio
async def test_get_deck_not_found(client: AsyncClient):
    resp = await client.get("/decks/99999")
    assert resp.status_code == 404
