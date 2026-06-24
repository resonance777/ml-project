"""
app.py — Streamlit web UI for the Roman Empire RAG system
=========================================================
A friendly, click-to-ask interface over the same RAG pipeline used by the CLI.

Run:
    streamlit run src/app.py
    # or, if the bare `streamlit` command is unavailable:
    python -m streamlit run src/app.py

Features
--------
* Paste your Gemini (or Anthropic) API key right in the sidebar — no .env needed.
* One-click example questions.
* Synthesised, cited answer plus the retrieved source passages with scores.
* Optional "Compare: with vs. without RAG" view for the before/after demo.
* Adjustable top-k and minimum-similarity controls.
"""

from __future__ import annotations

import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rag_pipeline import RAGPipeline, active_model, llm_provider  # noqa: E402

st.set_page_config(page_title="Roman Empire RAG", page_icon="🏛️", layout="wide")


# --------------------------------------------------------------------------- #
# Pipeline loading (cached so the model + index load only once per session)
# --------------------------------------------------------------------------- #
@st.cache_resource(show_spinner="Loading index and embedding model…")
def get_pipeline() -> RAGPipeline:
    return RAGPipeline().build()


EXAMPLE_QUESTIONS = [
    "Why did the Western Roman Empire fall?",
    "How was the Roman legion organised and equipped?",
    "What goods did Rome trade and with whom?",
    "How did Christianity become the official religion of Rome?",
    "Who were the Five Good Emperors?",
    "What rights did Roman women have?",
]


# --------------------------------------------------------------------------- #
# Sidebar — configuration
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.header("⚙️ Settings")

    st.subheader("API key")
    provider_choice = st.radio(
        "Provider", ["Gemini", "Anthropic Claude"], index=0, horizontal=False
    )
    key_input = st.text_input(
        "Paste your API key",
        type="password",
        help="Stored only for this session (not saved to disk).",
    )
    if key_input:
        if provider_choice == "Gemini":
            os.environ["GEMINI_API_KEY"] = key_input.strip()
            os.environ.pop("ANTHROPIC_API_KEY", None)
        else:
            os.environ["ANTHROPIC_API_KEY"] = key_input.strip()
            os.environ.pop("GEMINI_API_KEY", None)

    provider = llm_provider()
    if provider:
        st.success(f"LLM ready: **{provider}** · `{active_model()}`")
    else:
        st.warning("No key set → **extractive mode** (shows top passages only).")

    st.divider()
    st.subheader("Retrieval")
    top_k = st.slider("Chunks to retrieve (k)", 1, 8, 4)
    min_score = st.slider("Min similarity score", 0.0, 1.0, 0.0, 0.05)
    show_sources = st.checkbox("Show source passages", value=True)
    compare_mode = st.checkbox("Compare: with vs. without RAG", value=False)

    st.divider()
    st.caption("Source: a generated 11-page PDF on the Roman Empire.")


# --------------------------------------------------------------------------- #
# Main area
# --------------------------------------------------------------------------- #
st.title("🏛️ Ancient Empire Q&A — The Roman Empire")
st.write(
    "Ask anything about Roman politics, military, economy, culture, or society. "
    "Answers are grounded in the source document and cite their sections."
)

pipeline = get_pipeline()

# Track the current question across reruns (so example buttons work).
if "question" not in st.session_state:
    st.session_state.question = ""

st.write("**Try an example:**")
cols = st.columns(3)
for i, q in enumerate(EXAMPLE_QUESTIONS):
    if cols[i % 3].button(q, use_container_width=True):
        st.session_state.question = q

question = st.text_input(
    "Your question",
    value=st.session_state.question,
    placeholder="e.g. What was the Crisis of the Third Century?",
)

ask = st.button("Ask 🔍", type="primary")


def render_sources(contexts) -> None:
    st.subheader("📚 Retrieved sources")
    for i, r in enumerate(contexts, 1):
        with st.expander(f"{i}. [{r.chunk.section}] · similarity {r.score:.3f}"):
            st.write(r.chunk.text)


if ask and question.strip():
    st.session_state.question = question

    if compare_mode and provider:
        # Stacked full-width so both answers are fully readable (the no-context
        # answer is often long and gets cramped in a narrow column).
        st.markdown("### ❌ Without RAG — model answers from memory only")
        with st.spinner("Asking the model with no context…"):
            base = pipeline.answer_without_rag(question)
        st.info(base.answer)
        st.caption(f"model={base.model} · {base.latency_s:.2f}s")

        st.markdown("### ✅ With RAG — grounded in the document")
        with st.spinner("Retrieving context and answering…"):
            ans = pipeline.answer(question, k=top_k, min_score=min_score)
        st.success(ans.answer)
        st.caption(
            f"mode={ans.mode} · model={ans.model} · "
            f"{len(ans.contexts)} chunks · {ans.latency_s:.2f}s"
        )
        if show_sources and ans.contexts:
            render_sources(ans.contexts)
    else:
        with st.spinner("Retrieving context and answering…"):
            ans = pipeline.answer(question, k=top_k, min_score=min_score)
        st.subheader("💬 Answer")
        if ans.mode == "rag":
            st.success(ans.answer)
        else:
            st.info(ans.answer)
        st.caption(
            f"mode={ans.mode} · model={ans.model} · "
            f"{len(ans.contexts)} chunks retrieved · {ans.latency_s:.2f}s"
        )
        if show_sources and ans.contexts:
            render_sources(ans.contexts)

elif ask:
    st.warning("Please type a question first.")
