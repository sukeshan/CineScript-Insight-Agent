"""
Phase 1 v2.0 pipeline test.
Verifies: summary, characters, entities, scene segmentation, skills index.
"""

import asyncio
import os
import docx
from core.pipeline import process_script_stream
from core.prompts import build_main_prompt


def read_docx(file_path: str) -> str:
    """Read text from a docx file."""
    doc = docx.Document(file_path)
    return "\n".join(paragraph.text for paragraph in doc.paragraphs)


async def main():
    print("🎬 Starting Phase 1 v2.0 Pipeline...\n")
    
    script_path = os.path.join("docs", "Bullet  Assignment.docx")
    script = read_docx(script_path)
    
    stream = process_script_stream(script)
    
    # 1. First yield: summary
    summary = await anext(stream)
    print("✅ SUMMARY:")
    print(summary)
    
    # 2. Second yield: final ScriptContext
    context = await anext(stream)
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
