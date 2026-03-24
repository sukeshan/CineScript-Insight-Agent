"""
Phase 1 pipeline test.
"""

import asyncio
from core.pipeline import process_script_stream


import os
import docx

def read_docx(file_path: str) -> str:
    """Read text from a docx file."""
    doc = docx.Document(file_path)
    return "\n".join(paragraph.text for paragraph in doc.paragraphs)

async def main():
    print("🎬 Starting Phase 1 Pipeline...\n")
    
    # Read from docx
    script_path = os.path.join("docs", "Bullet  Assignment.docx")
    script = read_docx(script_path)
    
    # process_script_stream yields the summary first, then the final context
    stream = process_script_stream(script)
    
    # 1. First yield is the summary (string)
    summary = await anext(stream)
    print("✅ RECEIVED SUMMARY (UI Unlocks):")
    print(summary)
    print("\n⏳ Waiting for background agents to finish character & entity extraction...\n")
    
    # 2. Second yield is the final ScriptContext object
    context = await anext(stream)
    print("✅ RECEIVED FULL CONTEXT:")
    print(f"- Characters found: {len(context.characters)}")
    for c in context.characters:
        print(f"  * {c.name} ({c.role})")
        
    print(f"- Entities found: {len(context.entity_map)}")
    for e in context.entity_map:
        print(f"  * Scene {e.scene_id} [{e.entity_type}]: {e.description} (intensity: {e.intensity})")
        
    print(f"- Markdown files written:")
    print(f"  * {context.char_md_path}")
    print(f"  * {context.entity_md_path}")


if __name__ == "__main__":
    asyncio.run(main())
