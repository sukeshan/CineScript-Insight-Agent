"""
Character Analyst — Phase 1.
Extracts character names, roles, arcs, key moments, and relationships.
"""

from core.llm import call_llm_structured
from core.prompts import SHARED_PREFIX_SYSTEM
from models.characters import CharacterAnalysisOutput


async def run_character_analysis(script: str) -> CharacterAnalysisOutput:
    """
    Extract structured character data from the script.
    Benefits from KV cache if run simultaneously with or just after summary.
    """
    messages = [
        {"role": "system", "content": SHARED_PREFIX_SYSTEM},
        {"role": "user", "content": f"Script Text:\n{script}"},
    ]
    
    # Use Instructor-based structured extraction
    result = await call_llm_structured(
        messages=messages,
        response_model=CharacterAnalysisOutput,
        temperature=0.3
    )
    return result
