# 🎬 Script Analysis Dashboard

A premium, AI-powered platform for deep screenplay analysis. This system transforms raw script uploads into structured, actionable insights using a multi-phase agentic architecture.

## 🚀 Key Features

*   **Parallel Analytic Pipeline**: Automatically segments scenes, identifies characters, maps emotional entities, and generates a "Skills Index" for efficient retrieval.
*   **ReAct Conversational Agent**: A stateful chat interface that uses structured reasoning (Thought → Tool → Observation) to answer complex queries about the script.
*   **Context Budget Management**: Zero-latency token tracking with multi-stage compression (Offloading, Trimming, Anchoring) to sustain long-running conversations.
*   **Premium Streaming UI**: A stunning Glassmorphism dashboard built with Streamlit, featuring real-time processing indicators and a "Brain" expander for agent transparency.

---

## 🏗️ Core Architecture

The system is split into two primary engines:

### 1. The Ingestion Pipeline (`core/pipeline.py`)
Triggered immediately upon upload, this Phase 1 engine uses **LangGraph** to orchestrate several parallel specialized agents:
- **Summary Agent**: Generates the initial narrative arc and follow-up chips.
- **Character Analyst**: Extracts roles, arcs, and relationships.
- **Entity Mapper**: Maps scene-level narrative "entities" (hooks, reveals, cliffhangers).
- **Scene Splitter**: Uses Python regex to segment the script into individual markdown files.
- **Skills Index Builder**: Summarizes each scene in a batched, KV-cached call to create a retrieval index.

### 2. The Interaction Agent (`agents/conversation_graph.py`)
The Phase 2 conversation loop handles user queries after ingestion.
- **Structured Output**: Uses **Instructor** to force the agent into a `thought` and `tool_name` schema.
- **Dynamic Prompting**: Injects the `skills_index.md` into the system prompt turn-by-turn so the agent knows exactly which scene files to "load" for context.
- **Tool Retrieval**: Instead of loading the whole script, the agent selectively calls `load_file` to read characters, entities, or specific scenes.

---

## 🛠️ Tech Stack

- **LLM**: GPT-4o / GPT-4o-mini (via OpenAI & Instructor)
- **Orchestration**: LangGraph (Stateful Graphs & Parallel Execution)
- **Structured Data**: Pydantic
- **Frontend**: Streamlit (with custom CSS/Glassmorphism)
- **Text Processing**: `python-docx` & Regex

---

## 🏁 How to Run

1.  **Set up the environment**:
    ```bash
    conda create -n agent python=3.10
    conda activate agent
    pip install -r requirements.txt  # Or manually: streamlit, openai, instructor, langgraph, python-docx
    ```

2.  **Set your API Key**:
    ```bash
    export OPENAI_API_KEY='your-api-key-here'
    ```

3.  **Launch the Dashboard**:
    ```bash
    streamlit run ui/app.py
    ```

---

## 📂 Project Structure

- `agents/`: Implementation of the specialized AI agents (Summary, Scene Splitter, etc.).
- `core/`: Critical infrastructure (Pipeline, LLM client, Context Management, Prompts).
- `models/`: Pydantic schemas for structured LLM outputs.
- `ui/`: Streamlit dashboard and custom CSS assets.
- `outputs/`: The structured knowledge base generated for each script (scenes, character MDs, etc.).
- `tests/`: Automated verification scripts for Phases 1, 2, and 3.
