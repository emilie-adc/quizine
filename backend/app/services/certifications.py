from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


async def list_certifications(db: AsyncSession) -> list:
    # Models imported here — they are created in T11
    from app.models.certifications import Certification

    result = await db.execute(select(Certification))
    return list(result.scalars().all())


async def get_certification(db: AsyncSession, slug: str):
    # Models imported here — they are created in T11
    from app.models.certifications import Certification

    result = await db.execute(
        select(Certification)
        .where(Certification.slug == slug)
        .options(selectinload(Certification.domains))
    )
    return result.scalar_one_or_none()


async def get_domains(db: AsyncSession, slug: str) -> list | None:
    # Models imported here — they are created in T11
    from app.models.certifications import Certification

    cert = await db.execute(
        select(Certification)
        .where(Certification.slug == slug)
        .options(selectinload(Certification.domains))
    )
    certification = cert.scalar_one_or_none()
    if certification is None:
        return None
    return certification.domains
