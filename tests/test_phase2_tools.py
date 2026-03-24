import asyncio
import json
from core.prompts import MAIN_SYSTEM_PROMPT
from agents.conversation_graph import conversation_graph

async def main():
    print("🎬 Starting Unified Tool-Calling Test (Structured Outputs)...\n")
    
    messages = [
        {"role": "system", "content": MAIN_SYSTEM_PROMPT},
        {"role": "user", "content": "How engaging is this script based on the entity map? Load the file, analyze it, and write a 2-sentence summary to `outputs/engagement_summary.md`."}
    ]
    
    initial_state = {"messages": messages, "token_count": 0}
    
    print("🗣️ User: How engaging is this script based on the entity map? Load the file, analyze it, and write a 2-sentence summary to `outputs/engagement_summary.md`.\n")
    
    async for event in conversation_graph.astream(initial_state, stream_mode="updates"):
        for node_name, state_update in event.items():
            print(f"🤖 --- Node '{node_name}' finished processing ---")
            
            # Print latest messages
            for msg in state_update.get("messages", []):
                role = msg.get("role")
                if role == "user" and "Observation" in str(msg.get("content", "")):
                    print(f"✅ Tool Observation: {str(msg.get('content'))[:150]}...")
                elif role == "assistant":
                    try:
                        action = json.loads(msg.get("content", "{}"))
                        print(f"🧠 Thought: {action.get('thought')}")
                        if action.get("tool_name") == "final_answer":
                            print(f"💬 Assistant response:\n{action.get('tool_args', {}).get('response', '')}\n")
                            if action.get("follow_up_chips"):
                                print("🍟 Follow-up Chips:")
                                for chip in action["follow_up_chips"]:
                                    print(f"  → {chip}")
                        else:
                            print(f"🛠️  Assistant called tool: {action.get('tool_name')} with args: {action.get('tool_args')}")
                    except Exception:
                        print(f"💬 Assistant response (Raw):\n{msg.get('content')}\n")

if __name__ == "__main__":
    asyncio.run(main())
