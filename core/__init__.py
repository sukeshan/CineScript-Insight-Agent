"""Core package — Instructor-based LLM client, context, prompts, and orchestration."""

from core.llm import (
    get_client,
    get_async_client,
    call_llm_structured,
    call_llm_structured_sync,
    call_llm_text,
    call_llm_raw,
    DEFAULT_MODEL,
)
from core.context import ScriptContext
from core.prompts import (
    SHARED_PREFIX_SYSTEM,
    SUMMARY_PROMPT,
    CHARACTER_PROMPT,
    ENTITY_MAPPER_PROMPT,
    MAIN_SYSTEM_PROMPT,
    LOAD_FILE_TOOL,
)

__all__ = [
    "get_client",
    "get_async_client",
    "call_llm_structured",
    "call_llm_structured_sync",
    "call_llm_text",
    "call_llm_raw",
    "DEFAULT_MODEL",
    "ScriptContext",
    "SHARED_PREFIX_SYSTEM",
    "SUMMARY_PROMPT",
    "CHARACTER_PROMPT",
    "ENTITY_MAPPER_PROMPT",
    "MAIN_SYSTEM_PROMPT",
    "LOAD_FILE_TOOL",
]
