from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.cards import Card
from app.models.certifications import Certification
from app.models.decks import Deck
from app.schemas.decks import DeckCreate, DeckDetail, DeckSummary

router = APIRouter()


@router.post("", response_model=DeckSummary, status_code=201)
async def create_deck(body: DeckCreate, db: AsyncSession = Depends(get_db)) -> DeckSummary:
    if body.cert_id is not None:
        cert = await db.get(Certification, body.cert_id)
        if cert is None:
            raise HTTPException(status_code=404, detail="Certification not found")

    deck = Deck(
        title=body.title,
        cert_id=body.cert_id,
        custom_cert_name=body.custom_cert_name,
    )
    db.add(deck)
    await db.commit()
    await db.refresh(deck)
    return DeckSummary.model_validate(deck)


@router.get("", response_model=list[DeckSummary])
async def list_decks(db: AsyncSession = Depends(get_db)) -> list[DeckSummary]:
    result = await db.execute(select(Deck).order_by(Deck.created_at.desc()))
    decks = result.scalars().all()
    return [DeckSummary.model_validate(d) for d in decks]


@router.get("/{deck_id}", response_model=DeckDetail)
async def get_deck(deck_id: int, db: AsyncSession = Depends(get_db)) -> DeckDetail:
    result = await db.execute(
        select(Deck)
        .where(Deck.id == deck_id)
        .options(selectinload(Deck.certification))
    )
    deck = result.scalar_one_or_none()
    if deck is None:
        raise HTTPException(status_code=404, detail="Deck not found")

    count_result = await db.execute(
        select(func.count()).select_from(Card).where(Card.deck_id == deck_id)
    )
    card_count = count_result.scalar_one()

    cert = deck.certification
    return DeckDetail(
        id=deck.id,
        title=deck.title,
        cert_id=deck.cert_id,
        custom_cert_name=deck.custom_cert_name,
        created_at=deck.created_at,
        cert_slug=cert.slug if cert else None,
        cert_display_name=cert.display_name if cert else None,
        card_count=card_count,
    )
