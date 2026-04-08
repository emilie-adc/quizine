import json
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MCQ_PAYLOAD = json.dumps([
    {
        "question": "What is Delta Lake?",
        "options": ["A storage layer", "A compute engine", "A scheduler", "A catalogue"],
        "correct_index": 0,
        "topic_tag": "delta-lake",
    },
    {
        "question": "Which format does Delta Lake use?",
        "options": ["CSV", "Parquet", "JSON", "ORC"],
        "correct_index": 1,
        "topic_tag": "delta-lake",
    },
])

FLASHCARD_PAYLOAD = json.dumps([
    {"front": "What is Delta Lake?", "back": "An open storage layer built on Parquet.", "topic_tag": "delta-lake"},
    {"front": "What is Unity Catalog?", "back": "A unified governance solution for data.", "topic_tag": "unity-catalog"},
])


def _make_stream_mock(payload: str):
    """Return a mock that behaves like client.messages.stream() context manager."""

    async def _text_stream():
        # Yield payload in two chunks to exercise the streaming path
        mid = len(payload) // 2
        yield payload[:mid]
        yield payload[mid:]

    mock_stream = MagicMock()
    mock_stream.text_stream = _text_stream()

    @asynccontextmanager
    async def _stream_ctx(*args, **kwargs):
        yield mock_stream

    mock_client = MagicMock()
    mock_client.messages.stream = _stream_ctx
    return mock_client


def _parse_sse(content: bytes) -> str:
    """Reassemble the JSON string from SSE data lines."""
    result = []
    for line in content.decode().splitlines():
        if line.startswith("data: ") and line != "data: [DONE]":
            delta = json.loads(line[len("data: "):]).get("delta", "")
            result.append(delta)
    return "".join(result)


# ---------------------------------------------------------------------------
# MCQ tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_mcq_response_shape():
    with patch("app.services.generation.client", _make_stream_mock(MCQ_PAYLOAD)):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/generate/mcq", json={"text": "Study material here."})

    assert response.status_code == 200
    questions = json.loads(_parse_sse(response.content))
    assert isinstance(questions, list)
    for q in questions:
        assert set(q.keys()) == {"question", "options", "correct_index", "topic_tag"}


@pytest.mark.asyncio
async def test_mcq_exactly_four_options():
    with patch("app.services.generation.client", _make_stream_mock(MCQ_PAYLOAD)):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/generate/mcq", json={"text": "Study material here."})

    questions = json.loads(_parse_sse(response.content))
    for q in questions:
        assert len(q["options"]) == 4


@pytest.mark.asyncio
async def test_mcq_exactly_one_correct_answer():
    with patch("app.services.generation.client", _make_stream_mock(MCQ_PAYLOAD)):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/generate/mcq", json={"text": "Study material here."})

    questions = json.loads(_parse_sse(response.content))
    for q in questions:
        assert isinstance(q["correct_index"], int)
        assert 0 <= q["correct_index"] <= 3


# ---------------------------------------------------------------------------
# Flashcard tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_flashcard_response_shape():
    with patch("app.services.generation.client", _make_stream_mock(FLASHCARD_PAYLOAD)):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/generate/flashcards", json={"text": "Study material here."})

    assert response.status_code == 200
    cards = json.loads(_parse_sse(response.content))
    assert isinstance(cards, list)
    for card in cards:
        assert set(card.keys()) == {"front", "back", "topic_tag"}


@pytest.mark.asyncio
async def test_flashcard_has_non_empty_fields():
    with patch("app.services.generation.client", _make_stream_mock(FLASHCARD_PAYLOAD)):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/generate/flashcards", json={"text": "Study material here."})

    cards = json.loads(_parse_sse(response.content))
    for card in cards:
        assert card["front"]
        assert card["back"]
        assert card["topic_tag"]
