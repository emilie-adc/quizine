from __future__ import annotations

import json
from collections.abc import AsyncGenerator

from anthropic import AsyncAnthropic

from app.core.config import settings

client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

_FLASHCARD_SYSTEM = (
    "You are an expert certification study card writer. "
    "Generate flashcards as a JSON array. "
    "Each object must have exactly these keys: "
    '{"front": str, "back": str, "topic_tag": str}. '
    "Output only the JSON array — no markdown fences, no explanation."
)


async def stream_flashcards(
    text: str,
    certification: str | None,
    n_cards: int,
    topic_tags: list[str] | None,
) -> AsyncGenerator[str, None]:
    cert_block = f"Certification context:\n{certification}\n\n" if certification else ""
    tags_block = f"Focus on these topics: {', '.join(topic_tags)}.\n" if topic_tags else ""
    user_prompt = (
        f"{cert_block}"
        f"{tags_block}"
        f"Generate {n_cards} flashcards from the content below.\n\n"
        f"{text}"
    )

    async with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=4096,
        system=_FLASHCARD_SYSTEM,
        messages=[{"role": "user", "content": user_prompt}],
    ) as stream:
        async for chunk in stream.text_stream:
            yield f"data: {json.dumps({'delta': chunk})}\n\n"
        yield "data: [DONE]\n\n"


_MCQ_SYSTEM = (
    "You are an expert certification exam question writer. "
    "Generate multiple choice questions as a JSON array. "
    "Each object must have exactly these keys: "
    '{"question": str, "options": [str, str, str, str], "correct_index": int (0-3), "topic_tag": str}. '
    "Output only the JSON array — no markdown fences, no explanation."
)


async def stream_mcq(
    text: str,
    certification: str | None,
    n_questions: int,
) -> AsyncGenerator[str, None]:
    cert_block = f"Certification context:\n{certification}\n\n" if certification else ""
    user_prompt = (
        f"{cert_block}"
        f"Generate {n_questions} multiple-choice questions from the content below.\n\n"
        f"{text}"
    )

    async with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=4096,
        system=_MCQ_SYSTEM,
        messages=[{"role": "user", "content": user_prompt}],
    ) as stream:
        async for chunk in stream.text_stream:
            yield f"data: {json.dumps({'delta': chunk})}\n\n"
        yield "data: [DONE]\n\n"
