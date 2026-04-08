from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from typing import Optional

from anthropic import AsyncAnthropic
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings

client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

_FLASHCARD_SYSTEM = (
    "You are an expert certification study card writer. "
    "Generate flashcards as a JSON array. "
    "Each object must have exactly these keys: "
    '{"front": str, "back": str, "topic_tag": str}. '
    "Output only the JSON array — no markdown fences, no explanation."
)

_MCQ_SYSTEM = (
    "You are an expert certification exam question writer. "
    "Generate multiple choice questions as a JSON array. "
    "Each object must have exactly these keys: "
    '{"question": str, "options": [str, str, str, str], "correct_index": int (0-3), "topic_tag": str}. '
    "Output only the JSON array — no markdown fences, no explanation."
)


async def _persist_flashcards(
    db: AsyncSession, deck_id: int, source_text: str, cards: list[dict]
) -> None:
    from app.models.cards import Card
    from app.models.ingest import SourceChunk

    chunk = SourceChunk(deck_id=deck_id, content=source_text, chunk_index=0)
    db.add(chunk)
    await db.flush()

    for item in cards:
        card = Card(
            deck_id=deck_id,
            source_chunk_id=chunk.id,
            type="flashcard",
            front=item.get("front"),
            back=item.get("back"),
            custom_topic_tag=item.get("topic_tag"),
        )
        db.add(card)

    await db.commit()


async def _persist_mcq(
    db: AsyncSession, deck_id: int, source_text: str, questions: list[dict]
) -> None:
    from app.models.cards import Card, MCQOption
    from app.models.ingest import SourceChunk

    chunk = SourceChunk(deck_id=deck_id, content=source_text, chunk_index=0)
    db.add(chunk)
    await db.flush()

    for item in questions:
        card = Card(
            deck_id=deck_id,
            source_chunk_id=chunk.id,
            type="mcq",
            front=item.get("question"),
            back=None,
            custom_topic_tag=item.get("topic_tag"),
        )
        db.add(card)
        await db.flush()

        for i, option_text in enumerate(item.get("options", [])):
            db.add(MCQOption(
                card_id=card.id,
                position=i,
                text=option_text,
                is_correct=(i == item.get("correct_index", -1)),
            ))

    await db.commit()


async def stream_flashcards(
    text: str,
    certification: Optional[str],
    n_cards: int,
    topic_tags: Optional[list[str]],
    deck_id: Optional[int] = None,
    db: Optional[AsyncSession] = None,
) -> AsyncGenerator[str, None]:
    cert_block = f"Certification context:\n{certification}\n\n" if certification else ""
    tags_block = f"Focus on these topics: {', '.join(topic_tags)}.\n" if topic_tags else ""
    user_prompt = (
        f"{cert_block}"
        f"{tags_block}"
        f"Generate {n_cards} flashcards from the content below.\n\n"
        f"{text}"
    )

    full_text = ""
    async with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=4096,
        system=_FLASHCARD_SYSTEM,
        messages=[{"role": "user", "content": user_prompt}],
    ) as stream:
        async for chunk in stream.text_stream:
            full_text += chunk
            yield f"data: {json.dumps({'delta': chunk})}\n\n"

    if deck_id is not None and db is not None:
        try:
            cards = json.loads(full_text)
            await _persist_flashcards(db, deck_id, text, cards)
        except Exception:
            pass  # don't fail the stream on persistence errors

    yield "data: [DONE]\n\n"


async def stream_mcq(
    text: str,
    certification: Optional[str],
    n_questions: int,
    deck_id: Optional[int] = None,
    db: Optional[AsyncSession] = None,
) -> AsyncGenerator[str, None]:
    cert_block = f"Certification context:\n{certification}\n\n" if certification else ""
    user_prompt = (
        f"{cert_block}"
        f"Generate {n_questions} multiple-choice questions from the content below.\n\n"
        f"{text}"
    )

    full_text = ""
    async with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=4096,
        system=_MCQ_SYSTEM,
        messages=[{"role": "user", "content": user_prompt}],
    ) as stream:
        async for chunk in stream.text_stream:
            full_text += chunk
            yield f"data: {json.dumps({'delta': chunk})}\n\n"

    if deck_id is not None and db is not None:
        try:
            questions = json.loads(full_text)
            await _persist_mcq(db, deck_id, text, questions)
        except Exception:
            pass

    yield "data: [DONE]\n\n"
