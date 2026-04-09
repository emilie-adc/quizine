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
"""Tests for the /generate/mcq and /generate/flashcards endpoints and the generation service.

All Anthropic API calls are mocked; no network access is required.
"""
import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

# Ensure required env vars exist before the app is first imported.
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
os.environ.setdefault("UPLOADS_DIR", "./uploads")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:5173")

# ---------------------------------------------------------------------------
# Helpers / shared fixtures
# ---------------------------------------------------------------------------

_SAMPLE_QUESTIONS: list[dict] = [
    {
        "question": "What is Delta Lake?",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "correct_index": 0,
        "topic_tag": "Delta Lake",
    },
    {
        "question": "What is Unity Catalog?",
        "options": ["Option W", "Option X", "Option Y", "Option Z"],
        "correct_index": 2,
        "topic_tag": "Unity Catalog",
    },
]

_SAMPLE_FLASHCARDS: list[dict] = [
    {
        "front": "What is Delta Lake?",
        "back": "An open-source storage layer that brings reliability to data lakes.",
        "topic_tag": "Delta Lake",
    },
    {
        "front": "What is Unity Catalog?",
        "back": "A unified governance solution for all data assets in Databricks.",
        "topic_tag": "Unity Catalog",
    },
]


class _MockStream:
    """Async context manager that mimics the Anthropic streaming response."""

    def __init__(self, chunks: list[str]) -> None:
        self._chunks = chunks

    async def __aenter__(self) -> "_MockStream":
        return self

    async def __aexit__(self, *args: object) -> None:
        pass

    @property
    def text_stream(self):
        return self._iter_chunks()

    async def _iter_chunks(self):
        for chunk in self._chunks:
            yield chunk


@pytest.fixture()
def sample_questions() -> list[dict]:
    return list(_SAMPLE_QUESTIONS)


@pytest.fixture()
def sample_flashcards() -> list[dict]:
    return list(_SAMPLE_FLASHCARDS)


@pytest.fixture()
def non_stream_mock(sample_questions: list[dict]):
    """Patch _get_client so messages.create returns sample questions as JSON."""
    raw_json = json.dumps(sample_questions)
    content_block = MagicMock()
    content_block.text = raw_json
    message = MagicMock()
    message.content = [content_block]

    anthropic_client = MagicMock()
    anthropic_client.messages.create = AsyncMock(return_value=message)

    with patch("app.services.generation._get_client", return_value=anthropic_client):
        yield anthropic_client


@pytest.fixture()
def non_stream_flashcard_mock(sample_flashcards: list[dict]):
    """Patch _get_client so messages.create returns sample flashcards as JSON."""
    raw_json = json.dumps(sample_flashcards)
    content_block = MagicMock()
    content_block.text = raw_json
    message = MagicMock()
    message.content = [content_block]

    anthropic_client = MagicMock()
    anthropic_client.messages.create = AsyncMock(return_value=message)

    with patch("app.services.generation._get_client", return_value=anthropic_client):
        yield anthropic_client


@pytest.fixture()
def stream_mock(sample_questions: list[dict]):
    """Patch _get_client so messages.stream yields sample questions in two chunks."""
    raw_json = json.dumps(sample_questions)
    mid = len(raw_json) // 2
    chunks = [raw_json[:mid], raw_json[mid:]]

    anthropic_client = MagicMock()
    anthropic_client.messages.stream = MagicMock(return_value=_MockStream(chunks))

    with patch("app.services.generation._get_client", return_value=anthropic_client):
        yield anthropic_client


@pytest.fixture()
def stream_flashcard_mock(sample_flashcards: list[dict]):
    """Patch _get_client so messages.stream yields sample flashcards in two chunks."""
    raw_json = json.dumps(sample_flashcards)
    mid = len(raw_json) // 2
    chunks = [raw_json[:mid], raw_json[mid:]]

    anthropic_client = MagicMock()
    anthropic_client.messages.stream = MagicMock(return_value=_MockStream(chunks))

    with patch("app.services.generation._get_client", return_value=anthropic_client):
        yield anthropic_client


@pytest.fixture()
def app():
    from app.main import app as _app

    return _app


# ---------------------------------------------------------------------------
# Non-streaming endpoint tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_non_streaming_status_200(non_stream_mock, app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/generate/mcq",
            json={"text": "Study material", "stream": False},
        )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_non_streaming_returns_list(non_stream_mock, app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/generate/mcq",
            json={"text": "Study material", "stream": False},
        )
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_non_streaming_required_keys(non_stream_mock, app):
    """Every question object must contain the four required keys."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/generate/mcq",
            json={"text": "Study material", "stream": False},
        )
    required_keys = {"question", "options", "correct_index", "topic_tag"}
    for q in resp.json():
        assert required_keys.issubset(q.keys())


@pytest.mark.asyncio
async def test_non_streaming_exactly_four_options(non_stream_mock, app):
    """Each question must have exactly 4 options."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/generate/mcq",
            json={"text": "Study material", "stream": False},
        )
    for q in resp.json():
        assert len(q["options"]) == 4


@pytest.mark.asyncio
async def test_non_streaming_correct_index_in_range(non_stream_mock, app):
    """correct_index must be an integer in [0, 3] - exactly one correct answer."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/generate/mcq",
            json={"text": "Study material", "stream": False},
        )
    for q in resp.json():
        assert isinstance(q["correct_index"], int)
        assert 0 <= q["correct_index"] <= 3


# ---------------------------------------------------------------------------
# Streaming endpoint tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_streaming_content_type(stream_mock, app):
    """Streaming endpoint must respond with text/event-stream."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/generate/mcq",
            json={"text": "Study material", "stream": True},
        )
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]


@pytest.mark.asyncio
async def test_streaming_sse_delta_format(stream_mock, app):
    """All non-terminal SSE events must be JSON objects containing a delta key."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/generate/mcq",
            json={"text": "Study material", "stream": True},
        )
    events = [e for e in resp.text.strip().split("\n\n") if e]
    for event in events[:-1]:
        assert event.startswith("data: ")
        payload = json.loads(event[len("data: "):])
        assert "delta" in payload


@pytest.mark.asyncio
async def test_streaming_ends_with_done(stream_mock, app):
    """The final SSE event must be data: [DONE]."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/generate/mcq",
            json={"text": "Study material", "stream": True},
        )
    events = [e for e in resp.text.strip().split("\n\n") if e]
    assert events[-1] == "data: [DONE]"


# ---------------------------------------------------------------------------
# Request validation tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_request_missing_text_returns_422(app):
    """Omitting the required text field must yield HTTP 422."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/generate/mcq", json={"stream": False})
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Error handling in the generation service
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_service_raises_on_invalid_json():
    """generate_mcq raises ValueError when Anthropic returns non-JSON text."""
    content_block = MagicMock()
    content_block.text = "not valid json {{{"
    message = MagicMock()
    message.content = [content_block]

    anthropic_client = MagicMock()
    anthropic_client.messages.create = AsyncMock(return_value=message)

    with patch("app.services.generation._get_client", return_value=anthropic_client):
        from app.services.generation import generate_mcq

        with pytest.raises(ValueError, match="invalid JSON"):
            await generate_mcq("text", None, 1)


@pytest.mark.asyncio
async def test_service_raises_on_empty_content():
    """generate_mcq raises ValueError when Anthropic returns empty content."""
    message = MagicMock()
    message.content = []

    anthropic_client = MagicMock()
    anthropic_client.messages.create = AsyncMock(return_value=message)

    with patch("app.services.generation._get_client", return_value=anthropic_client):
        from app.services.generation import generate_mcq

        with pytest.raises(ValueError, match="empty response"):
            await generate_mcq("text", None, 1)


@pytest.mark.asyncio
async def test_service_raises_on_non_list_json():
    """generate_mcq raises ValueError when Anthropic returns a JSON object not a list."""
    content_block = MagicMock()
    content_block.text = '{"question": "test"}'
    message = MagicMock()
    message.content = [content_block]

    anthropic_client = MagicMock()
    anthropic_client.messages.create = AsyncMock(return_value=message)

    with patch("app.services.generation._get_client", return_value=anthropic_client):
        from app.services.generation import generate_mcq

        with pytest.raises(ValueError, match="expected a list"):
            await generate_mcq("text", None, 1)


# ---------------------------------------------------------------------------
# Flashcard non-streaming endpoint tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_flashcard_non_streaming_status_200(non_stream_flashcard_mock, app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/generate/flashcards",
            json={"text": "Study material", "stream": False},
        )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_flashcard_non_streaming_returns_list(non_stream_flashcard_mock, app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/generate/flashcards",
            json={"text": "Study material", "stream": False},
        )
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_flashcard_non_streaming_required_keys(non_stream_flashcard_mock, app):
    """Every flashcard object must contain the three required keys."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/generate/flashcards",
            json={"text": "Study material", "stream": False},
        )
    required_keys = {"front", "back", "topic_tag"}
    for card in resp.json():
        assert required_keys.issubset(card.keys())


# ---------------------------------------------------------------------------
# Flashcard streaming endpoint tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_flashcard_streaming_content_type(stream_flashcard_mock, app):
    """Streaming flashcards endpoint must respond with text/event-stream."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/generate/flashcards",
            json={"text": "Study material", "stream": True},
        )
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]


@pytest.mark.asyncio
async def test_flashcard_streaming_sse_delta_format(stream_flashcard_mock, app):
    """All non-terminal SSE events for flashcards must be JSON objects with a delta key."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/generate/flashcards",
            json={"text": "Study material", "stream": True},
        )
    events = [e for e in resp.text.strip().split("\n\n") if e]
    for event in events[:-1]:
        assert event.startswith("data: ")
        payload = json.loads(event[len("data: "):])
        assert "delta" in payload


@pytest.mark.asyncio
async def test_flashcard_streaming_ends_with_done(stream_flashcard_mock, app):
    """The final SSE event for flashcards must be data: [DONE]."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/generate/flashcards",
            json={"text": "Study material", "stream": True},
        )
    events = [e for e in resp.text.strip().split("\n\n") if e]
    assert events[-1] == "data: [DONE]"


@pytest.mark.asyncio
async def test_flashcard_request_missing_text_returns_422(app):
    """Omitting the required text field for flashcards must yield HTTP 422."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/generate/flashcards", json={"stream": False})
    assert resp.status_code == 422
