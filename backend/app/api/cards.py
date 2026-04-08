from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.cards import Card
from app.schemas.cards import CardResponse, CardUpdate

router = APIRouter()


async def _get_card_or_404(card_id: int, db: AsyncSession) -> Card:
    card = await db.get(Card, card_id)
    if card is None:
        raise HTTPException(status_code=404, detail="Card not found")
    return card


@router.patch("/{card_id}", response_model=CardResponse)
async def update_card(
    card_id: int, body: CardUpdate, db: AsyncSession = Depends(get_db)
) -> CardResponse:
    card = await _get_card_or_404(card_id, db)
    if body.front is not None:
        card.front = body.front
    if body.back is not None:
        card.back = body.back
    if body.custom_topic_tag is not None:
        card.custom_topic_tag = body.custom_topic_tag
    await db.commit()
    await db.refresh(card)
    return CardResponse.model_validate(card)


@router.delete("/{card_id}", status_code=204, response_model=None)
async def delete_card(card_id: int, db: AsyncSession = Depends(get_db)) -> None:
    card = await _get_card_or_404(card_id, db)
    await db.delete(card)
    await db.commit()


@router.post("/{card_id}/approve", response_model=CardResponse)
async def approve_card(card_id: int, db: AsyncSession = Depends(get_db)) -> CardResponse:
    card = await _get_card_or_404(card_id, db)
    card.approved = True
    await db.commit()
    await db.refresh(card)
    return CardResponse.model_validate(card)
