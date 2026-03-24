# Script Analysis System — Design Document

> AI Engineer Assignment | Bullet — Generative AI & Content Intelligence

---

## Overview

An agentic AI system that analyzes short-form scripts and generates structured storytelling insights through a unified, memory-aware pipeline.

The system follows a continuous intelligence loop:

1. **Upload & Initial Insight** — On script upload, a summary is generated immediately while character analysis, entity mapping, and scene splitting run in the background using a shared KV cache.
2. **Stateful Conversation Agent** — A LangGraph-based ReAct agent maintains conversation memory and uses specialized tools to pull deep insights from the pre-generated analysis files.
3. **Context Budget Management** — Automated context engineering triggers at 40% of the model's limit, compressing the history and removing the raw script to maintain optimal performance.

---

## Core Design Principles

| Principle | Description |
|---|---|
| **Progressive disclosure** | Summary shown instantly; background analysis completes silently; deeper insights on demand |
| **Shared KV-cache prefix** | Background tasks share a common system + script prefix to maximize prompt caching performance |
| **Parallel Processing** | Summary, character analysis, entity mapping, and scene splitting execute concurrently on upload |
| **Unified Context** | A single `ScriptContext` serves as the source of truth for all downstream tools and responses |
| **Skill-based Architecture** | Generated analysis files are treated as "skills" that the agent can load only when relevant |
| **ReAct Tool Pattern** | The model reasons about questions and autonomously calls `load_file` or `write_file` to fulfill requests |
| **Context Awareness** | Automatic compression and script-dropping at 40% context budget to avoid window overflow |
| **Interactive Feedback** | Every response ends with contextually relevant "follow-up chips" to guide the user deeper |

---

## System Architecture — Unified Flow

```mermaid
flowchart TD
    Upload(["🎬 Script Upload\nStreamlit file input"]):::gray --> Pre["Validate & Preprocess\nextract text · metadata"]:::gray
    Pre --> Lock(["🔒 UI Locked\ntyping bar hidden"]):::gray
    Lock --> Prefix["Shared Prefix Builder\nsystem: static analyst prompt\nuser: script text\nassistant: Script received\nKV Cache Boundary"]:::teal

    Prefix -->|"seed cache"| SA["Summary Agent"]:::purple
    Prefix -->|"Background Parallel"| CA["Character Analyst"]:::coral
    Prefix -->|"Background Parallel"| EM["Entity Mapper"]:::amber
    Prefix -->|"Background Parallel"| SS["Scene Splitter"]:::teal

    SA -->|"resolves first"| SUM(["✅ Summary shown\n+ follow-up questions\ntyping bar unlocked"]):::purple

    CA -->|"wait"| SI["Skills Index Builder"]:::teal
    EM -->|"wait"| SI
    SS -->|"wait"| SI

    SI --> Fin["Finalize Context"]:::teal
    Fin --> SC[("ScriptContext\n.md files ready")]:::teal

    SUM -->|"user asks question"| Agent["LangGraph ReAct Agent\nUnified State Memory"]:::blue
    SC -->|"file paths registered"| Agent

    Agent -->|"needs data"| Tool{"execute_tool"}:::amber
    Tool -->|"load_file / write_file"| Agent
    Agent -->|"final_answer"| Response(["💬 Response\n+ follow-up questions"]):::gray

    Response --> Budget{"Context at\n40% of limit?"}:::amber
    Budget -->|"no"| Agent
    Budget -->|"yes"| Compress["Context Compression\nRemove raw script from prompt\nCompress older turns"]:::coral
    Compress --> Agent

    classDef gray   fill:#888780,stroke:#5F5E5A,color:#fff
    classDef teal   fill:#1D9E75,stroke:#0F6E56,color:#fff
    classDef purple fill:#7F77DD,stroke:#534AB7,color:#fff
    classDef coral  fill:#D85A30,stroke:#993C1D,color:#fff
    classDef amber  fill:#BA7517,stroke:#854F0B,color:#fff
    classDef blue   fill:#185FA5,stroke:#0C447C,color:#fff
```

---

## Background Analysis & Initial Summary

### Orchestration

The system uses `asyncio` to manage concurrency. The summary seeds the KV cache, while the deep analysts (Character, Entity, Scene) follow immediately to hit the warm cache.

```mermaid
flowchart TD
    A(["🎬 Script Upload\nStreamlit — file only"]):::gray --> B["Validate & Preprocess\nextract text · metadata"]:::gray
    B --> Lock(["🔒 UI Locked — typing bar hidden\nloading state shown"]):::gray
    Lock --> C["Shared Prefix Builder\nsystem: static analyst prompt\nuser: script text\nassistant: Script received\nKV Cache Boundary"]:::teal

    C -->|"1 — seed cache"| D["Summary Agent\n3–4 line synopsis\nplot · stakes · tone"]:::purple
    C -->|"2 — Parallel"| E["Character Analyst\nextract characters"]:::coral
    C -->|"2 — Parallel"| F["Entity Mapper\nmap scene entities"]:::amber
    C -->|"2 — Parallel"| G["Scene Splitter\nsplit into .md files"]:::teal

    D -->|"resolves first"| H(["✅ Summary shown to user\ntyping bar unlocked\nfollow-up questions shown"]):::purple

    E -->|"completion"| I["Skills Index Builder\nindex all skills & files"]:::teal
    F -->|"completion"| I
    G -->|"completion"| I

    I --> J["Finalize Context"]:::teal
    J --> K[("ScriptContext\ncharacter_analysis.md\nentity_map.md\nscene_files")]:::teal

    classDef gray   fill:#888780,stroke:#5F5E5A,color:#fff
    classDef teal   fill:#1D9E75,stroke:#0F6E56,color:#fff
    classDef purple fill:#7F77DD,stroke:#534AB7,color:#fff
    classDef coral  fill:#D85A30,stroke:#993C1D,color:#fff
    classDef amber  fill:#BA7517,stroke:#854F0B,color:#fff
```

### KV Cache Firing Sequence

```mermaid
sequenceDiagram
    participant App as 🐍 App (asyncio)
    participant OpenAI as ☁️ OpenAI API
    participant UI as 🖥️ Streamlit UI

    App->>OpenAI: [1] summary_task — base_prefix + "generate synopsis"
    Note over OpenAI: Caches base_prefix on inference node 🔒
    App->>OpenAI: [2] char_task — base_prefix + "extract characters" ✅ cache hit
    App->>OpenAI: [3] entity_task — base_prefix + "map entities" ✅ cache hit
    Note over App: Parallel tasks run via asyncio.gather/create_task
    OpenAI-->>UI: Summary resolves → shown immediately, typing bar unlocked
    OpenAI-->>App: Characters resolve → written to character_analysis.md
    OpenAI-->>App: Entities resolve → written to entity_map.md
    Note over App: ScriptContext fully populated 🎯
```

---

## Unified Tool-Use Conversation Architecture

### Intelligent Retrieval

Instead of static routing, the conversation agent uses a ReAct (Reasoning and Acting) loop. It evaluates the user's question, determines which analysis file contains the answer, and uses tools to load that data into its working memory.

```mermaid
flowchart TD
    A(["User question"]):::gray --> B["LangGraph State Memory\n+ tools registered"]:::blue

    B --> C{"Agent Decision\nReAct Loop"}:::blue

    C -->|"load_file / write_file"| D["Execute Tool"]:::coral
    D -->|"observation"| C

    C -->|"final_answer"| E(["💬 Response\n+ follow-up chips"]):::gray

    classDef gray   fill:#888780,stroke:#5F5E5A,color:#fff
    classDef teal   fill:#1D9E75,stroke:#0F6E56,color:#fff
    classDef blue   fill:#185FA5,stroke:#0C447C,color:#fff
    classDef coral  fill:#D85A30,stroke:#993C1D,color:#fff
```

### System Prompt Structure

The agent is instructed to treat each generated file as a "skill".

```python
MAIN_SYSTEM_PROMPT = """
You are a script analysis assistant. You help users understand and improve their scripts.
You can answer questions about engagement, emotional arcs, cliffhangers, and improvements.

## Your skills (files you can load)

### Skill: character_analysis
- File: character_analysis.md
- Contains: character names, roles, dramatic arcs, relationships, key moments

### Skill: entity_map
- File: entity_map.md  
- Contains: scene-level entities (hook, conflict, revelation, etc.)

## Rules
- Load only the file the question actually needs using your tools.
- After answering, always generate 2–3 follow-up question chips.
- Never re-run background analysis. Use only the MD files and history.
"""
```

---

## Context Budget Management

### Strategy

- **Trigger**: Runs at **40% of the model's context window**.
- **Priority 1**: Drop the raw script message (retained only for the initial summary seeding).
- **Priority 2**: Truncate/Compress older turns while keeping the system prompt and the latest context.

---

## Project Structure

```
script-analysis/
│
├── agents/
│   ├── summary.py           # Initial Summary Generator
│   ├── characters.py        # Character Analyst
│   ├── entity_mapper.py     # Entity Mapper
│   ├── scene_splitter.py    # Script Scene Fragmenter
│   ├── skills_index_builder.py # Skills/Files Indexer
│   └── conversation_graph.py# Stateful ReAct Agent (LangGraph)
│
├── core/
│   ├── context.py           # ScriptContext source of truth
│   ├── pipeline.py          # Pipeline orchestration
│   ├── context_manager.py   # 40% threshold compression logic
│   ├── llm.py               # Structured output & token tracking
│   └── prompts.py           # Dynamic system prompt builder
│
├── models/                  # Pydantic output schemas
│   ├── entities.py          
│   ├── characters.py        
│   └── summary.py           
│
├── ui/
│   └── app.py               # Streamlit Dashboard & Chat Interface
│
├── outputs/                 # Analysis assets
│   ├── character_analysis.md
│   ├── entity_map.md
│   └── skills_index.md
│
└── requirements.txt
```

---

## Tech Stack

| Layer | Choice | Reason |
|---|---|---|
| **LLM** | GPT-4o | Structured output + prompt caching + 128k window |
| **Logic** | Python / Asyncio | High concurrency for background tasks |
| **Orchestration** | LangGraph | State management for tool-use loops |
| **Parsing** | Pydantic v2 | Guaranteed schema compliance for all agents |
| **UI** | Streamlit | Rapid prototyping with native chat & file support |
| **Memory** | ScriptContext | Centralized state to avoid redundant LLM calls |

---

## Possible Improvements

- Chunking + map-reduce for feature-length scripts
- Persist ScriptContext to SQLite or Redis for session resumption
- Embeddings-based semantic search over MD files instead of full file loading
- Stream tokens from each Phase 2 agent to Streamlit for lower perceived latency
- Multi-script comparison mode (compare two drafts, show what changed in arc/engagement)
- Fine-tune a small classifier for entity type labelling to remove LLM hallucination risk
- Confidence scores on engagement factors and emotion labels