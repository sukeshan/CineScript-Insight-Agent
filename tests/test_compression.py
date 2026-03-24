from core.context_manager import compress_context, count_tokens
import json

def test_script_offloading():
    print("\n--- Testing Script Offloading ---")
    long_script = "This is a long script. " * 50000 
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": f"Here is the script:\n\n{long_script}"},
        {"role": "assistant", "content": "Script received."},
    ]
    for i in range(5):
        messages.append({"role": "user", "content": f"Q{i}"})
        messages.append({"role": "assistant", "content": f"A{i}"})
        
    initial_tokens = count_tokens(messages)
    print(f"Initial tokens: {initial_tokens}")
    compressed = compress_context(messages)
    final_tokens = count_tokens(compressed)
    print(f"Final tokens: {final_tokens}")
    
    assert final_tokens < 51200
    assert "[Raw Script Offloaded" in compressed[1]["content"]
    print("✅ Script offloading successful!")

def test_force_turn_trimming():
    print("\n--- Testing Turn-based Trimming ---")
    # Set a very small local threshold by overriding the limit or just using many messages
    messages = [
        {"role": "system", "content": "System"},
        {"role": "user", "content": "Script Placeholder"},
        {"role": "assistant", "content": "Summary"},
    ]
    # Add 20 turns
    for i in range(20):
        messages.append({"role": "user", "content": f"Very long question {i} " * 100})
        messages.append({"role": "assistant", "content": f"Very long answer {i} " * 100})
        
    # Manually trigger truncate_to_window since threshold is high
    from core.context_manager import truncate_to_window
    compressed = truncate_to_window(messages, keep_last_n=5, keep_first=3)
    
    print(f"Initial messages: {len(messages)}")
    print(f"Compressed messages: {len(compressed)}")
    
    # 3 Anchors + 5 turns (10 messages) = 13 total
    assert len(compressed) == 13
    assert compressed[0]["content"] == "System"
    assert "question 19" in compressed[-2]["content"] # Last turn is kept
    assert "question 0" not in str(compressed[3:]) # Old turns dropped
    
    print("✅ Turn-based trimming successful!")

if __name__ == "__main__":
    test_script_offloading()
    test_force_turn_trimming()

