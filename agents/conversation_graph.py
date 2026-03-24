from typing import TypedDict, Any, Annotated, Literal
import operator
import os
import json
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END

from core.llm import call_llm_structured
from core.tools import execute_tool
from core.context_manager import should_compress, drop_raw_script_message, truncate_to_window
from core.prompts import build_main_prompt

# ── Structured Agent Action ───────────────────────────────────────────────────

class AgentAction(BaseModel):
    """
    Represents a single action in the ReAct loop. The LLM must reason about the conversation,
    choose a data-retrieval tool if needed, or provide the final conversational answer.
    """
    thought: str = Field(
        description="Detailed internal monologue explaining your step-by-step reasoning. Evaluate what information is missing, what tool is needed to retrieve it, and what the next logical step is."
    )
    tool_name: Literal["load_file", "write_file", "final_answer"] = Field(
        description=(
            "The specific action to execute. "
            "- 'load_file': reads an analysis file (e.g. outputs/character_analysis.md) into your context. "
            "- 'write_file': writes generated insights to a new markdown file. "
            "- 'final_answer': use ONLY when you have gathered all necessary information and are ready to respond to the user."
        )
    )
    tool_args: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "REQUIRED dictionary of arguments for the chosen tool. YOU MUST NOT LEAVE THIS EMPTY if calling a tool. "
            "It must be a valid JSON object containing the exact keys: "
            "- If tool_name is 'load_file', you MUST return exactly: {\"filename\": \"<path to file>\"} "
            "- If tool_name is 'write_file', you MUST return exactly: {\"filepath\": \"<path>\", \"content\": \"<markdown text>\"} "
            "- If tool_name is 'final_answer', return an empty dictionary {}."
        )
    )
    response: str | None = Field(
        default=None,
        description="If tool_name is 'final_answer', provide your comprehensive reply to the user here. Leave null otherwise."
    )
    follow_up_chips: list[str] | None = Field(
        default=None,
        description=(
            "If tool_name is 'final_answer', you MUST provide a list of 2-3 short, engaging follow-up questions (chips). "
            "These chips MUST be directly and highly relevant to the exact answer you just generated, "
            "propelling the conversation deeper into specific details of your response."
        )
    )

# ── LangGraph State ──────────────────────────────────────────────────────────

class ConversationState(TypedDict):
    messages: Annotated[list[dict[str, Any]], operator.add]
    token_count: int  # Running total from API usage — no tiktoken needed
    compression_triggered: bool  # Signal to the UI when budget is exceeded

# ── Nodes ────────────────────────────────────────────────────────────────────

async def agent_node(state: ConversationState) -> dict:
    """Call the LLM using structured output and save the action to history."""
    
    # 1. Dynamically build/refresh the system prompt if skills_index.md exists
    skills_index_path = "outputs/skills_index.md"
    current_messages = list(state["messages"])
    
    if os.path.exists(skills_index_path):
        with open(skills_index_path, "r", encoding="utf-8") as f:
            skills_content = f.read()
        dynamic_system_prompt = build_main_prompt(skills_content)
    else:
        # Fallback to default prompt without skills content
        dynamic_system_prompt = build_main_prompt()

    if current_messages and current_messages[0]["role"] == "system":
        current_messages[0]["content"] = dynamic_system_prompt
    else:
        current_messages.insert(0, {"role": "system", "content": dynamic_system_prompt})

    # 2. Check if compression is needed using the running token count
    current_token_count = state.get("token_count", 0)
    compression_active = False
    
    if should_compress(current_token_count):
        compression_active = True
        current_messages = drop_raw_script_message(current_messages)
        current_messages = await truncate_to_window(current_messages, keep_last_n=10, keep_first=3)
    
    # 3. Call LLM — get both the structured response AND token usage from the API
    action, usage = await call_llm_structured(
        messages=current_messages,
        response_model=AgentAction,
        temperature=0.4
    )

    # 4. Update running token count from API response (zero-latency)
    new_token_count = usage.get("total_tokens", current_token_count)
    
    # Save the LLM's thought and chosen action as an assistant message
    msg_dict: dict[str, Any] = {
        "role": "assistant",
        "content": action.model_dump_json()
    }
    
    return {
        "messages": [msg_dict], 
        "token_count": new_token_count,
        "compression_triggered": compression_active
    }

async def tools_node(state: ConversationState) -> dict:
    """Read the last action and execute the requested tool."""
    last_message = state["messages"][-1]
    
    try:
        action_data = json.loads(last_message.get("content", "{}"))
        tool_name = action_data.get("tool_name")
        tool_args = action_data.get("tool_args", {})
    except Exception as e:
        return {"messages": [{"role": "user", "content": f"Observation (Error): Could not parse tool request - {e}"}]}
        
    if tool_name == "final_answer":
        return {"messages": []}
        
    result = await execute_tool(tool_name, tool_args)
    
    obs_msg: dict[str, Any] = {
        "role": "user",
        "content": f"Observation from {tool_name}: {str(result)}"
    }
    
    return {"messages": [obs_msg]}

def should_continue(state: ConversationState) -> str:
    """Route back to tools or end the sequence."""
    last_message = state["messages"][-1]
    try:
        action_data = json.loads(last_message.get("content", "{}"))
        tool_name = action_data.get("tool_name")
        
        if tool_name in ["load_file", "write_file"]:
            return "tools"
    except Exception:
        pass
        
    return END

# ── Build the LangGraph ──────────────────────────────────────────────────────

workflow = StateGraph(ConversationState)

workflow.add_node("agent", agent_node)
workflow.add_node("tools", tools_node)

workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", should_continue)
workflow.add_edge("tools", "agent")

conversation_graph = workflow.compile()
