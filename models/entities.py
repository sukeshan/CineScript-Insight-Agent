"""
Pydantic models for scene entities extracted by the Entity Mapper agent.
"""

from typing import Literal

from pydantic import BaseModel, Field


class SceneEntity(BaseModel):
    """A single scene-level entity with emotional and engagement metrics."""

    scene_id: int = Field(description="Sequential scene number")
    entity_type: Literal[
        "hook",
        "conflict",
        "revelation",
        "false_death",
        "cliffhanger",
        "tension_build",
        "resolution",
    ] = Field(description="Type of storytelling entity")
    valence: float = Field(
        ge=-1.0, le=1.0, description="Emotional valence: -1 (negative) to +1 (positive)"
    )
    intensity: float = Field(
        ge=0.0, le=1.0, description="Emotional intensity: 0 (weak) to 1 (strong)"
    )
    engagement_delta: float = Field(
        ge=-1.0, le=1.0, description="Audience attention gain/loss"
    )
    position_pct: float = Field(
        ge=0.0, le=100.0, description="Position in the script as percentage (0-100)"
    )
    description: str = Field(description="One-line explanation of the moment")


class EntityMapOutput(BaseModel):
    """Wrapper for the full entity map output."""

    entities: list[SceneEntity]
