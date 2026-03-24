
from typing import Literal

from pydantic import BaseModel, Field

class SummaryThought(BaseModel):
    """A single reasoning step the analyst performs before writing the summary."""
    thought: str = Field(
        description=(
            "One clear reasoning step (1-2 sentences). "
            "Walk through the script methodically: "
            "first identify the inciting incident and setup, "
            "then pinpoint the central conflict and what is at stake, "
            "then note the emotional tone and any tonal shifts, "
            "and finally assess how the script ends or leaves the audience."
        )
    )


class SummaryOutput(BaseModel):
    """Complete structured summary of a short-form script."""
    thoughts: list[SummaryThought] = Field(
        description=(
            "Chain-of-thought reasoning performed BEFORE writing the summary. "
            "Generate 3-4 thoughts, each covering a distinct analytical angle: "
            "(1) What is the plot setup and inciting incident? "
            "(2) What is the core conflict, who drives it, and what are the stakes? "
            "(3) What is the overall emotional tone, and does it shift? "
            "(4) How does the script end — resolved, open, cliffhanger? "
            "These thoughts are internal reasoning and will NOT be shown to the user."
        )
    )
    summary: list[str] = Field(
        description=(
            "3-4 punchy bullet points summarising the script. "
            "Each bullet is one SHORT sentence (max 15 words) in present tense. "
            "Cover: setup, conflict, climax, and ending — nothing more. "
            "Be crisp, not elaborate. No cast lists."
        )
    )
    follow_up_questions: list[str] = Field(
        # Intial follow up questions are hardcoded, later we can make them dynamic
        description=(
            "Exactly 4 follow-up question chips shown as clickable buttons to the user. "
            "These must be: "
            "'What is the emotion arc of this script?' "
            "'How engaging is this script and why?' "
            "'How can I improve this script?' "
            "'What is the cliffhanger moment?'"
        )
    )

