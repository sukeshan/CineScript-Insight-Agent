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
    max_retries: int = 4,
) -> tuple[BaseModel, dict[str, int]]:
    """
    Async LLM call → validated Pydantic object + token usage.
    Uses create_with_completion() to get usage stats from the API response.
    Returns: (pydantic_model, {"prompt_tokens": N, "completion_tokens": N, "total_tokens": N})
    """
    client = get_async_client()
    model, completion = await client.create_with_completion(
        response_model=response_model,
        messages=messages,
        temperature=temperature,
        max_retries=max_retries,
    )
    
    # Extract token usage from the raw OpenAI completion
    usage = {}
    if hasattr(completion, "usage") and completion.usage:
        usage = {
            "prompt_tokens": completion.usage.prompt_tokens or 0,
            "completion_tokens": completion.usage.completion_tokens or 0,
            "total_tokens": completion.usage.total_tokens or 0,
        }
    
    return model, usage

