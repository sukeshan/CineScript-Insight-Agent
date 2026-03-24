from dataclasses import dataclass, field

from models.characters import Character
from models.entities import SceneEntity


@dataclass
class ScriptContext:
    """Central context object that carries all analysis results."""

    raw_script: str                              # original uploaded text
    summary: str = ""                            # from Summary Agent
    characters: list[Character] = field(default_factory=list)   # from Character Analyst
    entity_map: list[SceneEntity] = field(default_factory=list) # from Entity Mapper
    char_md_path: str = "outputs/character_analysis.md"
    entity_md_path: str = "outputs/entity_map.md"
    scene_files: list[dict] = field(default_factory=list)       # from Scene Splitter
    skills_index_path: str = "outputs/skills_index.md"          # from Skills Index Builder
    suggested_improvements: list[str] = field(default_factory=list)
    session_token_count: int = 0
    background_ready: bool = False

