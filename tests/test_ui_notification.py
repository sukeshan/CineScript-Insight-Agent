import asyncio
import json
from unittest.mock import AsyncMock, patch
from agents.conversation_graph import agent_node, AgentAction

async def test_compression_signal():
    print("\n--- Testing Compression Signal in agent_node ---")
    
    # Mock state with token count ABOVE threshold (400,000 * 0.40 = 160,000)
    state = {
        "messages": [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "Here is the script:\n\nSome script content..."},
            {"role": "assistant", "content": "Script received."}
        ],
        "token_count": 170000 # Above 160,000 threshold
    }
    
    # Mock LLM response
    mock_action = AgentAction(
        thought="The context is full, I should continue.",
        tool_name="final_answer",
        response="I am responding.",
        follow_up_chips=["Q1", "Q2"]
    )
    mock_usage = {"total_tokens": 171000}
    
    with patch("agents.conversation_graph.call_llm_structured", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = (mock_action, mock_usage)
        
        # Run agent_node
        result = await agent_node(state)
        
        # Verify compression was triggered
        assert result["compression_triggered"] is True
        print("✅ Signal correctly set to True when above threshold.")
        
        # Check if raw script was dropped in the messages sent to LLM
        # The node modifies the messages before calling LLM
        call_args = mock_llm.call_args[1]
        sent_messages = call_args["messages"]
        assert "[Raw Script Offloaded" in sent_messages[1]["content"]
        print("✅ Raw script was correctly offloaded.")

async def test_no_compression_signal():
    print("\n--- Testing No Compression Signal in agent_node ---")
    
    # Mock state with token count BELOW threshold
    state = {
        "messages": [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "Here is the script:\n\nSome script content..."},
            {"role": "assistant", "content": "Script received."}
        ],
        "token_count": 50000 # Well below 160,000 threshold
    }
    
    mock_action = AgentAction(
        thought="Processing normally.",
        tool_name="final_answer",
        response="I am responding.",
        follow_up_chips=["Q1", "Q2"]
    )
    mock_usage = {"total_tokens": 51000}
    
    with patch("agents.conversation_graph.call_llm_structured", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = (mock_action, mock_usage)
        
        result = await agent_node(state)
        
        assert result["compression_triggered"] is False
        print("✅ Signal correctly set to False when below threshold.")

if __name__ == "__main__":
    asyncio.run(test_compression_signal())
    asyncio.run(test_no_compression_signal())
