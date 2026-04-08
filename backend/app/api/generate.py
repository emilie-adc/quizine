from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services import generation

router = APIRouter()


class FlashcardRequest(BaseModel):
    text: str
    certification: str | None = None
    n_cards: int = 10
    topic_tags: list[str] | None = None
    stream: bool = True


class MCQRequest(BaseModel):
    text: str
    certification: str | None = None
    n_questions: int = 10
    stream: bool = True


@router.post("/flashcards")
async def generate_flashcards(req: FlashcardRequest) -> StreamingResponse:
    return StreamingResponse(
        generation.stream_flashcards(req.text, req.certification, req.n_cards, req.topic_tags),
        media_type="text/event-stream",
    )


@router.post("/mcq")
async def generate_mcq(req: MCQRequest) -> StreamingResponse:
    return StreamingResponse(
        generation.stream_mcq(req.text, req.certification, req.n_questions),
        media_type="text/event-stream",
    )
