import operator
from typing import Annotated, TypedDict, Any

from langgraph.graph import StateGraph, END, START

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


# --- Graph Definition ---

def build_phase1_graph() -> StateGraph:
    builder = StateGraph(PipelineState)
    
    builder.add_node("character", character_node)
    builder.add_node("entity", entity_node)
    builder.add_node("scene_splitter", scene_splitter_node)
    builder.add_node("skills_index", skills_index_node)
    builder.add_node("finalize", finalize_node)
    
    # START -> [character, entity, scene_splitter]
    builder.add_edge(START, "character")
    builder.add_edge(START, "entity")
    builder.add_edge(START, "scene_splitter")
    
    # [character, entity, scene_splitter] -> skills_index
    # We use a conditional fan-in technique: wait for all 3 to populate
    def check_parallel_completion(state: PipelineState):
        if state.get("characters_out") and state.get("entities_out") and state.get("scene_files"):
            return "skills_index"
        return END  # Wait for the others to finish
        
    builder.add_conditional_edges("character", check_parallel_completion)
    builder.add_conditional_edges("entity", check_parallel_completion)
    builder.add_conditional_edges("scene_splitter", check_parallel_completion)

    # skills_index -> finalize -> END
    builder.add_edge("skills_index", "finalize")
    builder.add_edge("finalize", END)

    return builder.compile()

# Setup a single instance for import
phase1_graph = build_phase1_graph()


# ── Async Generator wrapper for Streamlit ───────────────────────────────────

async def get_summary_only(script: str):
    """Run ONLY the summary agent and return its output."""
    import os
    os.makedirs("outputs", exist_ok=True)
    os.makedirs("outputs/scenes", exist_ok=True)
    os.makedirs("outputs/skills", exist_ok=True)
    
    summary_out = await run_summary(script)
    return summary_out


async def run_remaining_pipeline_stream(script: str, summary_out):
    """
    Yields status tuples ("status", message),
    and finally yields ("context", ScriptContext) when the whole graph finishes.
    Assumes summary_out is already computed and passed in.
    """
    inputs = {
        "raw_script": script,
        "summary": summary_out,
        "characters_out": None,
        "entities_out": None,
        "scene_files": None,
        "skills_index_path": None,
        "context": None
    }
    
    final_context = None

    # Node friendly names
    status_msg_map = {
        "character": "Extracting characters...",
        "entity": "Parsing entities...",
        "scene_splitter": "Splitting scenes...",
        "skills_index": "Building skills index...",
        "finalize": "Finalizing context..."
    }

    async for event in phase1_graph.astream(inputs, stream_mode="updates"):
        # Yield status for whatever nodes just completed or were updated
        for node_name, node_output in event.items():
            if isinstance(node_name, str) and node_name in status_msg_map:
                thoughts = []
                if isinstance(node_output, dict):
                    for val in node_output.values():
                        if hasattr(val, "thoughts") and getattr(val, "thoughts"):
                            for t in getattr(val, "thoughts"):
                                if hasattr(t, "thought"):
                                    thoughts.append(getattr(t, "thought"))
                        elif hasattr(val, "thought") and getattr(val, "thought"):
                            thoughts.append(getattr(val, "thought"))
                            
                yield "status", {"message": status_msg_map[node_name], "thoughts": thoughts}
                
        # Capture final context when it appears
        if "finalize" in event:
            final_context = event["finalize"].get("context")
            
    if final_context:
        yield "context", final_context
