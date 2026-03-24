import re
import os
from typing import Any


def slugify(text: str) -> str:
    """Convert a scene heading like 'INT. RIYA'S APARTMENT - NIGHT' to a filename-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[''`]", "", text)           # remove apostrophes
    text = re.sub(r"[^a-z0-9]+", "_", text)     # replace non-alphanum with _
    text = text.strip("_")
    return text


# Regex: matches lines like "SCENE 1", "SCENE 12", "  SCENE 4  " etc.
SCENE_HEADING_RE = re.compile(r"^\s*SCENE\s+(\d+)\s*$", re.IGNORECASE)


def split_scenes(script_text: str) -> list[dict[str, Any]]:
    """
    Parse a script and split it into individual scenes.
    
    Returns a list of dicts:
      [{"scene_id": "001", "slug": "INT. RIYA'S APARTMENT - NIGHT",
        "content": "...", "filepath": "outputs/scenes/scene_001_int_riyas_apartment_night.md"}]
    """
    lines = script_text.split("\n")
    scenes: list[dict[str, Any]] = []
    
    current_scene_num: str | None = None
    current_slug: str = ""
    current_lines: list[str] = []
    slug_captured = False
    
    for line in lines:
        match = SCENE_HEADING_RE.match(line)
        
        if match:
            # Save the previous scene if one exists
            if current_scene_num is not None:
                scenes.append(_build_scene_dict(current_scene_num, current_slug, current_lines))
            
            # Start a new scene
            current_scene_num = match.group(1).zfill(3)
            current_slug = ""
            current_lines = [line]
            slug_captured = False
        else:
            if current_scene_num is not None:
                current_lines.append(line)
                
                # Capture the first non-empty line after SCENE N as the slug (INT./EXT. line)
                if not slug_captured and line.strip():
                    current_slug = line.strip()
                    slug_captured = True
    
    # Don't forget the last scene
    if current_scene_num is not None:
        scenes.append(_build_scene_dict(current_scene_num, current_slug, current_lines))
    
    return scenes


def _build_scene_dict(scene_num: str, slug: str, lines: list[str]) -> dict[str, Any]:
    """Build the scene metadata dict."""
    slug_part = slugify(slug) if slug else "unknown"
    filename = f"scene_{scene_num}_{slug_part}.md"
    filepath = f"outputs/scenes/{filename}"
    content = "\n".join(lines).strip()
    
    return {
        "scene_id": scene_num,
        "slug": slug,
        "filename": filename,
        "filepath": filepath,
        "content": content,
    }


def write_scene_files(scenes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Write each scene to its own markdown file under outputs/scenes/."""
    os.makedirs("outputs/scenes", exist_ok=True)
    
    for scene in scenes:
        md_content = f"# Scene {scene['scene_id']}: {scene['slug']}\n\n{scene['content']}"
        with open(scene["filepath"], "w", encoding="utf-8") as f:
            f.write(md_content)
    
    return scenes


async def run_scene_splitter(script: str) -> list[dict[str, Any]]:
    """
    Pipeline-compatible entry point.
    Splits the script and writes scene files.
    Returns scene metadata list.
    """
    scenes = split_scenes(script)
    return write_scene_files(scenes)
