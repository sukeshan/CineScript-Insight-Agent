from core.context_manager import compress_context, count_tokens
import json

def test_compression():
    # Simulate a massively long user message and some history
    long_script = "This is a long script. " * 50000  # ~250k characters, way over 40% of 128k (which is ~51k tokens)
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": f"Here is the script:\n\n{long_script}"},
        {"role": "assistant", "content": "Script received."},
        {"role": "user", "content": "What is the theme?"},
        {"role": "assistant", "content": "The theme is endurance."},
        {"role": "user", "content": "What about the characters?"},
    ]
    
    initial_tokens = count_tokens(messages)
    print(f"Initial token count: {initial_tokens}")
    
    compressed = compress_context(messages)
    
    final_tokens = count_tokens(compressed)
    print(f"Final token count: {final_tokens}")
    print(f"Compressed turns count: {len(compressed)}")
    
    assert final_tokens < 51200
    assert "Here is the script" not in str(compressed)
    print("✅ Compression successful!")

if __name__ == "__main__":
    test_compression()
