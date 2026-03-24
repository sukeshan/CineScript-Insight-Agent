from core.llm import call_llm_structured
from core.prompts import SHARED_PREFIX_SYSTEM
from models.entities import EntityMapOutput


async def run_entity_mapper(script: str) -> EntityMapOutput:
    """
    Extract scene-level storytelling entities.
    Benefits from KV cache if run simultaneously with or just after summary.
    """
    messages = [
        {"role": "system", "content": SHARED_PREFIX_SYSTEM},
        {"role": "user", "content": f"Script Text:\n{script}"},
    ]
    
    # Use Instructor-based structured extraction
    result, _usage = await call_llm_structured(
        messages=messages,
        response_model=EntityMapOutput,
        temperature=0.3
    )
    return result
