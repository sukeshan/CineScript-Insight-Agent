"""
Core LLM client — uses Instructor + OpenAI GPT-5.2 for structured generation.
All outputs are validated Pydantic objects.
"""

import os
from typing import Any, Type

from dotenv import load_dotenv
import instructor
from pydantic import BaseModel

load_dotenv()

# ── Model config ──────────────────────────────────────────────────────────────
DEFAULT_MODEL = "gpt-5.2"
PROVIDER = f"openai/{DEFAULT_MODEL}"

# ── Client singletons ────────────────────────────────────────────────────────
_sync_client: instructor.Instructor | None = None
_async_client: instructor.AsyncInstructor | None = None


def _ensure_api_key() -> None:
    """Verify the OpenAI API key is set."""
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY not set in environment")


def get_client() -> instructor.Instructor:
    """Return a reusable sync Instructor client (OpenAI GPT-5.2)."""
    global _sync_client
    if _sync_client is None:
        _ensure_api_key()
        _sync_client = instructor.from_provider(PROVIDER)
    return _sync_client


def get_async_client() -> instructor.AsyncInstructor:
    """Return a reusable async Instructor client (OpenAI GPT-5.2)."""
    global _async_client
    if _async_client is None:
        _ensure_api_key()
        _async_client = instructor.from_provider(PROVIDER, async_client=True)
    return _async_client

# ── Structured output (Pydantic) ─────────────────────────────────────────────

async def call_llm_structured(
    messages: list[dict[str, Any]],
    response_model: Type[BaseModel],
    *,
    temperature: float = 0.3,
    max_retries: int = 2,
) -> BaseModel:
    """
    Async LLM call → validated Pydantic object.
    Instructor handles JSON schema enforcement + retries automatically.
    """
    client = get_async_client()
    return await client.create(
        response_model=response_model,
        messages=messages,
        temperature=temperature,
        max_retries=max_retries,
    )



