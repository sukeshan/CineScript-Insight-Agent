from core.context_manager import should_compress, drop_raw_script_message, truncate_to_window
import json

def test_script_offloading():
    print("\n--- Testing Script Offloading ---")
    long_script = "This is a long script. " * 50
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": f"Here is the script:\n\n{long_script}"},
        {"role": "assistant", "content": "Script received."},
    ]
    
    # Simulate being over threshold
    # Note: count_tokens was removed as the system now uses API-reported usage.
    compressed = drop_raw_script_message(messages)
    
    assert "[Raw Script Offloaded" in compressed[1]["content"]
    print("✅ Script offloading logic successful!")

def test_force_turn_trimming():
    print("\n--- Testing Turn-based Trimming ---")
    messages = [
        {"role": "system", "content": "System"},
        {"role": "user", "content": "Script Placeholder"},
        {"role": "assistant", "content": "Summary"},
    ]
    # Add 20 turns
    for i in range(20):
        messages.append({"role": "user", "content": f"Question {i}"})
        messages.append({"role": "assistant", "content": f"Answer {i}"})
        
    compressed = truncate_to_window(messages, keep_last_n=5, keep_first=3)
    
    print(f"Initial messages: {len(messages)}")
    print(f"Compressed messages: {len(compressed)}")
    
    # 3 Anchors + 5 turns (10 messages) = 13 total
    assert len(compressed) == 13
    assert compressed[0]["content"] == "System"
    print("✅ Turn-based trimming logic successful!")

if __name__ == "__main__":
    test_script_offloading()
    test_force_turn_trimming()

