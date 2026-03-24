from pydantic import BaseModel, Field


class CharacterThought(BaseModel):
    """A single reasoning step the analyst performs before extracting characters."""
    thought: str = Field(
        description=(
            "One clear reasoning step (1-2 sentences). "
            "Methodically identify every character mentioned or active in the script. "
            "Consider their primary purpose, how they change (or cause change), "
            "and what their key moments and relationships are."
        )
    )

class Character(BaseModel):
    """A single character extracted from the script."""

    name: str = Field(description="The character's name as it appears in the script.")
    role: str = Field(description="Their narrative role (e.g., Protagonist, Antagonist, Catalyst, Supporting, Foil).")
    arc: str = Field(description="Their character arc summarized as a short phrase using → notation (e.g., 'Guilt → Absolution', 'Static → Dead').")
    key_moments: list[str] = Field(description="List of 2-4 key moments or actions involving this character that define their role in the story.")
    relationships: list[str] = Field(description="List of relationships with other key characters (e.g., 'Ex-girlfriend of Arjun', 'Victim of Riya').")


class CharacterAnalysisOutput(BaseModel):
    """Wrapper for the full character analysis output."""
    thoughts: list[CharacterThought] = Field(
        description=(
            "Chain-of-thought reasoning performed BEFORE extracting the characters. "
            "Generate 2-4 thoughts to ensure you've found all relevant characters and understand their dynamics. "
            "These thoughts are internal reasoning and will NOT be shown to the user."
        )
    )
    characters: list[Character] = Field(
        description="Exhaustive list of all characters extracted from the script, with their detailed analysis."
    )
