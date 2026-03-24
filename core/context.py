"""
ScriptContext — single source of truth for all downstream agents.
Populated during Phase 1 and consumed by Phase 2-4 agents.
"""

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
    suggested_improvements: list[str] = field(default_factory=list)
    # ↑ tracks what Improvement Coach already suggested — avoids repetition
    session_token_count: int = 0
    # ↑ updated after every turn — triggers Phase 4 compression at 40% threshold
    background_ready: bool = False
    # ↑ set to True when character + entity analysis complete
