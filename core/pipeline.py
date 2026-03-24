import operator
from typing import Annotated, TypedDict, Any

from langgraph.graph import StateGraph, END

from agents.summary import run_summary
from agents.characters import run_character_analysis
from agents.entity_mapper import run_entity_mapper
from agents.scene_splitter import run_scene_splitter
from agents.skills_index_builder import run_skills_index_builder
from models.summary import SummaryOutput
from models.characters import CharacterAnalysisOutput
from models.entities import EntityMapOutput
from core.context import ScriptContext


# ── State Definition ──────────────────────────────────────────────────────────

class PipelineState(TypedDict):
    """The state dictionary flowing through the Phase 1 graph."""
    raw_script: str
    
    summary: SummaryOutput | None
    characters_out: CharacterAnalysisOutput | None
    entities_out: EntityMapOutput | None
    scene_files: list[dict[str, Any]] | None
    skills_index_path: str | None
    
    # Final consolidated context
    context: ScriptContext | None


# ── Nodes ─────────────────────────────────────────────────────────────────────

async def summary_node(state: PipelineState) -> dict:
    """Generate the summary first. This seeds the KV cache."""
    summary_out = await run_summary(state["raw_script"])
    return {"summary": summary_out}


async def character_node(state: PipelineState) -> dict:
    """Extract characters. Runs in parallel with entity mapping and scene splitting."""
    chars = await run_character_analysis(state["raw_script"])
    
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
    """Map scene entities. Runs in parallel with character extraction and scene splitting."""
    entities = await run_entity_mapper(state["raw_script"])
    
    with open("outputs/entity_map.md", "w", encoding="utf-8") as f:
        f.write("# Entity Map\n\n")
        f.write("| Scene | Type | Valence | Intensity | Eng. Delta | Pos % | Description |\n")
        f.write("|---|---|---|---|---|---|---|\n")
        for e in entities.entities:
            f.write(f"| {e.scene_id} | {e.entity_type} | {e.valence} | {e.intensity} | {e.engagement_delta} | {e.position_pct:.1f}% | {e.description} |\n")
            
    return {"entities_out": entities}


async def scene_splitter_node(state: PipelineState) -> dict:
    """Split script into individual scene markdown files. Runs in parallel."""
    scenes = await run_scene_splitter(state["raw_script"])
    return {"scene_files": scenes}


async def skills_index_node(state: PipelineState) -> dict:
    """Generate skills_index.md after scenes are split. Uses full script for KV cache hit."""
    scenes = state.get("scene_files") or []
    index_path = await run_skills_index_builder(scenes, state["raw_script"])
    return {"skills_index_path": index_path}


def finalize_node(state: PipelineState) -> dict:
    """Consolidate everything into the final ScriptContext."""
    chars = state["characters_out"].characters if state["characters_out"] else []
    ents = state["entities_out"].entities if state["entities_out"] else []
    
    ctx = ScriptContext(
        raw_script=state["raw_script"],
        summary="\n".join([f"- {s}" for s in state["summary"].summary]) if state.get("summary") else "",
        characters=chars,
        entity_map=ents,
        scene_files=state.get("scene_files") or [],
        skills_index_path=state.get("skills_index_path") or "",
        char_md_path="outputs/character_analysis.md",
        entity_md_path="outputs/entity_map.md",
        background_ready=True
    )
    return {"context": ctx}


# ── Graph Builder ─────────────────────────────────────────────────────────────

def build_phase1_graph() -> StateGraph:
    """
    Construct and compile the Phase 1 LangGraph.
    Flow: START → summary → [character, entity, scene_splitter] (parallel) → skills_index → finalize → END
    """
    builder = StateGraph(PipelineState)

    # Add nodes
    builder.add_node("summary", summary_node)
    builder.add_node("character", character_node)
    builder.add_node("entity", entity_node)
    builder.add_node("scene_splitter", scene_splitter_node)
    builder.add_node("skills_index", skills_index_node)
    builder.add_node("finalize", finalize_node)

    # START → summary (seeds KV cache)
    builder.set_entry_point("summary")

    # summary → [character, entity, scene_splitter] (parallel fan-out)
    builder.add_edge("summary", "character")
    builder.add_edge("summary", "entity")
    builder.add_edge("summary", "scene_splitter")

    # [character, entity, scene_splitter] → skills_index (fan-in)
    builder.add_edge("character", "skills_index")
    builder.add_edge("entity", "skills_index")
    builder.add_edge("scene_splitter", "skills_index")

    # skills_index → finalize → END
    builder.add_edge("skills_index", "finalize")
    builder.add_edge("finalize", END)

    return builder.compile()

# Setup a single instance for import
phase1_graph = build_phase1_graph()


# ── Async Generator wrapper for Streamlit ───────────────────────────────────

async def process_script_stream(script: str):
    """
    Yields status tuples ("status", message),
    then yields ("summary", summary_data) as soon as the summary node finishes,
    and finally yields ("context", ScriptContext) when the whole graph finishes.
    """
    import os
    os.makedirs("outputs", exist_ok=True)
    os.makedirs("outputs/scenes", exist_ok=True)
    os.makedirs("outputs/skills", exist_ok=True)
    
    inputs = {
        "raw_script": script,
        "summary": None,
        "characters_out": None,
        "entities_out": None,
        "scene_files": None,
        "skills_index_path": None,
        "context": None
    }
    
    summary_yielded = False
    final_context = None

    # Node friendly names
    status_msg_map = {
        "summary": "Generating summary...",
        "character": "Extracting characters...",
        "entity": "Parsing entities...",
        "scene_splitter": "Splitting scenes...",
        "skills_index": "Building skills index...",
        "finalize": "Finalizing context..."
    }

    async for event in phase1_graph.astream(inputs, stream_mode="updates"):
        # Yield status for whatever nodes just completed or were updated
        for node_name in event.keys():
            if isinstance(node_name, str) and node_name in status_msg_map:
                yield "status", status_msg_map[node_name]
                
        if "summary" in event and not summary_yielded:
            yield "summary", event.get("summary", {}).get("summary", [])
            summary_yielded = True
            
        if "finalize" in event:
            final_context = event["finalize"]["context"]
            
    yield "context", final_context
