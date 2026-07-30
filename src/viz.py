"""
viz.py
======
Plotly figures for the Streamlit UI:

* knowledge_graph_figure — force-directed entity/relation graph (mini-GraphRAG)
* timeline_figure        — dated events on one axis, with answer highlighting
* chunk_map_figure       — 2-D PCA projection of chunk embeddings + the query

All three share one dark, warm chart surface and a validated categorical
palette so the app reads as a single system.
"""

from __future__ import annotations

import re

import networkx as nx
import numpy as np
import plotly.graph_objects as go

# --------------------------------------------------------------------------- #
# Shared chart chrome (dark mode; matches .streamlit/config.toml)
# --------------------------------------------------------------------------- #
SURFACE = "#1a1a19"          # chart surface
INK = "#f4f1e8"              # primary ink (warm white)
INK_SECONDARY = "#c3c2b7"
INK_MUTED = "#898781"
GRID = "#2c2c2a"
ACCENT = "#c98500"           # antique gold — the single accent

FONT = dict(family='system-ui, "Segoe UI", sans-serif', color=INK_SECONDARY, size=13)

# Categorical slots (dark-surface steps of the validated palette).
TYPE_COLORS = {
    "person": "#3987e5",       # blue
    "battle": "#e66767",       # red
    "place": "#199e70",        # aqua
    "institution": "#9085e9",  # violet
    "concept": "#c98500",      # yellow/gold
}
TYPE_LABELS = {
    "person": "People",
    "battle": "Battles & wars",
    "place": "Places",
    "institution": "Institutions",
    "concept": "Concepts",
}

# Sequential blue ramp (ordinal-legal steps on a dark surface).
BLUE_RAMP = ["#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7",
             "#3987e5", "#2a78d6", "#256abf", "#1c5cab", "#184f95"]


def _base_layout(**overrides) -> dict:
    layout = dict(
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        font=FONT,
        margin=dict(l=24, r=24, t=32, b=24),
        hoverlabel=dict(
            bgcolor="#232320", bordercolor=GRID,
            font=dict(family=FONT["family"], color=INK, size=13),
        ),
    )
    layout.update(overrides)
    return layout


# --------------------------------------------------------------------------- #
# 1) Knowledge graph
# --------------------------------------------------------------------------- #
def knowledge_graph_figure(graph: dict, height: int = 620) -> go.Figure:
    """Force-directed graph of entities and relations. Node click -> question."""
    G = nx.Graph()
    for ent in graph["entities"]:
        G.add_node(ent["label"], type=ent["type"])
    for rel in graph["relations"]:
        if rel["source"] in G and rel["target"] in G:
            G.add_edge(rel["source"], rel["target"], label=rel["relation"])

    # Drop isolated nodes — they clutter the picture without telling a story.
    G.remove_nodes_from(list(nx.isolates(G)))

    pos = nx.spring_layout(G, k=0.85, iterations=120, seed=42)
    degrees = dict(G.degree())
    max_deg = max(degrees.values()) if degrees else 1

    fig = go.Figure()

    # Edges: one line trace + invisible midpoints that carry the relation label.
    edge_x, edge_y, mid_x, mid_y, mid_text = [], [], [], [], []
    for u, v, data in G.edges(data=True):
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]
        mid_x.append((x0 + x1) / 2)
        mid_y.append((y0 + y1) / 2)
        mid_text.append(f"{u} — <i>{data.get('label', 'related to')}</i> — {v}")

    fig.add_trace(go.Scatter(
        x=edge_x, y=edge_y, mode="lines",
        line=dict(width=1, color=GRID),
        hoverinfo="skip", showlegend=False,
    ))
    fig.add_trace(go.Scatter(
        x=mid_x, y=mid_y, mode="markers",
        marker=dict(size=9, color="rgba(0,0,0,0)"),
        hovertext=mid_text, hoverinfo="text", showlegend=False,
    ))

    # Nodes: one trace per entity type so the legend doubles as a type key.
    label_cutoff = sorted(degrees.values(), reverse=True)[:14][-1] if degrees else 0
    for etype, color in TYPE_COLORS.items():
        nodes = [n for n, d in G.nodes(data=True) if d["type"] == etype]
        if not nodes:
            continue
        fig.add_trace(go.Scatter(
            x=[pos[n][0] for n in nodes],
            y=[pos[n][1] for n in nodes],
            mode="markers+text",
            name=TYPE_LABELS[etype],
            marker=dict(
                size=[10 + 16 * degrees[n] / max_deg for n in nodes],
                color=color,
                line=dict(width=1, color=SURFACE),
            ),
            # Selective direct labels: only well-connected nodes get text.
            text=[n if degrees[n] >= label_cutoff else "" for n in nodes],
            textposition="top center",
            textfont=dict(size=11, color=INK_SECONDARY),
            customdata=nodes,
            hovertext=[
                f"<b>{n}</b><br>{TYPE_LABELS[etype]} · {degrees[n]} connection(s)"
                f"<br><i>click to ask about it</i>"
                for n in nodes
            ],
            hoverinfo="text",
        ))

    fig.update_layout(**_base_layout(
        height=height,
        showlegend=True,
        legend=dict(
            orientation="h", yanchor="bottom", y=1.0, x=0,
            bgcolor="rgba(0,0,0,0)", font=dict(size=12),
        ),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        dragmode="pan",
    ))
    return fig


# --------------------------------------------------------------------------- #
# 2) Timeline
# --------------------------------------------------------------------------- #
_YEAR_RE = re.compile(r"\b(\d{1,4})\s*(BCE|BC|CE|AD)\b")


def years_in_text(text: str) -> set[int]:
    """Signed years mentioned in a text (BCE negative). Used for highlighting."""
    years: set[int] = set()
    for num, era in _YEAR_RE.findall(text or ""):
        y = int(num)
        years.add(-y if era in ("BCE", "BC") else y)
    return years


def _signed(evt: dict) -> int:
    return -evt["year"] if evt["era"] == "BCE" else evt["year"]


def _fmt_year(y: int) -> str:
    return f"{-y} BCE" if y < 0 else f"{y} CE"


def timeline_figure(
    events: list[dict],
    highlight_years: set[int] | None = None,
    height: int = 420,
    secret_unlocked: bool = False,
) -> go.Figure:
    """Dated events on a single axis; events mentioned in the answer glow gold.

    Somewhere on the axis, six meets seven. Clicking it (the app listens via
    on_select) unlocks a hidden persona; `secret_unlocked` restyles the mark.
    """
    highlight_years = highlight_years or set()
    events = sorted(events, key=_signed)

    xs = [_signed(e) for e in events]
    # Stagger stem heights so labels in dense stretches don't collide.
    levels = [1.0, 1.8, 1.4, 2.2]
    ys = [levels[i % len(levels)] for i in range(len(events))]
    hits = [_signed(e) in highlight_years for e in events]

    fig = go.Figure()

    # Era bands: Republic / Empire (West).
    fig.add_vrect(x0=-509, x1=-27, fillcolor="#232320", line_width=0, layer="below")
    fig.add_vrect(x0=-27, x1=476, fillcolor="#1f1e1b", line_width=0, layer="below")
    fig.add_annotation(x=-268, y=2.75, text="REPUBLIC", showarrow=False,
                       font=dict(size=11, color=INK_MUTED), opacity=0.9)
    fig.add_annotation(x=224, y=2.75, text="EMPIRE", showarrow=False,
                       font=dict(size=11, color=INK_MUTED), opacity=0.9)

    # Stems.
    for x, y, hit in zip(xs, ys, hits):
        fig.add_shape(
            type="line", x0=x, x1=x, y0=0, y1=y,
            line=dict(color=ACCENT if hit else GRID, width=2 if hit else 1),
        )

    # Base events (quiet) and highlighted events (gold, labeled).
    quiet = [i for i, h in enumerate(hits) if not h]
    loud = [i for i, h in enumerate(hits) if h]

    fig.add_trace(go.Scatter(
        x=[xs[i] for i in quiet], y=[ys[i] for i in quiet],
        mode="markers",
        marker=dict(size=9, color="#5598e7", line=dict(width=1, color=SURFACE)),
        hovertext=[f"<b>{_fmt_year(xs[i])}</b> — {events[i]['label']}" for i in quiet],
        hoverinfo="text", showlegend=False,
    ))
    if loud:
        fig.add_trace(go.Scatter(
            x=[xs[i] for i in loud], y=[ys[i] for i in loud],
            mode="markers+text",
            marker=dict(size=13, color=ACCENT, line=dict(width=2, color=INK)),
            text=[events[i]["label"] for i in loud],
            textposition="top center",
            textfont=dict(size=11, color=INK),
            hovertext=[f"<b>{_fmt_year(xs[i])}</b> — {events[i]['label']}" for i in loud],
            hoverinfo="text", showlegend=False,
        ))

    # The "67" easter egg: a quiet mark at 67 CE. Gold once unlocked.
    secret_color = ACCENT if secret_unlocked else INK_MUTED
    fig.add_trace(go.Scatter(
        x=[67], y=[0.45],
        mode="markers+text",
        marker=dict(
            size=13 if secret_unlocked else 8,
            symbol="hexagon",
            color=secret_color,
            line=dict(width=1, color=INK if secret_unlocked else SURFACE),
        ),
        text=["6·7 🗿" if secret_unlocked else "67"],
        textposition="bottom center",
        textfont=dict(size=10, color=secret_color),
        customdata=["67"],
        hovertext=[
            "🗿 <b>6 7!!</b> Emperor Six-Seven reigns. Check the Voice pills."
            if secret_unlocked else
            "67 CE — <i>six… seven…</i> something stirs. Click it."
        ],
        hoverinfo="text", showlegend=False,
    ))

    tick_vals = [-750, -500, -250, -1, 250, 500]
    fig.update_layout(**_base_layout(
        height=height,
        xaxis=dict(
            tickvals=tick_vals,
            ticktext=[_fmt_year(t if t != -1 else -1).replace("1 BCE", "1 BCE")
                      for t in tick_vals],
            zeroline=False, showgrid=False,
            linecolor=GRID, tickfont=dict(color=INK_MUTED),
        ),
        yaxis=dict(visible=False, range=[-0.2, 3.1]),
        showlegend=False,
    ))
    # Baseline.
    fig.add_shape(type="line", x0=-790, x1=560, y0=0, y1=0,
                  line=dict(color=INK_MUTED, width=1))
    return fig


# --------------------------------------------------------------------------- #
# 3) Chunk map (PCA of embeddings)
# --------------------------------------------------------------------------- #
def compute_chunk_map(pipeline):
    """Fit a 2-D PCA on the chunk embeddings stored in the FAISS index."""
    from sklearn.decomposition import PCA

    n = pipeline.index.ntotal
    vecs = pipeline.index.reconstruct_n(0, n)
    pca = PCA(n_components=2, random_state=42)
    coords = pca.fit_transform(vecs)
    return pca, coords


def chunk_map_figure(
    pipeline,
    pca,
    coords: np.ndarray,
    query: str | None = None,
    retrieved_ids: set[int] | None = None,
    height: int = 560,
) -> go.Figure:
    """Chunks in 2-D embedding space; the query lands among what it retrieves."""
    retrieved_ids = retrieved_ids or set()
    chunks = pipeline.chunks

    sections = sorted({c.section for c in chunks},
                      key=lambda s: int(s.split(".")[0]) if s.split(".")[0].isdigit() else 99)
    sec_idx = {s: i for i, s in enumerate(sections)}
    ramp_pos = [int(round(i * (len(BLUE_RAMP) - 1) / max(len(sections) - 1, 1)))
                for i in range(len(sections))]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=coords[:, 0], y=coords[:, 1],
        mode="markers",
        marker=dict(
            size=[15 if c.chunk_id in retrieved_ids else 10 for c in chunks],
            color=[BLUE_RAMP[ramp_pos[sec_idx[c.section]]] for c in chunks],
            line=dict(
                width=[2.5 if c.chunk_id in retrieved_ids else 1 for c in chunks],
                color=[ACCENT if c.chunk_id in retrieved_ids else SURFACE
                       for c in chunks],
            ),
        ),
        hovertext=[
            f"<b>chunk {c.chunk_id}</b> · {c.section}"
            f"{' · <b>retrieved</b>' if c.chunk_id in retrieved_ids else ''}"
            f"<br>{c.text[:140]}…"
            for c in chunks
        ],
        hoverinfo="text",
        showlegend=False,
    ))

    if query:
        qxy = pca.transform(pipeline._embed([query]))[0]
        fig.add_trace(go.Scatter(
            x=[qxy[0]], y=[qxy[1]],
            mode="markers+text",
            marker=dict(size=17, symbol="star", color=ACCENT,
                        line=dict(width=1, color=INK)),
            text=["your question"], textposition="bottom center",
            textfont=dict(size=11, color=ACCENT),
            hovertext=[f"<b>Query:</b> {query}"], hoverinfo="text",
            showlegend=False,
        ))

    fig.update_layout(**_base_layout(
        height=height,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        annotations=[dict(
            text="hue = position in the document (light → dark = section 1 → "
                 f"{len(sections)}) · gold ring = retrieved for the last question",
            xref="paper", yref="paper", x=0, y=-0.04,
            showarrow=False, font=dict(size=11, color=INK_MUTED), align="left",
        )],
    ))
    return fig
