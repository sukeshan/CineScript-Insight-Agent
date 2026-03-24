"""Core package — Instructor-based LLM client, context, prompts, and orchestration."""

from core.llm import (
    get_client,
    get_async_client,
    call_llm_structured,
    DEFAULT_MODEL,
)
from core.context import ScriptContext
from core.prompts import (
    SHARED_PREFIX_SYSTEM,
    MAIN_SYSTEM_PROMPT,
)

__all__ = [
    "get_client",
    "get_async_client",
    "call_llm_structured",
    "DEFAULT_MODEL",
    "ScriptContext",
    "SHARED_PREFIX_SYSTEM",
    "MAIN_SYSTEM_PROMPT",
]
