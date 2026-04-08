"""
T15 card endpoint tests — SQLite in-memory.
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


@pytest_asyncio.fixture
async def deck_and_card(client: AsyncClient):
    """Create a deck and a flashcard, return (deck_id, card_id)."""
    deck_resp = await client.post("/decks", json={"title": "Test Deck", "custom_cert_name": "Test"})
    deck_id = deck_resp.json()["id"]

    # Insert a card directly via the DB session (bypass generation)
    from app.models.cards import Card
    from app.core.database import get_db
    from app.main import app

    override = app.dependency_overrides[get_db]
    card_id = None
    async for db in override():
        card = Card(deck_id=deck_id, type="flashcard", front="Q", back="A")
        db.add(card)
        await db.commit()
        await db.refresh(card)
        card_id = card.id
        break

    return deck_id, card_id


# ── PATCH /cards/{id} ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_patch_card_front(client: AsyncClient, deck_and_card):
    _, card_id = deck_and_card
    resp = await client.patch(f"/cards/{card_id}", json={"front": "Updated Q"})
    assert resp.status_code == 200
    assert resp.json()["front"] == "Updated Q"
    assert resp.json()["back"] == "A"  # unchanged


@pytest.mark.asyncio
async def test_patch_card_not_found(client: AsyncClient):
    resp = await client.patch("/cards/99999", json={"front": "X"})
    assert resp.status_code == 404


# ── DELETE /cards/{id} ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_card(client: AsyncClient, deck_and_card):
    _, card_id = deck_and_card
    resp = await client.delete(f"/cards/{card_id}")
    assert resp.status_code == 204

    # Confirm gone
    resp2 = await client.patch(f"/cards/{card_id}", json={"front": "X"})
    assert resp2.status_code == 404


@pytest.mark.asyncio
async def test_delete_card_not_found(client: AsyncClient):
    resp = await client.delete("/cards/99999")
    assert resp.status_code == 404


# ── POST /cards/{id}/approve ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_approve_card(client: AsyncClient, deck_and_card):
    _, card_id = deck_and_card
    resp = await client.post(f"/cards/{card_id}/approve")
    assert resp.status_code == 200
    assert resp.json()["approved"] is True


@pytest.mark.asyncio
async def test_approve_card_not_found(client: AsyncClient):
    resp = await client.post("/cards/99999/approve")
    assert resp.status_code == 404
