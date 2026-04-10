from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.certifications import CertificationDetail, CertificationSummary, Domain
from app.services import certifications as cert_service

router = APIRouter()


@router.get("/", response_model=list[CertificationSummary])
async def list_certifications(db: AsyncSession = Depends(get_db)) -> list[CertificationSummary]:
    return await cert_service.list_certifications(db)


@router.get("/{slug}", response_model=CertificationDetail)
async def get_certification(slug: str, db: AsyncSession = Depends(get_db)) -> CertificationDetail:
    cert = await cert_service.get_certification(db, slug)
    if cert is None:
        raise HTTPException(status_code=404, detail="Certification not found")
    return cert


@router.get("/{slug}/domains", response_model=list[Domain])
async def get_domains(slug: str, db: AsyncSession = Depends(get_db)) -> list[Domain]:
    domains = await cert_service.get_domains(db, slug)
    if domains is None:
        raise HTTPException(status_code=404, detail="Certification not found")
    return domains
