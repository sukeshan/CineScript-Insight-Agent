"""
Context Budget Management.
Tracks token usage and compresses context when reaching thresholds.
"""
import copy
from typing import Any

# GPT-5.2 context limit is ~4M
MODEL_CONTEXT_LIMIT = 400_000
BUDGET_THRESHOLD = 0.40

def get_token_limit() -> int:
    return int(MODEL_CONTEXT_LIMIT * BUDGET_THRESHOLD)

def should_compress(current_token_count: int) -> bool:
    """Check if the running token count exceeds the compression threshold."""
    return current_token_count >= get_token_limit()

def drop_raw_script_message(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Finds the user message that contains the raw script and replaces it with a placeholder."""
    compressed = copy.deepcopy(messages)
    for msg in compressed:
        if msg["role"] == "user" and "Here is the script" in str(msg.get("content", "")):
            msg["content"] = "[Raw Script Offloaded to save context budget. The system retains the Summary and Analysis in tools.]"
            break
    return compressed

def get_turns(messages: list[dict[str, Any]]) -> list[list[int]]:
    """
    Groups message indices into 'turns'.
    A turn = a user message and all subsequent assistant/tool messages.
    """
    turns: list[list[int]] = []
    current_turn: list[int] = []
    for i, msg in enumerate(messages):
        if msg["role"] == "user" and current_turn:
            turns.append(current_turn)
            current_turn = [i]
        else:
            current_turn.append(i)
    if current_turn:
        turns.append(current_turn)
    return turns

def truncate_to_window(messages: list[dict[str, Any]], keep_last_n: int = 10, keep_first: int = 3) -> list[dict[str, Any]]:
    """
    Keeps the first N 'anchor' messages and the last M 'turns'.
    """
    if len(messages) <= keep_first:
        return messages
        
    anchors = messages[:keep_first]
    rest = messages[keep_first:]
    
    turns = get_turns(rest)
    if len(turns) <= keep_last_n:
        return messages
        
    # Keep only the last N turns
    kept_turns_indices: list[int] = []
    for turn in turns[-keep_last_n:]:
        kept_turns_indices.extend(turn)
        
    recent_messages = [rest[i] for i in kept_turns_indices]
    return anchors + recent_messages
