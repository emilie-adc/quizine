"""Tests for the /generate/mcq endpoint and the generation service.

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
