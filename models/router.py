"""
Pydantic model for the Router Agent's decision output.
"""

from typing import Literal

from pydantic import BaseModel, Field


class RouterDecision(BaseModel):
    """Router output — classifies user intent and maps to required files."""

    intent: Literal["engagement", "emotion", "improve", "cliffhanger", "multi"] = Field(
        description="Classified user intent"
    )
    required_files: list[Literal["character_analysis.md", "entity_map.md"]] = Field(
        description="MD files required to answer this question"
    )
