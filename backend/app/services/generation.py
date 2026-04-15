from __future__ import annotations

import functools
import json
from collections.abc import AsyncGenerator
from typing import Any, Optional

from anthropic import AsyncAnthropic
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings


@functools.lru_cache(maxsize=1)
def _get_client() -> AsyncAnthropic:
    return AsyncAnthropic(api_key=get_settings().ANTHROPIC_API_KEY)


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


def _build_flashcard_prompt(
    text: str,
    certification: Optional[str],
    n_cards: int,
    topic_tags: Optional[list[str]],
) -> str:
    cert_block = f"Certification context:\n{certification}\n\n" if certification else ""
    tags_block = f"Focus on these topics: {', '.join(topic_tags)}.\n" if topic_tags else ""
    return (
        f"{cert_block}"
        f"{tags_block}"
        f"Generate {n_cards} flashcards from the content below.\n\n"
        f"{text}"
    )


async def stream_flashcards(
    text: str,
    certification: Optional[str],
    n_cards: int,
    topic_tags: Optional[list[str]],
    deck_id: Optional[int] = None,
    db: Optional[AsyncSession] = None,
) -> AsyncGenerator[str, None]:
    user_prompt = _build_flashcard_prompt(text, certification, n_cards, topic_tags)

    full_text = ""
    async with _get_client().messages.stream(
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


async def generate_flashcards(
    text: str,
    certification: Optional[str],
    n_cards: int,
    topic_tags: Optional[list[str]],
) -> list[dict[str, Any]]:
    """Return the fully generated flashcard array as a Python list (non-streaming)."""
    user_prompt = _build_flashcard_prompt(text, certification, n_cards, topic_tags)

    message = await _get_client().messages.create(
        model="claude-opus-4-6",
        max_tokens=4096,
        system=_FLASHCARD_SYSTEM,
        messages=[{"role": "user", "content": user_prompt}],
    )
    if not message.content:
        raise ValueError("Anthropic returned an empty response")
    raw = "".join(block.text for block in message.content if hasattr(block, "text"))
    if not raw:
        raise ValueError("Anthropic returned no text content")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Anthropic returned invalid JSON: {exc}\nRaw response: {raw!r}"
        ) from exc

    if not isinstance(parsed, list):
        raise ValueError(
            f"Anthropic returned JSON of type {type(parsed).__name__}, expected a list"
        )
    if not all(isinstance(item, dict) for item in parsed):
        raise ValueError("Anthropic returned a JSON array containing non-object items")
    return parsed


def _build_mcq_prompt(
    text: str,
    certification: Optional[str],
    n_questions: int,
) -> str:
    cert_block = f"Certification context:\n{certification}\n\n" if certification else ""
    return (
        f"{cert_block}"
        f"Generate {n_questions} multiple-choice questions from the content below.\n\n"
        f"{text}"
    )


async def stream_mcq(
    text: str,
    certification: Optional[str],
    n_questions: int,
    deck_id: Optional[int] = None,
    db: Optional[AsyncSession] = None,
) -> AsyncGenerator[str, None]:
    user_prompt = _build_mcq_prompt(text, certification, n_questions)

    full_text = ""
    async with _get_client().messages.stream(
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


async def generate_mcq(
    text: str,
    certification: Optional[str],
    n_questions: int,
) -> list[dict[str, Any]]:
    """Return the fully generated MCQ array as a Python list (non-streaming)."""
    user_prompt = _build_mcq_prompt(text, certification, n_questions)

    message = await _get_client().messages.create(
        model="claude-opus-4-6",
        max_tokens=4096,
        system=_MCQ_SYSTEM,
        messages=[{"role": "user", "content": user_prompt}],
    )
    if not message.content:
        raise ValueError("Anthropic returned an empty response")
    raw = "".join(block.text for block in message.content if hasattr(block, "text"))
    if not raw:
        raise ValueError("Anthropic returned no text content")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Anthropic returned invalid JSON: {exc}\nRaw response: {raw!r}"
        ) from exc

    if not isinstance(parsed, list):
        raise ValueError(
            f"Anthropic returned JSON of type {type(parsed).__name__}, expected a list"
        )
    if not all(isinstance(item, dict) for item in parsed):
        raise ValueError("Anthropic returned a JSON array containing non-object items")
    return parsed
