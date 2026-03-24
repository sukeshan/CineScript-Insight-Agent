"""
Pydantic models for scene entities extracted by the Entity Mapper agent.
"""

from typing import Literal

from pydantic import BaseModel, Field


class EntityThought(BaseModel):
    """A single reasoning step the analyst performs before mapping the scene entities."""
    thought: str = Field(
        description=(
            "One clear reasoning step (1-2 sentences). "
            "Methodically break the script down chronologically into specific storytelling beats or scenes. "
            "For each beat, identify its structural purpose (hook, conflict, revelation, etc.), "
            "the emotional valence (positive/negative), intensity, and how it impacts audience engagement."
        )
    )

class SceneEntity(BaseModel):
    """A single scene-level entity with emotional and engagement metrics."""

    scene_id: int = Field(description="Sequential number starting from 1 for each chronological scene/beat.")
    entity_type: Literal[
        "hook",
        "conflict",
        "revelation",
        "false_death",
        "cliffhanger",
        "tension_build",
        "resolution",
    ] = Field(description="The foundational structural type or purpose of this storytelling entity/beat in the narrative arc.")
    valence: float = Field(
        ge=-1.0, le=1.0, description="Emotional valence of the beat: from -1.0 (highly negative/sad/scary) to +1.0 (highly positive/joyful/relieving)."
    )
    intensity: float = Field(
        ge=0.0, le=1.0, description="Emotional intensity of the beat: from 0.0 (calm/weak) to 1.0 (extremely intense/high stakes)."
    )
    engagement_delta: float = Field(
        ge=-1.0, le=1.0, description="Pacing and attention metric: how much audience attention is gained or lost during this beat. -1.0 (massive loss) to +1.0 (massive grip)."
    )
    position_pct: float = Field(
        ge=0.0, le=100.0, description="Approximate position in the script as a percentage (0 to 100), where this scene occurs."
    )
    description: str = Field(description="A concise one-line clear explanation of exactly what happens in this narrative beat.")


class EntityMapOutput(BaseModel):
    """Wrapper for the full entity map output."""
    thoughts: list[EntityThought] = Field(
        description=(
            "Chain-of-thought reasoning performed BEFORE mapping the scene entities. "
            "Generate 3-5 thoughts walking through the script's chronological beats to ensure accurate mapping. "
            "These thoughts are internal reasoning and will NOT be shown to the user."
        )
    )
    entities: list[SceneEntity] = Field(
        description="Comprehensive chronological list of all storytelling sequence/scene beats mapped from the script."
    )
