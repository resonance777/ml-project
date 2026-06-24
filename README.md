# RAG & LLM for Ancient Empire History — The Roman Empire

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
- **Graceful fallback** — runs in *extractive* mode (returns top passages)
  when no API key is set, so it is always runnable.
- **CLI + evaluation harness** with retrieval-accuracy and latency metrics.

## Project layout

```
ml-project/
├── src/
│   ├── content.py        # structured Roman Empire historical content
│   ├── generate_pdf.py   # builds data/roman_empire.pdf
│   ├── rag_pipeline.py   # extract → chunk → embed → FAISS → retrieve → LLM
│   ├── query_cli.py      # interactive / one-shot query interface
│   ├── app.py            # Streamlit web UI (click-to-ask)
│   └── evaluate.py       # runs example queries + metrics → docs/results.md
├── data/
│   ├── roman_empire.pdf  # generated source document (11 pages)
│   ├── faiss.index       # cached vector index
│   └── chunks.json       # cached chunk metadata
├── docs/
│   ├── DOCUMENTATION.md   # step-by-step write-up (What/Why/How/Result)
│   └── results.md         # auto-generated evaluation report
├── requirements.txt
├── .env.example
└── README.md
```

## Setup

> On this machine the Python launcher is at
> `C:\Users\kkhee\AppData\Local\Python\pythoncore-3.14-64\python.exe`.
> Substitute `python` below with that full path if the bare `python` command
> does not work.

```bash
pip install -r requirements.txt

# Optional: enable LLM answers (Gemini by default)
cp .env.example .env          # then paste your GEMINI_API_KEY
```

Get a free Gemini key at <https://aistudio.google.com/apikey>.

## Usage

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
- **Python 3.14**: the bare `python` command on this machine is a stub; use the
  full interpreter path shown above.
