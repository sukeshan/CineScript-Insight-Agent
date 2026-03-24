"""
Agent Tools.
Provides the LLM with read/write access to the generated markdown outputs.
"""

import os
import json

def load_file(filename: str) -> str:
    """
    Load a script analysis file to answer the user's question.
    """
    if not os.path.exists(filename):
        return f"Error: File '{filename}' not found."
        
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file '{filename}': {str(e)}"

def write_file(filepath: str, content: str) -> str:
    """
    Write content to a file. Used to generate new analysis files or modify existing ones.
    """
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote to {filepath}"
    except Exception as e:
        return f"Error writing to file '{filepath}': {str(e)}"

# Native OpenAI tool definitions
TOOLS_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "load_file",
            "description": "Load a script analysis file to answer the user's question.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "The path of the file to load (e.g. outputs/character_analysis.md or outputs/entity_map.md)"
                    }
                },
                "required": ["filename"],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write or overwrite a file with specific content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "The destination path where the file should be written"
                    },
                    "content": {
                        "type": "string",
                        "description": "The full text content to write to the file"
                    }
                },
                "required": ["filepath", "content"],
                "additionalProperties": False
            }
        }
    }
]

# Dispatcher
async def execute_tool(tool_name: str, arguments: dict) -> str:
    """Execute the tool by name using the parsed JSON arguments."""
    if tool_name == "load_file":
        return load_file(arguments.get("filename", ""))
    elif tool_name == "write_file":
        return write_file(arguments.get("filepath", ""), arguments.get("content", ""))
    else:
        return f"Error: Unknown tool {tool_name}"
