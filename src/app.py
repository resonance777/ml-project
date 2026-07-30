"""
app.py — Streamlit web UI for the Roman Empire RAG system
=========================================================
A dark, editorial interface over the same RAG pipeline used by the CLI.

Run:
    streamlit run src/app.py
    # or, if the bare `streamlit` command is unavailable:
    python -m streamlit run src/app.py

Features
--------
* Paste your Gemini (or Anthropic) API key right in the sidebar — no .env needed.
* "Ask the Emperor": the same grounded RAG answer, voiced by Marcus Aurelius,
  Cicero, or a veteran legionary (retrieval and citations are identical).
* Knowledge graph of the document — click a node to ask about it.
* Timeline of dated events — events cited in the answer light up in gold.
* Embedding map — a 2-D PCA of all chunks showing where the question lands.
* Optional "Compare: with vs. without RAG" view for the before/after demo.
"""

from __future__ import annotations

import html
import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from build_graph import load_graph  # noqa: E402
from rag_pipeline import RAGPipeline, active_model, llm_provider  # noqa: E402
from viz import (  # noqa: E402
    chunk_map_figure,
    compute_chunk_map,
    knowledge_graph_figure,
    timeline_figure,
    years_in_text,
)

st.set_page_config(page_title="ROMA — Ancient Empire Q&A", page_icon="🏛️", layout="wide")

# --------------------------------------------------------------------------- #
# Styling — warm dark surfaces, one gold accent, a classical serif for display
# --------------------------------------------------------------------------- #
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;0,700;1,500&display=swap');

/* ---- type ---- */
.hero-kicker {
    font-family: system-ui, "Segoe UI", sans-serif;
    font-size: 0.78rem; letter-spacing: 0.42em; text-transform: uppercase;
    color: #c98500; margin-bottom: 0.4rem;
}
.hero-title {
    font-family: 'Cormorant Garamond', Georgia, serif;
    font-size: 3.4rem; font-weight: 600; line-height: 1.05;
    letter-spacing: -0.01em; color: #f4f1e8; margin: 0 0 0.5rem 0;
    text-wrap: balance;
}
.hero-sub {
    color: #898781; font-size: 1.02rem; max-width: 46rem; line-height: 1.6;
    margin-bottom: 0.2rem;
}
.gold-rule {
    border: none; height: 1px; margin: 1.1rem 0 0.4rem 0;
    background: linear-gradient(90deg, #c98500 0%, rgba(201,133,0,0.25) 45%, transparent 100%);
}
h2, h3, [data-testid="stMarkdownContainer"] h2, [data-testid="stMarkdownContainer"] h3 {
    font-family: 'Cormorant Garamond', Georgia, serif;
    letter-spacing: 0.01em; font-weight: 600;
}
.section-label {
    font-size: 0.72rem; letter-spacing: 0.34em; text-transform: uppercase;
    color: #898781; margin: 0.4rem 0 0.6rem 0;
}

/* ---- answer card ---- */
.answer-card {
    background: #1a1a19;
    border: 1px solid rgba(244,241,232,0.08);
    border-left: 3px solid #c98500;
    border-radius: 14px;
    padding: 1.6rem 1.9rem 1.4rem 1.9rem;
    margin: 0.4rem 0 0.8rem 0;
}
.answer-card .voice {
    font-size: 0.72rem; letter-spacing: 0.3em; text-transform: uppercase;
    color: #c98500; margin-bottom: 0.7rem;
}
.answer-card .body {
    font-family: 'Cormorant Garamond', Georgia, serif;
    font-size: 1.28rem; line-height: 1.65; color: #f4f1e8;
    max-width: 62rem;
}
.answer-card .body p { margin: 0 0 0.8rem 0; }
.answer-card .cite { color: #c98500; font-style: normal; }
.answer-meta {
    color: #898781; font-size: 0.82rem; letter-spacing: 0.04em;
    margin-bottom: 1.2rem;
}
.baseline-card {
    background: #171614;
    border: 1px dashed rgba(244,241,232,0.14);
    border-radius: 14px;
    padding: 1.3rem 1.9rem;
    margin: 0.4rem 0 0.8rem 0;
    color: #c3c2b7; line-height: 1.6;
}

/* ---- widgets ---- */
.stButton > button {
    transition: transform 0.18s ease, border-color 0.18s ease, background 0.18s ease;
    border-radius: 10px;
}
.stButton > button:hover { transform: translateY(-1px); border-color: #c98500; }
.stButton > button:active { transform: translateY(1px) scale(0.99); }
button[kind="primary"], .stButton > button[kind="primary"] {
    background: #c98500; color: #141311; font-weight: 600;
    letter-spacing: 0.06em;
}
[data-testid="stTextInput"] input {
    border-radius: 10px; font-size: 1.02rem;
}
div[data-baseweb="tab-list"] { gap: 0.4rem; }
button[data-baseweb="tab"] { letter-spacing: 0.05em; }
[data-testid="stExpander"] {
    border: 1px solid rgba(244,241,232,0.07); border-radius: 10px;
    background: #1a1a19;
}
[data-testid="stSidebar"] { border-right: 1px solid rgba(244,241,232,0.06); }
</style>
""",
    unsafe_allow_html=True,
)


# --------------------------------------------------------------------------- #
# Cached resources
# --------------------------------------------------------------------------- #
@st.cache_resource(show_spinner="Loading index and embedding model…")
def get_pipeline() -> RAGPipeline:
    return RAGPipeline().build()


@st.cache_resource(show_spinner="Projecting embeddings…")
def get_chunk_map(_pipeline: RAGPipeline):
    return compute_chunk_map(_pipeline)


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
    st.markdown('<div class="section-label">Configuration</div>', unsafe_allow_html=True)

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
        st.warning("No key set → **extractive mode** (top passages only).")

    st.divider()
    st.subheader("Retrieval")
    top_k = st.slider("Chunks to retrieve (k)", 1, 8, 4)
    min_score = st.slider("Min similarity score", 0.0, 1.0, 0.0, 0.05)
    show_sources = st.checkbox("Show source passages", value=True)
    compare_mode = st.checkbox("Compare: with vs. without RAG", value=False)

    st.divider()
    st.caption("Source: a generated 14-section PDF on the Roman Empire.")


# --------------------------------------------------------------------------- #
# State + ask logic
# --------------------------------------------------------------------------- #
pipeline = get_pipeline()

ss = st.session_state
ss.setdefault("last", None)        # last Answer (rendered across reruns)
ss.setdefault("last_base", None)   # last no-RAG baseline (compare mode)
ss.setdefault("graph_asked", "")   # guard so a node click fires only once
ss.setdefault("emperor67", False)  # easter egg: unlocked via "67" on the timeline

# A question queued by a graph-node click on the previous run. It must be
# consumed BEFORE the text_input widget is instantiated, so the input shows it.
pending_q = ss.pop("pending_q", None)
if pending_q:
    ss.q_input = pending_q


def do_ask(question: str, persona: str) -> None:
    """Run the pipeline once and persist the result across reruns."""
    ss.last_base = None
    if compare_mode and llm_provider():
        with st.spinner("Asking the model with no context…"):
            ss.last_base = pipeline.answer_without_rag(question)
    with st.spinner("Consulting the archives…"):
        ss.last = pipeline.answer(
            question, k=top_k, min_score=min_score, persona=persona
        )


# --------------------------------------------------------------------------- #
# Hero
# --------------------------------------------------------------------------- #
st.markdown(
    """
<div class="hero-kicker">· S · P · Q · R ·</div>
<div class="hero-title">The Roman Empire,<br>answered from the source</div>
<div class="hero-sub">A retrieval-augmented pipeline over an 11-page historical
document: FAISS finds the passages, the LLM writes the answer, every claim
carries its citation. No context, no claim.</div>
<hr class="gold-rule">
""",
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------- #
# Persona + question
# --------------------------------------------------------------------------- #
persona_specs = RAGPipeline.PERSONAS
persona_titles = {k: f'{v["emoji"]} {v["title"]}' for k, v in persona_specs.items()}

# The hidden persona stays out of the pills until the timeline's "67" is clicked.
persona_options = [
    k for k in persona_specs if k != "emperor67" or ss.emperor67
]

st.markdown('<div class="section-label">Voice · Ask the Emperor</div>',
            unsafe_allow_html=True)
persona = st.pills(
    "Voice",
    options=persona_options,
    format_func=lambda k: persona_titles[k],
    default="historian",
    label_visibility="collapsed",
)
persona = persona or "historian"
if not provider:
    st.caption("Personas need an LLM key — in extractive mode the voice is ignored.")

example = st.pills(
    "Try an example",
    options=EXAMPLE_QUESTIONS,
    selection_mode="single",
    default=None,
    key="example_pills",
    label_visibility="visible",
)
if example and example != ss.get("_example_done"):
    # Pills render before the text input, so writing its state here is legal.
    ss._example_done = example
    ss.q_input = example
    do_ask(example, persona)

col_q, col_btn = st.columns([5, 1])
with col_q:
    question = st.text_input(
        "Your question",
        key="q_input",
        placeholder="e.g. What was the Crisis of the Third Century?",
        label_visibility="collapsed",
    )
with col_btn:
    ask = st.button("Ask", type="primary", width="stretch")

if ask:
    if question.strip():
        do_ask(question.strip(), persona)
    else:
        st.warning("Please type a question first.")
elif pending_q:
    # A graph-node click queued this question on the previous run.
    do_ask(pending_q, persona)


# --------------------------------------------------------------------------- #
# Answer rendering
# --------------------------------------------------------------------------- #
def answer_html(ans, persona_key: str) -> str:
    voice = persona_specs.get(persona_key, persona_specs["historian"])
    body = html.escape(ans.answer)
    import re as _re
    # Minimal markdown the LLM tends to emit: **bold** and bullet lines.
    body = _re.sub(r"\*\*([^*\n]+)\*\*", r"<strong>\1</strong>", body)
    body = _re.sub(r"(?m)^\s*[*-]\s+", "• ", body)
    # Paint citations like [4. The Roman Military] in the accent color.
    body = _re.sub(r"\[([^\[\]]{2,60})\]", r'<span class="cite">[\1]</span>', body)
    paragraphs = "".join(f"<p>{p}</p>" for p in body.split("\n") if p.strip())
    label = f'{voice["emoji"]} {html.escape(voice["title"])}' \
        if persona_key != "historian" else "📖 Answer · grounded in the document"
    return (
        f'<div class="answer-card"><div class="voice">{label}</div>'
        f'<div class="body">{paragraphs}</div></div>'
    )


def render_sources(contexts) -> None:
    st.markdown('<div class="section-label">Retrieved sources</div>',
                unsafe_allow_html=True)
    for i, r in enumerate(contexts, 1):
        with st.expander(f"{i} · [{r.chunk.section}] · similarity {r.score:.3f}"):
            st.write(r.chunk.text)


if ss.last is not None:
    ans = ss.last
    used_persona = persona if ans.mode == "rag" else "historian"

    if ans.mode == "extractive" and pipeline.last_llm_error and llm_provider():
        st.warning(f"LLM call failed — showing raw passages instead. "
                   f"Reason: {pipeline.last_llm_error}")

    if ss.last_base is not None:
        st.markdown("### Without RAG — the model answers from memory")
        st.markdown(
            f'<div class="baseline-card">{html.escape(ss.last_base.answer)}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="answer-meta">model {ss.last_base.model} · '
            f'{ss.last_base.latency_s:.2f}s</div>',
            unsafe_allow_html=True,
        )
        st.markdown("### With RAG — grounded in the document")

    st.markdown(answer_html(ans, used_persona), unsafe_allow_html=True)
    st.markdown(
        f'<div class="answer-meta">mode {ans.mode} · model {ans.model} · '
        f'{len(ans.contexts)} chunks · {ans.latency_s:.2f}s</div>',
        unsafe_allow_html=True,
    )
    if show_sources and ans.contexts:
        render_sources(ans.contexts)


# --------------------------------------------------------------------------- #
# Visual layer — knowledge graph · timeline · embedding map
# --------------------------------------------------------------------------- #
st.markdown('<hr class="gold-rule">', unsafe_allow_html=True)
graph = load_graph()

tab_graph, tab_time, tab_map = st.tabs(
    ["🕸 Knowledge graph", "📜 Timeline", "✦ Embedding map"]
)

with tab_graph:
    if graph is None:
        st.info(
            "The knowledge graph has not been built yet. Set an API key and run "
            "`python src/build_graph.py` once — the result is cached."
        )
    else:
        st.caption(
            f"{len(graph['entities'])} entities and {len(graph['relations'])} "
            "relations extracted from the document by the LLM. "
            "**Click a node to ask about it.** Hover an edge midpoint for the relation."
        )
        event = st.plotly_chart(
            knowledge_graph_figure(graph),
            width="stretch",
            on_select="rerun",
            selection_mode="points",
            key="kg_chart",
        )
        points = event.selection.get("points", []) if event else []
        clicked = next(
            (p.get("customdata") for p in points if p.get("customdata")), None
        )
        if clicked and clicked != ss.graph_asked:
            ss.graph_asked = clicked
            # Queue the question; the next run consumes it before the input
            # widget exists, so the input box updates too.
            ss.pending_q = f"What does the document say about {clicked}?"
            st.rerun()

with tab_time:
    if graph is None or not graph.get("events"):
        st.info("Timeline events are extracted together with the knowledge graph — "
                "run `python src/build_graph.py` once.")
    else:
        highlight = years_in_text(ss.last.answer) if ss.last else set()
        n_hit = sum(
            1 for e in graph["events"]
            if (-e["year"] if e["era"] == "BCE" else e["year"]) in highlight
        )
        if ss.last and n_hit:
            st.caption(
                f"**{n_hit} event(s) mentioned in the answer glow gold.** "
                "Hover the quiet markers for the rest."
            )
        else:
            st.caption(
                "Every dated event the LLM found in the document. Ask a question "
                "above — events cited in the answer will light up in gold."
            )
        tl_event = st.plotly_chart(
            timeline_figure(graph["events"], highlight, secret_unlocked=ss.emperor67),
            width="stretch",
            on_select="rerun",
            selection_mode="points",
            key="tl_chart",
        )
        tl_points = tl_event.selection.get("points", []) if tl_event else []
        if any("67" in str(p.get("customdata")) for p in tl_points) and not ss.emperor67:
            ss.emperor67 = True
            st.balloons()
            st.toast("🗿 6 7!! Emperor Six-Seven unlocked — check the Voice pills.",
                     icon="🗿")
            st.rerun()

with tab_map:
    st.caption(
        "Each dot is one chunk of the document, projected from 384-dimensional "
        "embedding space to 2-D (PCA). Chunks from the same part of the document "
        "cluster together — and your question lands nearest the chunks it retrieves."
    )
    pca, coords = get_chunk_map(pipeline)
    q = ss.last.question if ss.last else None
    retrieved = (
        {r.chunk.chunk_id for r in ss.last.contexts} if ss.last else set()
    )
    st.plotly_chart(
        chunk_map_figure(pipeline, pca, coords, query=q, retrieved_ids=retrieved),
        width="stretch",
        key="map_chart",
    )
