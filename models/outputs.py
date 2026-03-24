"""
Pydantic models for on-demand agent outputs (engagement, emotion arc, etc.).
"""

from pydantic import BaseModel, Field


class EngagementScore(BaseModel):
    """Output of the Engagement Scorer agent."""

    overall_score: float = Field(ge=0, le=10, description="Overall engagement score 0-10")
    factors: dict[str, float] = Field(
        description="Factor breakdown, e.g. hook_strength, conflict_depth, etc."
    )
    explanation: str = Field(description="Explanation of the score")
    follow_up_questions: list[str] = Field(
        description="2-3 continuable follow-up questions"
    )


class ArcBeat(BaseModel):
    """A single beat in the emotion arc."""

    position_pct: float = Field(ge=0, le=100, description="Position in script 0-100")
    emotion: str = Field(description="Dominant emotion at this beat")
    valence: float = Field(ge=-1.0, le=1.0, description="Emotional valence")
    intensity: float = Field(ge=0.0, le=1.0, description="Emotional intensity")
    description: str = Field(description="One-line summary of this beat")


class EmotionArc(BaseModel):
    """Output of the Emotion Arc Agent."""

    dominant_emotions: list[str] = Field(description="Top 2-4 dominant emotions")
    arc_beats: list[ArcBeat] = Field(description="Beat-by-beat emotion arc")
    overall_tone: str = Field(description="Overall emotional tone of the script")
    follow_up_questions: list[str] = Field(
        description="2-3 continuable follow-up questions"
    )
