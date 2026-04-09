"""Tests for the /certifications endpoints.

All database access is mocked; no real DB connection is required.
"""
from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

# Ensure required env vars exist before the app is first imported.
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
os.environ.setdefault("UPLOADS_DIR", "./uploads")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:5173")

from app.schemas.certifications import CertificationDetail, CertificationSummary, Domain

# ---------------------------------------------------------------------------
# Sample fixture data
# ---------------------------------------------------------------------------

_SAMPLE_DOMAINS = [
    Domain(
        id=1,
        name="ML Fundamentals",
        slug="ml-fundamentals",
        weight_pct=30,
        description="Core machine learning concepts",
    ),
    Domain(
        id=2,
        name="Feature Engineering",
        slug="feature-engineering",
        weight_pct=25,
        description="Feature preparation and selection",
    ),
]

_SAMPLE_SUMMARY = CertificationSummary(
    id=1,
    slug="databricks-ml-associate",
    display_name="Databricks Machine Learning Associate",
    provider="Databricks",
    level="Associate",
    pass_score_pct=70,
)

_SAMPLE_DETAIL = CertificationDetail(
    id=1,
    slug="databricks-ml-associate",
    display_name="Databricks Machine Learning Associate",
    provider="Databricks",
    level="Associate",
    pass_score_pct=70,
    prompt_context="Databricks ML Associate context.",
    domains=_SAMPLE_DOMAINS,
)


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def app():
    from app.main import app as _app

    return _app


@pytest.fixture(autouse=True)
def override_db(app):
    """Override the get_db dependency so no real DB connection is attempted."""
    from app.core.database import get_db

    async def _fake_db():
        yield MagicMock()

    app.dependency_overrides[get_db] = _fake_db
    yield
    app.dependency_overrides.pop(get_db, None)


# ---------------------------------------------------------------------------
# GET /certifications/  — list all certifications
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_certifications_status_200(app):
    with patch(
        "app.services.certifications.list_certifications",
        new=AsyncMock(return_value=[_SAMPLE_SUMMARY]),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/certifications/")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_list_certifications_returns_list(app):
    with patch(
        "app.services.certifications.list_certifications",
        new=AsyncMock(return_value=[_SAMPLE_SUMMARY]),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/certifications/")
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 1


@pytest.mark.asyncio
async def test_list_certifications_response_shape(app):
    with patch(
        "app.services.certifications.list_certifications",
        new=AsyncMock(return_value=[_SAMPLE_SUMMARY]),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/certifications/")
    cert = resp.json()[0]
    required_keys = {"id", "slug", "display_name", "provider", "level", "pass_score_pct"}
    assert required_keys.issubset(cert.keys())
    assert cert["slug"] == "databricks-ml-associate"


@pytest.mark.asyncio
async def test_list_certifications_empty(app):
    with patch(
        "app.services.certifications.list_certifications",
        new=AsyncMock(return_value=[]),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/certifications/")
    assert resp.status_code == 200
    assert resp.json() == []


# ---------------------------------------------------------------------------
# GET /certifications/{slug}  — certification detail
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_certification_status_200(app):
    with patch(
        "app.services.certifications.get_certification",
        new=AsyncMock(return_value=_SAMPLE_DETAIL),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/certifications/databricks-ml-associate")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_get_certification_response_shape(app):
    with patch(
        "app.services.certifications.get_certification",
        new=AsyncMock(return_value=_SAMPLE_DETAIL),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/certifications/databricks-ml-associate")
    data = resp.json()
    required_keys = {"id", "slug", "display_name", "provider", "level", "pass_score_pct", "prompt_context", "domains"}
    assert required_keys.issubset(data.keys())
    assert data["slug"] == "databricks-ml-associate"
    assert isinstance(data["domains"], list)
    assert len(data["domains"]) == 2


@pytest.mark.asyncio
async def test_get_certification_unknown_slug_returns_404(app):
    with patch(
        "app.services.certifications.get_certification",
        new=AsyncMock(return_value=None),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/certifications/unknown-slug")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /certifications/{slug}/domains  — domains for a certification
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_domains_status_200(app):
    with patch(
        "app.services.certifications.get_domains",
        new=AsyncMock(return_value=_SAMPLE_DOMAINS),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/certifications/databricks-ml-associate/domains")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_get_domains_returns_list(app):
    with patch(
        "app.services.certifications.get_domains",
        new=AsyncMock(return_value=_SAMPLE_DOMAINS),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/certifications/databricks-ml-associate/domains")
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 2


@pytest.mark.asyncio
async def test_get_domains_response_shape(app):
    with patch(
        "app.services.certifications.get_domains",
        new=AsyncMock(return_value=_SAMPLE_DOMAINS),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/certifications/databricks-ml-associate/domains")
    domain = resp.json()[0]
    required_keys = {"id", "name", "slug", "weight_pct", "description"}
    assert required_keys.issubset(domain.keys())
    assert domain["slug"] == "ml-fundamentals"


@pytest.mark.asyncio
async def test_get_domains_unknown_slug_returns_404(app):
    with patch(
        "app.services.certifications.get_domains",
        new=AsyncMock(return_value=None),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/certifications/unknown-slug/domains")
    assert resp.status_code == 404
