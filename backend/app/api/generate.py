from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services import generation

router = APIRouter()


class FlashcardRequest(BaseModel):
    text: str
    certification: Optional[str] = None
    n_cards: int = 10
    topic_tags: Optional[list[str]] = None
    stream: bool = True
    deck_id: Optional[int] = None


class MCQRequest(BaseModel):
    text: str
    certification: Optional[str] = None
    n_questions: int = 10
    stream: bool = True
    deck_id: Optional[int] = None


@router.post("/flashcards")
async def generate_flashcards(
    req: FlashcardRequest,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    return StreamingResponse(
        generation.stream_flashcards(
            req.text, req.certification, req.n_cards, req.topic_tags,
            deck_id=req.deck_id, db=db,
        ),
        media_type="text/event-stream",
    )


@router.post("/mcq")
async def generate_mcq(
    req: MCQRequest,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    return StreamingResponse(
        generation.stream_mcq(
            req.text, req.certification, req.n_questions,
            deck_id=req.deck_id, db=db,
        ),
        media_type="text/event-stream",
    )
