"""
T13 seed script tests — run against SQLite in-memory (async via aiosqlite).
"""
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import select

from app.models.base import Base
import app.models  # noqa: F401 — registers all models


@pytest_asyncio.fixture
async def db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_seed_inserts_certifications(db: AsyncSession):
    from seed_certifications import seed_certifications
    await seed_certifications(db)

    from app.models.certifications import Certification
    result = await db.execute(select(Certification))
    certs = result.scalars().all()
    assert len(certs) == 2
    slugs = {c.slug for c in certs}
    assert "databricks-ml-associate" in slugs
    assert "databricks-ml-professional" in slugs


@pytest.mark.asyncio
async def test_seed_inserts_domains(db: AsyncSession):
    from seed_certifications import seed_certifications
    await seed_certifications(db)

    from app.models.certifications import CertDomain
    result = await db.execute(select(CertDomain))
    domains = result.scalars().all()
    # 4 domains per cert × 2 certs
    assert len(domains) == 8
    weights = [d.weight_pct for d in domains]
    assert all(w > 0 for w in weights)


@pytest.mark.asyncio
async def test_seed_is_idempotent(db: AsyncSession):
    from seed_certifications import seed_certifications
    await seed_certifications(db)
    await seed_certifications(db)  # second run — must not duplicate

    from app.models.certifications import Certification, CertDomain
    certs = (await db.execute(select(Certification))).scalars().all()
    domains = (await db.execute(select(CertDomain))).scalars().all()
    assert len(certs) == 2
    assert len(domains) == 8


@pytest.mark.asyncio
async def test_seed_domain_weights_sum_to_100(db: AsyncSession):
    from seed_certifications import seed_certifications
    await seed_certifications(db)

    from app.models.certifications import Certification
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Certification).options(selectinload(Certification.domains))
    )
    for cert in result.scalars().all():
        total = sum(d.weight_pct for d in cert.domains)
        assert total == 100, f"{cert.slug} weights sum to {total}, not 100"
