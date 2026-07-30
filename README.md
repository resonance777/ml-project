# RAG & LLM for Ancient Empire History — The Roman Empire

> **Team project** (3 people). Original repository: [shev-k/ml-project](https://github.com/shev-k/ml-project).
>
> | Who | Area |
> |---|---|
> | **Konstantin Shevtsov** ([@shev-k](https://github.com/shev-k)) and **Davyd Zakharov** | Knowledge base — source document, extraction, cleaning and chunking; prompt engineering and LLM integration; Streamlit UI, CLI and evaluation harness |
> | **Ruslan Sabitov** ([@resonance777](https://github.com/resonance777)) | Search engine — MiniLM embeddings, FAISS index, top-k similarity retrieval (core of `rag_pipeline.py`); presented the system architecture at the defence |
>
> Git history in this repository preserves each author's original commits.

A complete **Retrieval-Augmented Generation (RAG)** pipeline that answers
questions about the **Roman Empire** by retrieving passages from a generated
10+ page historical PDF and feeding them to an LLM (Anthropic Claude).

```
PDF (10+ pages)  ─►  extract & clean  ─►  chunk  ─►  embed (MiniLM)
                                                        │
   answer  ◄──  Claude (LLM)  ◄──  inject context  ◄──  FAISS top-k search
```

## Features

- **PDF generation** — 11-page Roman Empire document (politics, military,
  economy, culture, society) built with ReportLab.
- **Section-aware chunking** — 300–800 word windows with ~80-word overlap.
- **Embeddings** — `sentence-transformers/all-MiniLM-L6-v2` (384-d).
- **Vector DB** — FAISS `IndexFlatIP` (exact cosine similarity).
- **LLM answers** — Google Gemini (or Anthropic Claude) with context injection
  + citations. Provider auto-detected from whichever API key is set.
- **"Ask the Emperor" personas** — the same grounded, cited answer voiced by
  Marcus Aurelius, Cicero, or a veteran legionary. Style changes; facts don't.
- **Knowledge graph** — the LLM extracts entities and relations from the
  document once (cached in `data/graph.json`); the app renders an interactive
  force-directed graph. Clicking a node asks about it.
- **Timeline** — every dated event in the document on one axis; events cited
  in the current answer light up in gold.
- **Embedding map** — a 2-D PCA of all chunk embeddings; shows how chunks
  cluster by topic and where the current question lands.
- **Graceful fallback** — runs in *extractive* mode (returns top passages)
  when no API key is set or the LLM call fails, with the real reason shown.
- **CLI + evaluation harness** with retrieval-accuracy and latency metrics.
- **???** — somewhere on the timeline, six meets seven. 🗿

## Project layout

```
ml-project/
├── src/
│   ├── content.py        # structured Roman Empire historical content
│   ├── generate_pdf.py   # builds data/roman_empire.pdf
│   ├── rag_pipeline.py   # extract → chunk → embed → FAISS → retrieve → LLM
│   ├── build_graph.py    # LLM-extracts entities/relations/events → graph.json
│   ├── viz.py            # plotly figures: graph, timeline, embedding map
│   ├── query_cli.py      # interactive / one-shot query interface
│   ├── app.py            # Streamlit web UI (personas, graph, timeline, map)
│   └── evaluate.py       # runs example queries + metrics → docs/results.md
├── data/
│   ├── roman_empire.pdf  # generated source document (11 pages)
│   ├── faiss.index       # cached vector index
│   ├── chunks.json       # cached chunk metadata
│   └── graph.json        # cached knowledge graph + timeline events
├── docs/
│   ├── DOCUMENTATION.md   # step-by-step write-up (What/Why/How/Result)
│   └── results.md         # auto-generated evaluation report
├── requirements.txt
├── .env.example
└── README.md
```

## Setup

> If the bare `python` command ever stops working again, use the full path
> `C:\Users\kkhee\AppData\Local\Python\pythoncore-3.14-64\python.exe` instead
> (see the notes at the bottom).

```bash
pip install -r requirements.txt

# Optional: enable LLM answers (Gemini by default)
cp .env.example .env          # then paste your GEMINI_API_KEY
```

Get a free Gemini key at <https://aistudio.google.com/apikey>.

## Usage

### 🚀 One-click launchers (Windows)

- **`run_app.bat`** — double-click to open the web UI in the browser.
- **`ask.bat "your question"`** — one-shot CLI answer with sources;
  run without arguments for interactive mode.

Both use the full interpreter path, so they work even when the bare
`python` command does not.

### 🌐 Web app (easiest — recommended)

```bash
python -m streamlit run src/app.py
```

Opens a browser UI where you can paste your API key in the sidebar (no `.env`
needed), click an example question or type your own, and see the cited answer
plus the retrieved source passages. Toggle **"Compare: with vs. without RAG"**
for the before/after demo.

### 💻 Command line

```bash
# 1. Generate the source PDF (already included, but reproducible)
python src/generate_pdf.py

# 2. Build the vector index (first run downloads the embedding model ~80 MB)
python src/rag_pipeline.py --force

# 2b. (optional) Rebuild the knowledge graph / timeline (needs an API key;
#     the result is cached in data/graph.json so this only runs once)
python src/build_graph.py --force

# 3a. Ask a single question
python src/query_cli.py -q "Why did the Western Roman Empire fall?" --show-context

# 3b. Interactive mode (type 'quit' to exit; prefix 'ctx:' to show passages)
python src/query_cli.py

# 4. Run the evaluation suite (writes docs/results.md)
python src/evaluate.py
```

### Modes

| | API key set | no API key |
|---|---|---|
| **Answer** | Claude synthesises an answer with citations | top retrieved passages (extractive) |
| **Retrieval** | identical (local, FAISS) | identical |

## Notes / known environment quirks

- **Cyrillic project path**: `faiss.write_index()` cannot open non-ASCII paths
  on Windows, so the index is (de)serialised through Python file I/O instead.
- **Python 3.14**: the bare `python` command used to be shadowed by the
  Microsoft Store stub; fixed on 2026-07-09 by moving
  `C:\Users\kkhee\AppData\Local\Python\bin` before `WindowsApps` in the user
  PATH. `python` now works in any freshly opened terminal.
