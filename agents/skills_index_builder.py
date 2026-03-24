import os
from typing import Any
from pydantic import BaseModel, Field

from core.llm import call_llm_structured
from core.prompts import SHARED_PREFIX_SYSTEM


class SceneSummaryBatch(BaseModel):
    """Chain-of-thought reasoning followed by one-line summaries for each scene."""
    thought: str = Field(
        description=(
            "Your internal reasoning before generating summaries. "
            "For each scene, briefly note the key characters, conflict, and turning point. "
            "This helps produce accurate, grounded summaries."
        )
    )
    summaries: list[str] = Field(
        description=(
            "A list of one-line summaries, one per scene. "
            "Index 0 = Scene 1, Index 1 = Scene 2, etc. "
            "Each summary must be a single concise sentence capturing the key action/event of that scene."
        )
    )


async def run_skills_index_builder(
    scenes: list[dict[str, Any]],
    raw_script: str,
) -> str:
    """
    Generate skills_index.md using the full script as context (KV cache hit).
    The SHARED_PREFIX_SYSTEM + full script prefix is already cached from
    the summary/character/entity agents that ran before this node.
    """
    if not scenes:
        return ""

    # Build scene boundary hints so the LLM knows how to segment its summaries
    scene_hints = "\n".join(
        f"- Scene {s['scene_id']}: {s['slug']}" for s in scenes
    )

    messages = [
        {"role": "system", "content": SHARED_PREFIX_SYSTEM},
        {
            "role": "user",
            "content": (
                f"Here is the full script:\n\n{raw_script}\n\n"
                f"---\n\nThe script has been segmented into {len(scenes)} scenes:\n{scene_hints}\n\n"
                "For each scene listed above, write exactly ONE concise sentence summarizing the key action."
            ),
        },
    ]

    result: SceneSummaryBatch
    result, _usage = await call_llm_structured(
        messages=messages,
        response_model=SceneSummaryBatch,
        temperature=0.3,
    )

    # Pad summaries to match scene count
    summaries = result.summaries
    while len(summaries) < len(scenes):
        summaries.append("(No summary generated)")

    # Write skills_index.md
    os.makedirs("outputs", exist_ok=True)
    index_path = "outputs/skills_index.md"

    with open(index_path, "w", encoding="utf-8") as f:
        f.write("# Skills Index\n\n")
        f.write("| Scene | File | Summary |\n")
        f.write("|---|---|---|\n")
        for scene, summary in zip(scenes, summaries):
            f.write(f"| {scene['scene_id']} | {scene['filename']} | {summary} |\n")

    return index_path
