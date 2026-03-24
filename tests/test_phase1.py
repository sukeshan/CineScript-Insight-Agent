"""
Phase 1 v2.0 pipeline test.
Verifies: summary, characters, entities, scene segmentation, skills index.
"""

import asyncio
import os
import docx
import pytest
from core.pipeline import get_summary_only, run_remaining_pipeline_stream
from core.prompts import build_main_prompt


def read_docx(file_path: str) -> str:
    """Read text from a docx file."""
    doc = docx.Document(file_path)
    return "\n".join(paragraph.text for paragraph in doc.paragraphs)


async def main():
    print("🎬 Starting Phase 1 v2.0 Pipeline...\n")
    
    script_path = os.path.join("docs", "Bullet  Assignment.docx")
    script = read_docx(script_path)
    
    print("⏳ Generating summary...")
    summary = await get_summary_only(script)
    print("✅ SUMMARY:")
    for point in summary.summary:
        print(f"  - {point}")

    # Exhaust stream
    stream = run_remaining_pipeline_stream(script, summary)
    
    # Run through the stream
    context = None
    
    async for event_type, data in stream:
        if event_type == "status":
            print(f"⏳ {data.get('message', '')}")
            for t in data.get('thoughts', []):
                print(f"   💭 {t}")
        elif event_type == "context":
            context = data
            print("\n✅ FULL CONTEXT:")

    print(f"- Characters: {len(context.characters)}")
    for c in context.characters:
        print(f"  * {c.name} ({c.role})")
        
    print(f"- Entities: {len(context.entity_map)}")
    for e in context.entity_map:
        print(f"  * Scene {e.scene_id} [{e.entity_type}]: {e.description}")
    
    print(f"\n- Scene files: {len(context.scene_files)}")
    for s in context.scene_files:
        print(f"  * {s['filepath']} → {s['slug']}")
    
    print(f"\n- Skills index: {context.skills_index_path}")
    
    # Verify files exist
    assert os.path.exists("outputs/character_analysis.md"), "character_analysis.md missing!"
    assert os.path.exists("outputs/entity_map.md"), "entity_map.md missing!"
    assert os.path.exists("outputs/skills_index.md"), "skills_index.md missing!"
    assert os.path.exists("outputs/skills/cliffhanger_detection.md"), "cliffhanger_detection.md missing!"
    assert os.path.isdir("outputs/scenes"), "scenes/ directory missing!"
    
    scene_files = os.listdir("outputs/scenes")
    assert len(scene_files) > 0, "No scene files created!"
    print(f"\n- Scene markdown files in outputs/scenes/: {len(scene_files)}")
    for f in sorted(scene_files):
        print(f"  * {f}")
    
    # Build dynamic prompt and verify it contains the skills index
    with open("outputs/skills_index.md", "r") as f:
        skills_content = f.read()
    dynamic_prompt = build_main_prompt(skills_content)
    assert "Scene Files" in dynamic_prompt
    assert "scene_" in dynamic_prompt
    print("\n✅ Dynamic system prompt contains skills index!")
    
    print("\n🎉 Phase 1 v2.0 — ALL CHECKS PASSED!")


if __name__ == "__main__":
    asyncio.run(main())
