# Project 3 — RAG & LLM for Ancient Empire History
## The Roman Empire: Step-by-Step Implementation Documentation

**Chosen civilisation:** Roman Empire
**Stack:** Python 3.14 · ReportLab · pypdf · sentence-transformers (all-MiniLM-L6-v2) · FAISS · Anthropic Claude
**Repository:** `src/` (code) · `data/` (PDF + index) · `docs/` (this write-up + auto-generated `results.md`)

---

### Architecture overview

```
content.py ──► generate_pdf.py ──►  roman_empire.pdf (11 pages)
                                          │
                                   pypdf extract + clean
                                          │
                              section-aware overlapping chunking  (28 chunks)
                                          │
                      all-MiniLM-L6-v2 embeddings (384-d, normalised)
                                          │
                              FAISS IndexFlatIP (exact cosine)
                                          │
   user query ──► embed ──► top-k search ──► context injection ──► Claude ──► cited answer
```

---

## Step 1 — Content Generation and PDF Creation

**What.** I compiled an original ~6,000-word historical reference on the Roman
Empire, organised into 14 numbered sections covering the five required aspects:
politics (Republic, Principate, administration, law), military, economy/trade,
culture/engineering, and society/religion/family. It is rendered to an 11-page
PDF (`data/roman_empire.pdf`).

**Why.** RAG quality is bounded by source quality. I wanted (a) factually solid,
self-contained prose and (b) *clear structure*, because the numbered headings
later double as natural chunk boundaries and as human-readable citation labels.
Content is stored as structured Python data (`content.py`) rather than a raw
string so the generator can apply consistent heading/body styling.

**How.** ReportLab's high-level *Platypus* flowables handle pagination and
wrapping automatically:

```python
doc = SimpleDocTemplate(output_path, pagesize=A4, title=TITLE, author=AUTHOR)
story = [Paragraph(TITLE, styles["DocTitle"]), PageBreak()]
for title, paragraphs in SECTIONS:
    story.append(Paragraph(title, styles["SectionHeading"]))   # heading style
    for para in paragraphs:
        story.append(Paragraph(para, styles["BodyJustified"]))  # justified body
doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
```

**Result.** A reproducible 11-page PDF (title page + 10 content pages, ~21 KB)
with page-number footers and a distinct heading style — comfortably above the
10-page minimum and structured for clean downstream parsing.

---

## Step 2 — Text Preprocessing Strategy

**What.** I extract text from every PDF page with `pypdf`, then normalise it:
repair hyphen-split words, strip the `Page N` footers, and collapse redundant
whitespace while keeping newlines.

**Why.** Raw PDF extraction introduces artefacts — mid-word hyphenation across
line breaks, footer text, and irregular spacing — that pollute embeddings and
waste context tokens. Newlines are deliberately *preserved* so that the section
heading detector in Step 3 can still see one heading per line.

**How.**

```python
text = re.sub(r"-\n(\w)", r"\1", text)               # de-hyphenate "engi-\nneering"
text = re.sub(r"(?im)^\s*Page\s+\d+\s*$", "", text)  # drop page footers
text = re.sub(r"[ \t]+", " ", text)                  # collapse spaces, keep \n
text = re.sub(r"\n{3,}", "\n\n", text)
```

**Result.** Clean, normalised text from which section headings can be reliably
recovered. The title-page metadata (before the first numbered heading) is later
discarded so only genuine historical content is indexed.

---

## Step 3 — Chunking Implementation

**What.** A two-level chunker: first split the document into sections on the
numbered headings, then split each section into **overlapping, sentence-aligned
word windows** (~220 target words, 350 hard max, **80-word overlap**).

**Why.**
- *Section-aware* splitting keeps each chunk topically coherent and lets me tag
  every chunk with its section title for citations.
- *Sentence alignment* avoids cutting mid-sentence, which would damage meaning.
- *Overlap* preserves context across boundaries, so a fact mentioned at the end
  of one chunk and explained in the next is still retrievable.
- The spec suggested 300–800 words; I tuned slightly smaller (≈220) because the
  source paragraphs are dense and smaller chunks gave sharper similarity scores
  and more precise citations.

**How.** Whole sentences accumulate until the target size, then the chunk is
flushed and the next one is seeded with the previous chunk's overlap tail:

```python
def flush(carry_overlap):
    chunk = Chunk(cid, section_title, " ".join(current))
    if carry_overlap:
        tail = chunk.text.split()[-OVERLAP_WORDS:]   # 80-word carry-over
        current[:] = [" ".join(tail)]
    ...
for sent in sentences:
    if current_words + len(sent.split()) > MAX_CHUNK_WORDS:
        flush(carry_overlap=True)
    current.append(sent); current_words += len(sent.split())
    if current_words >= TARGET_CHUNK_WORDS:
        flush(carry_overlap=True)
```

**Result.** 28 overlapping chunks, each carrying a `section` label. Section
boundaries are respected, and the 80-word overlap measurably preserves context
across chunk edges.

---

## Step 4 — Vector Embedding Process

**What.** Each chunk is encoded with
`sentence-transformers/all-MiniLM-L6-v2` into a **384-dimensional**,
L2-normalised vector.

**Why.** MiniLM-L6-v2 is the assignment's recommended model and an excellent
default: it is small (~80 MB), fast on CPU, and produces strong semantic
embeddings. L2-normalising the vectors means an inner-product search is exactly
cosine similarity — simpler and faster than computing cosine explicitly.

**How.**

```python
vecs = model.encode(texts, convert_to_numpy=True,
                    normalize_embeddings=True).astype("float32")
```

**Result.** A `(28, 384)` float32 matrix of unit vectors. Embedding all chunks
takes well under a second on CPU after the one-time model download; the model is
lazy-loaded so retrieval-only runs stay light.

---

## Step 5 — Vector Database Setup

**What.** Vectors are stored in a **FAISS `IndexFlatIP`** index. The index and
chunk metadata are cached to disk (`data/faiss.index`, `data/chunks.json`).

**Why.** FAISS is fast, dependency-light, fully local (no API keys or network),
and ideal for this corpus size. With only 28 vectors, an **exact** flat index
gives perfect recall with negligible latency — approximate indexes (IVF/HNSW)
would add complexity for no benefit at this scale. `IndexFlatIP` + normalised
vectors = exact cosine ranking.

**How.**

```python
index = faiss.IndexFlatIP(384)   # inner product == cosine on unit vectors
index.add(embeddings)
```

> **Windows/Cyrillic-path issue & fix:** the project lives under a Cyrillic
> `Документы` folder, and `faiss.write_index()`'s C++ file writer cannot open
> non-ASCII paths. I serialise the index to bytes and write it with Python I/O
> instead, which handles Unicode paths correctly:
> ```python
> open(INDEX_PATH, "wb").write(faiss.serialize_index(index).tobytes())
> ```

**Result.** A persisted, reloadable index. Building runs once; subsequent
queries reload from cache in milliseconds.

---

## Step 6 — Retrieval Mechanism

**What.** A query is embedded with the same model, then FAISS returns the
**top-k (default k=4)** most similar chunks with cosine scores; an optional
`min_score` filter drops weak matches.

**Why.** k=4 (within the recommended 3–5) gives the LLM enough supporting
evidence to synthesise and cross-check an answer without diluting the prompt
with irrelevant text. Using the *same* embedding model for queries and chunks is
essential so both live in the same vector space.

**How.**

```python
qvec = self._embed([query])
scores, idxs = self.index.search(qvec, k)
return [RetrievedChunk(self.chunks[i], float(s))
        for s, i in zip(scores[0], idxs[0]) if i != -1 and s >= min_score]
```

**Result.** Relevant, scored passages. Example — *"How was the Roman army
organised?"* → top hit **[4. The Roman Military]** at cosine **0.616**.

---

## Step 7 — LLM Integration and Prompt Engineering

**What.** Retrieved chunks are formatted into a context block and injected into
a prompt sent to an **LLM**. The provider is auto-detected from the available
API key — **Google Gemini** (`gemini-2.5-flash`, default) or **Anthropic
Claude** (`claude-haiku-4-5`) — behind one `_call_llm()` interface. The system
prompt constrains the model to answer *only* from the context and to cite the
section titles it used.

**Why.** Grounding the model in retrieved text is the whole point of RAG: it
suppresses hallucination and yields verifiable, cited answers. Explicit
"answer only from context / say so if absent" instructions plus per-passage
`[Source: section]` tags make citations natural and make unanswerable questions
fail safely instead of inventing facts.

**How.**

```python
context = "\n\n---\n\n".join(f"[Source: {r.chunk.section}]\n{r.chunk.text}"
                            for r in contexts)
prompt = ("Answer using ONLY the context passages below. Cite the section "
          "titles in square brackets, e.g. [4. The Roman Military]. If the "
          f"answer is not in the context, say so.\n\nCONTEXT\n{context}\n\n"
          f"QUESTION\n{query}")
msg = client.messages.create(model=LLM_MODEL, max_tokens=600,
        system="Answer strictly from context and cite the sections used.",
        messages=[{"role": "user", "content": prompt}])
```

**Why a fallback.** If `ANTHROPIC_API_KEY` is unset (or a call fails), the
pipeline returns the top retrieved passages verbatim with scores ("extractive
mode"). This keeps the deliverable **always runnable** for grading, and cleanly
separates *retrieval* quality from *generation* quality.

**Result.** With a key, Claude produces concise, cited answers grounded in the
PDF. Without one, the system still returns the correct source passages.

---

## Step 8 — End-to-End Pipeline Testing

**What.** `evaluate.py` runs a suite of 10 diverse questions, checking whether
the expected source section appears in the top-k, recording the top-1 cosine
score and latency, and writing a Markdown report to `docs/results.md`.
`query_cli.py` provides interactive and one-shot interfaces.

**Why.** Automated evaluation turns "looks good" into measurable
**retrieval accuracy** and **latency**, and makes regressions visible after any
change to chunking or embeddings (e.g. it confirmed that removing the title-page
preamble improved result purity).

**How.**

```python
retrieved = rag.retrieve(q, k=4)
hit = any(expected.lower() in r.chunk.section.lower() for r in retrieved)
```

**Result.** See the Results section below. Headline: **10/10 (100%)** retrieval
accuracy and sub-second local retrieval.

---

# Results Section

> Numbers below are reproducible via `python src/evaluate.py`
> (full report: `docs/results.md`). Retrieval metrics are independent of the
> LLM; answer quality additionally requires an API key.

### Query examples (10 diverse questions)

1. When and how was Rome founded according to tradition?
2. How was the Roman legion organised and equipped?
3. What goods did Rome trade and with whom?
4. What was the role of slaves in Roman society?
5. How did Christianity become the official religion of Rome?
6. What engineering innovations are the Romans known for?
7. Why did the Western Roman Empire fall in 476 CE?
8. Who were the Five Good Emperors?
9. What rights did Roman women have?
10. What was the Crisis of the Third Century?

### Retrieval accuracy

| Metric | Value |
|---|---|
| Expected section in top-4 | **10 / 10 (100%)** |
| Average top-1 cosine relevance | **0.615** |
| Range of top-1 scores | ~0.55 – 0.73 |

Every question retrieved its correct source section within the top 4 chunks.
Strongly worded factual questions score highest (e.g. *"Why did the Western
Roman Empire fall?"* → 0.726); broader questions whose answer spans several
sections score lower but still rank the right section first.

### Performance metrics

| Metric | Value |
|---|---|
| Index build (28 chunks, incl. embedding) | < 1 s (after model load) |
| Per-query retrieval (cached index) | ~5–15 ms |
| Extractive answer latency | ~0.01 s |
| LLM answer latency (Claude, when enabled) | ~1–3 s (network-bound) |

The first call pays a one-time embedding-model load (~3 s); all subsequent
retrievals are millisecond-scale because the FAISS index is cached.

### Response quality: before vs. after RAG

| | Baseline LLM (no context) | RAG (with retrieved context) |
|---|---|---|
| Grounding | answers from parametric memory | answers from the supplied PDF |
| Verifiability | none | cites `[section]` for each claim |
| Unknown queries | may hallucinate | instructed to say "not in document" |
| Specificity | generic | tied to the document's exact wording/dates |

`rag_pipeline.answer_without_rag()` implements the baseline so the two can be
compared directly when an API key is present.

### Retrieval accuracy of chunks (qualitative)

Inspecting `docs/results.md`, the top chunk for each query is consistently the
passage a human would pick. Section-aware chunking means citations point at a
meaningful unit ("4. The Roman Military"), and the 80-word overlap prevents
boundary facts (e.g. auxiliaries gaining citizenship after 25 years) from being
lost between chunks.

### Challenges encountered & solutions

| Challenge | Solution |
|---|---|
| **FAISS can't write to a Cyrillic Windows path** (`Документы`) | Serialise the index to bytes and persist via Python file I/O (`serialize_index` / `deserialize_index`). |
| **Python 3.14 + bare `python` is a broken stub** (prints "Python", exit 49) | Invoke the real interpreter by full path; documented in README. |
| **Title-page text polluted retrieval** (appeared as an "Introduction" chunk) | Discard all preamble before the first numbered heading during chunking; chunks dropped 29 → 28 and noise disappeared. |
| **Choosing chunk size** | Started at the upper end (800 w), but dense source text gave sharper scores at ~220 w; validated with the eval harness. |
| **Always-runnable requirement without paid API** | Graceful extractive fallback that returns top passages, so retrieval is demonstrable with zero credentials. |

### What was learned

RAG quality is dominated by the *retrieval* half: clean preprocessing,
topical chunking, and consistent embeddings produced 100% section-level
retrieval accuracy on this corpus. The LLM then mainly needs to be *constrained*
to its context and *forced* to cite — most of the engineering effort and most of
the failure modes live before the model is ever called.
