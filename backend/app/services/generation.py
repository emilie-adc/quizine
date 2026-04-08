import functools
import json
from collections.abc import AsyncGenerator
from typing import Any

from anthropic import AsyncAnthropic

from app.core.config import get_settings

_MCQ_SYSTEM = (
    "You are an expert certification exam question writer. "
    "Generate multiple choice questions as a JSON array. "
    "Each object must have exactly these keys: "
    '{"question": str, "options": [str, str, str, str], "correct_index": int (0-3), "topic_tag": str}. '
    "Output only the JSON array — no markdown fences, no explanation."
)


@functools.lru_cache(maxsize=1)
def _get_client() -> AsyncAnthropic:
    return AsyncAnthropic(api_key=get_settings().ANTHROPIC_API_KEY)


def _build_user_prompt(text: str, certification: str | None, n_questions: int) -> str:
    cert_block = f"Certification context:\n{certification}\n\n" if certification else ""
    return (
        f"{cert_block}"
        f"Generate {n_questions} multiple-choice questions from the content below.\n\n"
        f"{text}"
    )


async def stream_mcq(
    text: str,
    certification: str | None,
    n_questions: int,
) -> AsyncGenerator[str, None]:
    user_prompt = _build_user_prompt(text, certification, n_questions)

    async with _get_client().messages.stream(
        model="claude-opus-4-6",
        max_tokens=4096,
        system=_MCQ_SYSTEM,
        messages=[{"role": "user", "content": user_prompt}],
    ) as stream:
        async for chunk in stream.text_stream:
            yield f"data: {json.dumps({'delta': chunk})}\n\n"
        yield "data: [DONE]\n\n"


async def generate_mcq(
    text: str,
    certification: str | None,
    n_questions: int,
) -> list[dict[str, Any]]:
    """Return the fully generated MCQ array as a Python list (non-streaming)."""
    user_prompt = _build_user_prompt(text, certification, n_questions)

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
