"""
Pydantic models for character analysis output.
"""

from pydantic import BaseModel, Field


class Character(BaseModel):
    """A single character extracted from the script."""

    name: str = Field(description="Character name")
    role: str = Field(description="Role in the story (protagonist, antagonist, catalyst, etc.)")
    arc: str = Field(description="Character arc summary, e.g. 'Guilt → Absolution'")
    key_moments: list[str] = Field(description="Key moments involving this character")
    relationships: list[str] = Field(description="Relationships with other characters")


class CharacterAnalysisOutput(BaseModel):
    """Wrapper for the full character analysis output."""

    characters: list[Character]
