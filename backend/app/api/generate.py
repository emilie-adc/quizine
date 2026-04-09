from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse, StreamingResponse
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


@router.post("/flashcards", response_model=None)
async def generate_flashcards(req: FlashcardRequest) -> StreamingResponse | JSONResponse:
    if req.stream:
        return StreamingResponse(
            generation.stream_flashcards(req.text, req.certification, req.n_cards, req.topic_tags),
            media_type="text/event-stream",
        )
    cards = await generation.generate_flashcards(
        req.text, req.certification, req.n_cards, req.topic_tags
    )
    return JSONResponse(content=cards)


@router.post("/mcq", response_model=None)
async def generate_mcq(req: MCQRequest) -> StreamingResponse | JSONResponse:
    if req.stream:
        return StreamingResponse(
            generation.stream_mcq(req.text, req.certification, req.n_questions),
            media_type="text/event-stream",
        )
    questions = await generation.generate_mcq(req.text, req.certification, req.n_questions)
    return JSONResponse(content=questions)
