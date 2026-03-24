from core.llm import call_llm_structured
from core.prompts import SHARED_PREFIX_SYSTEM
from models.summary import SummaryOutput

async def run_summary(script: str) -> SummaryOutput:
    """
    Generate a short summary of the script.
    Uses shared prefix to seed KV cache for subsequent calls.
    """
    messages = [
        {"role": "system", "content": SHARED_PREFIX_SYSTEM},
        {"role": "user", "content": f"Script Text:\n{script}"},
    ]
    
    # We use structured output for the summary, including CoT and chips
    result = await call_llm_structured(
        messages=messages, 
        response_model=SummaryOutput,
        temperature=0.7
    )
    return result
