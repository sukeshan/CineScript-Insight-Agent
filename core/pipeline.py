import operator
from typing import Annotated, TypedDict

from langgraph.graph import StateGraph, END

from agents.summary import run_summary
from agents.characters import run_character_analysis
from agents.entity_mapper import run_entity_mapper
from models.summary import SummaryOutput
from models.characters import CharacterAnalysisOutput
from models.entities import EntityMapOutput
from core.context import ScriptContext


# ── State Definition ──────────────────────────────────────────────────────────

class PipelineState(TypedDict):
    """The state dictionary flowing through the Phase 1 graph."""
    raw_script: str
    
    # Reducers: just overwrite with latest value
    summary: SummaryOutput | None
    characters_out: CharacterAnalysisOutput | None
    entities_out: EntityMapOutput | None
    
    # Final consolidated context
    context: ScriptContext | None


# ── Nodes ─────────────────────────────────────────────────────────────────────

async def summary_node(state: PipelineState) -> dict:
    """Generate the summary first. This seeds the KV cache."""
    summary_out = await run_summary(state["raw_script"])
    return {"summary": summary_out}


async def character_node(state: PipelineState) -> dict:
    """Extract characters. Runs in parallel with entity mapping."""
    chars = await run_character_analysis(state["raw_script"])
    
    # Write to local markdown file immediately
    with open("outputs/character_analysis.md", "w", encoding="utf-8") as f:
        f.write("# Character Analysis\n\n")
        for char in chars.characters:
            f.write(f"### {char.name}\n")
            f.write(f"- **Role**: {char.role}\n")
            f.write(f"- **Arc**: {char.arc}\n")
            f.write(f"- **Key Moments**: {', '.join(char.key_moments)}\n")
            f.write(f"- **Relationships**: {', '.join(char.relationships)}\n\n")
            
    return {"characters_out": chars}


async def entity_node(state: PipelineState) -> dict:
    """Map scene entities. Runs in parallel with character extraction."""
    entities = await run_entity_mapper(state["raw_script"])
    
    # Write to local markdown file immediately
    with open("outputs/entity_map.md", "w", encoding="utf-8") as f:
        f.write("# Entity Map\n\n")
        f.write("| Scene | Type | Valence | Intensity | Eng. Delta | Pos % | Description |\n")
        f.write("|---|---|---|---|---|---|---|\n")
        for e in entities.entities:
            f.write(f"| {e.scene_id} | {e.entity_type} | {e.valence} | {e.intensity} | {e.engagement_delta} | {e.position_pct:.1f}% | {e.description} |\n")
            
    return {"entities_out": entities}


def finalize_node(state: PipelineState) -> dict:
    """Consolodate everything into the final ScriptContext."""
    chars = state["characters_out"].characters if state["characters_out"] else []
    ents = state["entities_out"].entities if state["entities_out"] else []
    
    ctx = ScriptContext(
        raw_script=state["raw_script"],
        summary="\n".join([f"- {s}" for s in state["summary"].summary]) if state.get("summary") else "",
        characters=chars,
        entity_map=ents,
        char_md_path="outputs/character_analysis.md",
        entity_md_path="outputs/entity_map.md",
        background_ready=True
    )
    return {"context": ctx}


# ── Graph Builder ─────────────────────────────────────────────────────────────

def build_phase1_graph() -> StateGraph:
    """Construct and compile the Phase 1 LangGraph."""
    builder = StateGraph(PipelineState)

    # Add nodes
    builder.add_node("summary", summary_node)
    builder.add_node("character", character_node)
    builder.add_node("entity", entity_node)
    builder.add_node("finalize", finalize_node)

    # Edge logic
    # Start -> summary
    builder.set_entry_point("summary")

    # summary -> [character, entity] (Parallel Fan-out)
    builder.add_edge("summary", "character")
    builder.add_edge("summary", "entity")

    # [character, entity] -> finalize (Fan-in)
    # LangGraph waits for all incoming edges to complete before running a node
    builder.add_edge("character", "finalize")
    builder.add_edge("entity", "finalize")
    
    builder.add_edge("finalize", END)

    return builder.compile()

# Setup a single instance for import
phase1_graph = build_phase1_graph()


# ── Async Generator wrapper for Streamlit ───────────────────────────────────

async def process_script_stream(script: str):
    """
    Yields the summary as soon as the summary node finishes,
    then yields the final ScriptContext when the whole graph finishes.
    """
    import os
    os.makedirs("outputs", exist_ok=True)
    
    inputs = {
        "raw_script": script,
        "summary": None,
        "characters_out": None,
        "entities_out": None,
        "context": None
    }
    
    summary_yielded = False
    final_context = None

    # Stream over node outputs as they complete
    async for event in phase1_graph.astream(inputs, stream_mode="updates"):
        # `event` is a dict of {node_name: {state_updates}}
        
        # When summary node completes, yield its text immediately to unlock UI
        if "summary" in event and not summary_yielded:
            yield event["summary"]["summary"]
            summary_yielded = True
            
        # When finalize node completes, capture the context
        if "finalize" in event:
            final_context = event["finalize"]["context"]
            
    # Yield the final context dict at the end
    yield final_context
