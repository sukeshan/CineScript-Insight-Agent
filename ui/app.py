"""
Script Analysis Dashboard — Streamlit UI (Phase 4)
Orchestrates the Phase 1 pipeline and Phase 2 conversation agent.
"""
import asyncio
import json
import os
import sys
import html

import streamlit as st

# Ensure project root is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.pipeline import get_summary_only, run_remaining_pipeline_stream
from agents.conversation_graph import conversation_graph
from core.prompts import build_main_prompt

# ── Page Config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Script Analysis Dashboard",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS (Glassmorphism Dark Theme) ────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
    --bg-primary: #0a0a14;
    --bg-secondary: #12121f;
    --bg-card: rgba(255,255,255,0.05);
    --bg-card-hover: rgba(255,255,255,0.08);
    --border-glass: rgba(255,255,255,0.1);
    --accent: #8b7fff;
    --accent-bright: #a49bff;
    --accent-glow: rgba(139,127,255,0.3);
    --gradient-start: #8b7fff;
    --gradient-end: #6dd5ed;
    --text-primary: #f0f0f8;
    --text-secondary: #c8c8dc;
    --text-muted: #9898b4;
    --success: #34d399;
    --warning: #fbbf24;
    --error: #f87171;
}

/* ── Global ──────────────────────────────────────────────────────────── */
html, body, [data-testid="stApp"] {
    font-family: 'Inter', sans-serif !important;
    background: linear-gradient(160deg, var(--bg-primary) 0%, var(--bg-secondary) 100%) !important;
    color: var(--text-primary) !important;
}

/* All text elements */
p, span, li, td, th, label, .stMarkdown {
    color: var(--text-primary) !important;
}
h1, h2, h3, h4, h5, h6 {
    color: var(--text-primary) !important;
    font-weight: 700 !important;
}

/* ── Hide chrome ─────────────────────────────────────────────────────── */
header[data-testid="stHeader"] { display: none !important; }
footer { display: none !important; }
#MainMenu { display: none !important; }

/* ── Sidebar ─────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, rgba(10,10,20,0.98), rgba(18,18,31,0.98)) !important;
    border-right: 1px solid var(--border-glass) !important;
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] li {
    color: var(--text-secondary) !important;
}
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: var(--text-primary) !important;
}
[data-testid="stSidebar"] hr {
    border-color: rgba(139,127,255,0.15) !important;
}

/* ── Chat Messages ───────────────────────────────────────────────────── */
[data-testid="stChatMessage"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-glass) !important;
    border-radius: 16px !important;
    padding: 20px !important;
    margin-bottom: 12px !important;
    backdrop-filter: blur(16px) !important;
    transition: border-color 0.3s ease !important;
}
[data-testid="stChatMessage"]:hover {
    border-color: rgba(139,127,255,0.25) !important;
}

/* ── Stream Deck Cards ───────────────────────────────────────────────── */
.stream-card {
    background: linear-gradient(135deg, rgba(139,127,255,0.06), rgba(109,213,237,0.04));
    border: 1px solid var(--border-glass);
    border-radius: 16px;
    padding: 20px 16px;
    text-align: center;
    backdrop-filter: blur(12px);
    min-height: 90px;
    transition: all 0.3s ease;
}
.stream-card:hover {
    border-color: var(--accent);
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(139,127,255,0.12);
}
.stream-card h4 {
    margin: 0 0 8px 0;
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.stream-card .status { font-size: 1.6rem; }
.stream-card.done { border-color: var(--success); }

/* Pulse animation for processing */
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}
.stream-card.loading .status { animation: pulse 1.5s ease-in-out infinite; }

/* ── Brain Expander ──────────────────────────────────────────────────── */
details.brain-expander {
    background: linear-gradient(135deg, rgba(139,127,255,0.06), rgba(139,127,255,0.02));
    border: 1px solid rgba(139,127,255,0.18);
    border-radius: 10px;
    padding: 10px 14px;
    margin-top: 10px;
    font-size: 0.82rem;
    color: var(--text-muted);
    transition: all 0.2s ease;
}
details.brain-expander[open] {
    border-color: rgba(139,127,255,0.35);
    background: rgba(139,127,255,0.08);
}
details.brain-expander summary {
    cursor: pointer;
    font-weight: 600;
    color: var(--accent-bright);
    padding: 2px 0;
}

/* ── Tool Activity Indicator ─────────────────────────────────────────── */
.tool-indicator {
    background: rgba(251,191,36,0.06);
    border-left: 3px solid var(--warning);
    border-radius: 0 10px 10px 0;
    padding: 8px 14px;
    margin: 6px 0;
    font-size: 0.8rem;
    font-weight: 500;
    color: var(--warning);
}

/* ── File Uploader ───────────────────────────────────────────────────── */
[data-testid="stFileUploader"] {
    border: 2px dashed rgba(139,127,255,0.3) !important;
    border-radius: 16px !important;
    padding: 24px !important;
    transition: all 0.3s ease !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: var(--accent) !important;
    background: rgba(139,127,255,0.04) !important;
}

/* ── Buttons (Chips) ─────────────────────────────────────────────────── */
.stButton > button {
    border-radius: 24px !important;
    border: 1px solid var(--accent) !important;
    color: var(--accent-bright) !important;
    background: rgba(139,127,255,0.06) !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    padding: 8px 18px !important;
    transition: all 0.25s ease !important;
    letter-spacing: 0.2px !important;
}
.stButton > button:hover {
    background: var(--accent-glow) !important;
    box-shadow: 0 0 20px rgba(139,127,255,0.2) !important;
    transform: translateY(-1px) !important;
    color: #fff !important;
}

/* ── Expander in sidebar ─────────────────────────────────────────────── */
[data-testid="stExpander"] {
    border: 1px solid var(--border-glass) !important;
    border-radius: 10px !important;
    background: var(--bg-card) !important;
}

/* ── Chat Input ──────────────────────────────────────────────────────── */
[data-testid="stChatInput"] textarea {
    color: var(--text-primary) !important;
    background: var(--bg-card) !important;
    border: 1px solid var(--border-glass) !important;
    border-radius: 12px !important;
}

/* ── Spinner ──────────────────────────────────────────────────────────── */
.stSpinner > div { color: var(--accent-bright) !important; }

/* ── Tables ──────────────────────────────────────────────────────────── */
table { border-collapse: collapse; width: 100%; }
th {
    background: rgba(139,127,255,0.1) !important;
    color: var(--accent-bright) !important;
    font-weight: 600;
    padding: 8px 12px;
    border-bottom: 1px solid var(--border-glass);
    text-align: left;
}
td {
    padding: 6px 12px;
    border-bottom: 1px solid rgba(255,255,255,0.04);
    color: var(--text-secondary) !important;
}
tr:hover td { background: rgba(139,127,255,0.04); }

/* ── Scrollbar ───────────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
    background: rgba(139,127,255,0.25);
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover { background: rgba(139,127,255,0.4); }
</style>
""", unsafe_allow_html=True)


# ── Session State Init ───────────────────────────────────────────────────────

def init_state():
    defaults = {
        "messages": [],
        "agent_messages": [],
        "token_count": 0,
        "context": None,
        "summary_out": None,
        "processing": False,
        "pipeline_pending": False,
        "script_text": ""
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ── Async Helper ─────────────────────────────────────────────────────────────

def run_async(coro):
    """Run an async coroutine in Streamlit's sync context."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def run_async_stream(async_gen):
    """Run an async generator in Streamlit's sync context and yield its items."""
    loop = asyncio.new_event_loop()
    try:
        while True:
            try:
                yield loop.run_until_complete(async_gen.__anext__())
            except StopAsyncIteration:
                break
    finally:
        loop.close()

async def _finish_pipeline_async(status_container):
    results = []
    async for event_type, content in run_remaining_pipeline_stream(st.session_state.script_text, st.session_state.summary_out):
        if event_type == "status":
            msg = content.get("message", "Processing...")
            thoughts = content.get("thoughts", [])
            status_container.update(label=f"⏳ {msg}", state="running")
            for t in thoughts:
                status_container.markdown(f"💭 *Thought:* {t}")
        elif event_type == "context":
            results.append(("context", content))
            
    status_container.update(label="✅ Analysis Complete!", state="complete")
    return results

def finish_pipeline(status_container):
    return run_async(_finish_pipeline_async(status_container))


# ── Agent Runner ─────────────────────────────────────────────────────────────

async def _run_agent_async_stream(user_message: str):
    agent_msgs = list(st.session_state.agent_messages)
    agent_msgs.append({"role": "user", "content": user_message})
    state = {"messages": agent_msgs, "token_count": st.session_state.token_count}

    async for event in conversation_graph.astream(state, stream_mode="updates"):
        yield event


def process_user_message(user_message: str):
    """Run the conversation graph and append results to chat history."""
    if st.session_state.pipeline_pending:
        st.session_state.processing = True
        status_container = st.status("🚀 Finishing script analysis...", expanded=True)
        results = finish_pipeline(status_container)
        for event_type, data in results:
            if event_type == "context":
                st.session_state.context = data
        st.session_state.pipeline_pending = False
        st.session_state.processing = False

    max_attempts = 2
    steps = []
    success = False
    
    for attempt in range(max_attempts):
        try:
            with st.status("🧠 Thinking...", expanded=True) as status_container:
                for step in run_async_stream(_run_agent_async_stream(user_message)):
                    steps.append(step)
                    if "agent" in step:
                        agent_msg = step["agent"]["messages"][-1]
                        try:
                            action = json.loads(agent_msg.get("content", "{}"))
                            thought = action.get("thought", "")
                            tool_name = action.get("tool_name", "")
                            if thought:
                                status_container.markdown(f"💭 **Thought:** {thought}")
                            if tool_name and tool_name != "final_answer":
                                status_container.markdown(f"🔧 **Running tool:** `{tool_name}`")
                        except Exception:
                            pass
                    elif "tools" in step:
                        status_container.markdown("✅ Generated observation")
                    
                    # Check for compression signal
                    if "agent" in step and step["agent"].get("compression_triggered"):
                        st.toast("📉 **Context Budget Exceeded**: Compressing conversation history to save tokens...", icon="💡")
                        
                status_container.update(label="✅ Response ready", state="complete")
            success = True
            break
        except Exception as e:
            if attempt < max_attempts - 1:
                st.toast("⚠️ LLM formatting failed. Retrying...")
                import time
                time.sleep(1)
            else:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "⚠️ **Failed to generate a response.** The AI model encountered repeated formatting errors. Please try asking again.",
                    "chips": []
                })
                return

    if not success:
        return

    tool_activities = []
    final_response = ""
    all_thoughts = []
    final_chips = []

    for step in steps:
        if "agent" in step:
            agent_msg = step["agent"]["messages"][-1]
            try:
                action = json.loads(agent_msg.get("content", "{}"))
                thought = action.get("thought", "")
                if thought:
                    all_thoughts.append(thought)
                    
                tool_name = action.get("tool_name", "")
                tool_args = action.get("tool_args", {})

                if tool_name == "final_answer":
                    final_response = action.get("response", "")
                    final_chips = action.get("follow_up_chips", []) or []
                elif tool_name in ["load_file", "write_file"]:
                    tool_activities.append(
                        f"{tool_name}({', '.join(f'{k}={v}' for k, v in tool_args.items())})"
                    )
            except Exception:
                pass

        if "agent" in step and "token_count" in step["agent"]:
            st.session_state.token_count = step["agent"]["token_count"]
            
    final_thought = "\n\n".join(all_thoughts)

    # Update the persistent agent messages
    st.session_state.agent_messages.append({"role": "user", "content": user_message})
    st.session_state.agent_messages.append({"role": "assistant", "content": final_response})

    # Add to display messages
    st.session_state.messages.append({
        "role": "assistant",
        "content": final_response,
        "thought": final_thought,
        "tool_activity": tool_activities if tool_activities else None,
        "chips": final_chips,
    })


# ── Sidebar: Knowledge Hub ───────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🎬 Script Analysis")
    st.markdown("---")

    if st.session_state.context:
        ctx = st.session_state.context

        st.markdown("### 📁 Skills Index")
        if ctx.skills_index_path and os.path.exists(ctx.skills_index_path):
            with open(ctx.skills_index_path, "r") as f:
                st.markdown(f.read(), unsafe_allow_html=True)
        else:
            st.caption("No skills index yet.")

        st.markdown("---")
        st.markdown("### 📑 Analysis Documents")

        doc_files = {
            "Characters": ctx.char_md_path,
            "Entity Map": ctx.entity_md_path,
            "Cliffhanger Skill": "outputs/skills/cliffhanger_detection.md",
        }
        for label, path in doc_files.items():
            if os.path.exists(path):
                with st.expander(f"📄 {label}"):
                    with open(path, "r") as f:
                        st.markdown(f.read())

        st.markdown("---")
        st.markdown(f"**Token Count**: `{st.session_state.token_count:,}`")
    elif st.session_state.pipeline_pending:
        st.info("Subflows (Characters, Entities) will begin processing automatically when you start chatting.")
    else:
        st.caption("Upload a script to begin analysis.")


# ── Main Area ────────────────────────────────────────────────────────────────

st.markdown("# 🎬 Script Analysis Dashboard")

# ── File Upload ──────────────────────────────────────────────────────────────

if not st.session_state.summary_out:
    uploaded = st.file_uploader(
        "Upload your script (.docx)",
        type=["docx"],
        help="Upload a .docx screenplay to begin deep analysis.",
    )

    if uploaded and not st.session_state.processing:
        st.session_state.processing = True

        from docx import Document
        doc = Document(uploaded)
        script_text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        st.session_state.script_text = script_text

        with st.status("🚀 Generating summary...", expanded=False) as status_container:
            summary_out = run_async(get_summary_only(script_text))
            status_container.update(label="✅ Summary Complete!", state="complete")

        st.session_state.summary_out = summary_out
        st.session_state.pipeline_pending = True
        st.session_state.processing = False

        summary_text = "\n".join(f"- {s}" for s in summary_out.summary)
        st.session_state.messages.append({
            "role": "assistant",
            "content": summary_text,
            "chips": summary_out.follow_up_questions,
        })

        st.session_state.agent_messages = [
            {"role": "system", "content": build_main_prompt()},
            {"role": "user", "content": f"Here is the script:\n\n{script_text}"},
            {"role": "assistant", "content": f"Summary:\n\n{summary_text}"},
        ]

        st.rerun()


# ── Chat Interface ───────────────────────────────────────────────────────────

if st.session_state.summary_out:
    for msg in st.session_state.messages:
        role = msg["role"]
        with st.chat_message(role, avatar="🎬" if role == "assistant" else "👤"):
            st.markdown(msg["content"])

            if msg.get("thought"):
                st.markdown(
                    f'<details class="brain-expander"><summary>🧠 Agent Reasoning</summary>\n\n'
                    f'{html.escape(msg["thought"])}\n</details>',
                    unsafe_allow_html=True,
                )

            if msg.get("tool_activity"):
                for tool_act in msg["tool_activity"]:
                    st.markdown(
                        f'<div class="tool-indicator">🔧 {html.escape(tool_act)}</div>',
                        unsafe_allow_html=True,
                    )

    # Follow-up chips
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
        last_msg = st.session_state.messages[-1]
        chips = last_msg.get("chips", [])
        if chips:
            chip_cols = st.columns(min(len(chips), 4))
            for i, chip in enumerate(chips):
                with chip_cols[i]:
                    if st.button(chip, key=f"chip_{len(st.session_state.messages)}_{i}"):
                        st.session_state.chip_clicked = chip
                        st.rerun()

    # Deferred chip processing at root layout
    if st.session_state.get("chip_clicked"):
        chip = st.session_state.chip_clicked
        st.session_state.chip_clicked = None
        st.session_state.messages.append({"role": "user", "content": chip})
        with st.chat_message("user", avatar="👤"):
            st.markdown(chip)
        process_user_message(chip)
        st.rerun()

    # Chat input
    user_input = st.chat_input(
        "Ask about your script...",
        disabled=st.session_state.processing,
    )

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)
        process_user_message(user_input)
        st.rerun()
