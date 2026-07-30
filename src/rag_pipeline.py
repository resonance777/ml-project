"""
rag_pipeline.py
===============
End-to-end Retrieval-Augmented Generation (RAG) pipeline for question answering
over the Roman Empire source PDF.

Pipeline stages
---------------
1. Extract  -> read raw text from the PDF (pypdf).
2. Clean    -> normalise whitespace, fix hyphenation, drop page-number noise.
3. Chunk    -> split into section-aware, overlapping word windows
               (300-800 words, ~80 word overlap).
4. Embed    -> encode chunks with sentence-transformers/all-MiniLM-L6-v2 (384-d).
5. Index    -> store vectors in a FAISS inner-product index (cosine on L2-norm).
6. Retrieve -> embed the query, take top-k most similar chunks with scores.
7. Generate -> inject retrieved context into a prompt and call Claude to answer
               with citations. Falls back to an extractive answer if no API key.

The class persists the index + chunk metadata to disk so the (relatively slow)
embedding step only runs once.

Environment variables
----------------------
ANTHROPIC_API_KEY   required for LLM-generated answers (otherwise extractive mode)
RAG_LLM_MODEL       Claude model id (default: claude-haiku-4-5-20251001)
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field
from typing import Optional

import faiss
import numpy as np
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

try:
    from dotenv import load_dotenv

    # Load both .env and .env.local (the latter overrides). load_dotenv only
    # reads .env by default, so we point at .env.local explicitly.
    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    load_dotenv(os.path.join(_root, ".env"))
    load_dotenv(os.path.join(_root, ".env.local"), override=True)
except Exception:  # python-dotenv is optional
    pass

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(HERE)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

DEFAULT_PDF = os.path.join(DATA_DIR, "roman_empire.pdf")
INDEX_PATH = os.path.join(DATA_DIR, "faiss.index")
META_PATH = os.path.join(DATA_DIR, "chunks.json")

EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"  # 384-d, fast, strong

# --- LLM provider selection -------------------------------------------------
# The pipeline auto-detects which LLM to use based on available API keys:
#   GEMINI_API_KEY / GOOGLE_API_KEY -> Google Gemini   (google-genai SDK)
#   ANTHROPIC_API_KEY               -> Anthropic Claude (anthropic SDK)
#   (neither)                       -> extractive fallback (top passages)
GEMINI_MODEL = os.environ.get("RAG_GEMINI_MODEL", "gemini-2.5-flash")
ANTHROPIC_MODEL = os.environ.get("RAG_ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")


def llm_provider() -> Optional[str]:
    """Return the active LLM provider name based on which API key is set."""
    if os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"):
        return "gemini"
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic"
    return None


def _short_llm_error(e: Exception) -> str:
    """Condense an SDK exception into one human-readable line for the UI."""
    msg = str(e)
    if "RESOURCE_EXHAUSTED" in msg or "429" in msg:
        return (
            "API rate/quota limit reached (free-tier Gemini allows a limited "
            "number of requests per day per model). Wait for the quota to "
            "reset or set RAG_GEMINI_MODEL to a different model in .env.local."
        )
    if "API key not valid" in msg or "401" in msg or "PERMISSION_DENIED" in msg:
        return "the API key was rejected — check the key in .env.local / sidebar."
    if "UNAVAILABLE" in msg or "503" in msg:
        return ("the model is temporarily overloaded (503) — try again in a "
                "few seconds or switch RAG_GEMINI_MODEL in .env.local.")
    return msg[:200]


def active_model() -> str:
    """Human-readable id of the model that will actually be called."""
    provider = llm_provider()
    if provider == "gemini":
        return GEMINI_MODEL
    if provider == "anthropic":
        return ANTHROPIC_MODEL
    return "none"

# Chunking parameters (assignment spec: 300-800 words, 50-100 word overlap).
TARGET_CHUNK_WORDS = 220   # aim per chunk; sentences are added until this is hit
MAX_CHUNK_WORDS = 350      # hard ceiling so a chunk fits comfortably in context
OVERLAP_WORDS = 80         # words carried over from the previous chunk

# Heading pattern matching our PDF section titles, e.g. "1. Origins and the ...".
HEADING_RE = re.compile(r"^\s*(\d{1,2})\.\s+[A-Z].{2,80}$")


# --------------------------------------------------------------------------- #
# Data model
# --------------------------------------------------------------------------- #
@dataclass
class Chunk:
    chunk_id: int
    section: str
    text: str


@dataclass
class RetrievedChunk:
    chunk: Chunk
    score: float


@dataclass
class Answer:
    question: str
    answer: str
    contexts: list[RetrievedChunk] = field(default_factory=list)
    mode: str = "rag"            # "rag", "extractive", or "no-context"
    latency_s: float = 0.0
    model: str = ""


# --------------------------------------------------------------------------- #
# Stage 1 & 2: extraction and cleaning
# --------------------------------------------------------------------------- #
def extract_text(pdf_path: str) -> str:
    """Extract raw text from every page of the PDF and concatenate it."""
    reader = PdfReader(pdf_path)
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages)


def clean_text(raw: str) -> str:
    """
    Normalise extracted PDF text.

    * Repair words split across line breaks by hyphenation ("engi-\nneering").
    * Drop standalone "Page N" footer lines we added in the generator.
    * Collapse runs of whitespace while preserving line breaks so that the
      heading detector below can still see one heading per line.
    """
    text = raw.replace("\r", "\n")
    text = re.sub(r"-\n(\w)", r"\1", text)                # de-hyphenate
    text = re.sub(r"(?im)^\s*Page\s+\d+\s*$", "", text)   # remove page footers
    # Collapse spaces/tabs but keep newlines.
    text = re.sub(r"[ \t]+", " ", text)
    # Collapse 3+ newlines down to 2.
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# --------------------------------------------------------------------------- #
# Stage 3: section-aware, overlapping chunking
# --------------------------------------------------------------------------- #
def split_into_sections(text: str) -> list[tuple[str, str]]:
    """
    Split cleaned text into (section_title, section_body) pairs using the
    numbered headings produced by the PDF generator. Falls back to a single
    "Document" section if no headings are detected.
    """
    lines = text.split("\n")
    sections: list[tuple[str, list[str]]] = []
    current_title: Optional[str] = None
    current_body: list[str] = []

    for line in lines:
        if HEADING_RE.match(line.strip()):
            if current_title is not None and current_body:
                sections.append((current_title, current_body))
            current_title = line.strip()
            current_body = []
        else:
            # Skip any preamble (the title page) that appears before the first
            # real numbered heading — it is metadata, not historical content.
            if current_title is not None and line.strip():
                current_body.append(line.strip())

    if current_title is not None and current_body:
        sections.append((current_title, current_body))

    if not sections:
        return [("Document", text)]

    return [(title, " ".join(body)) for title, body in sections]


def _sentences(text: str) -> list[str]:
    """Lightweight sentence splitter (no extra NLP dependency)."""
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if p.strip()]


def chunk_section(section_title: str, body: str, start_id: int) -> list[Chunk]:
    """
    Turn one section's body into overlapping word-window chunks.

    We accumulate whole sentences until reaching TARGET_CHUNK_WORDS (never
    exceeding MAX_CHUNK_WORDS), then start the next chunk with an OVERLAP_WORDS
    tail of the previous one so context is preserved across boundaries.
    """
    chunks: list[Chunk] = []
    sentences = _sentences(body)
    cid = start_id

    current: list[str] = []
    current_words = 0

    def flush(carry_overlap: bool):
        nonlocal current, current_words, cid
        if not current:
            return []
        text = " ".join(current).strip()
        chunk = Chunk(chunk_id=cid, section=section_title, text=text)
        cid += 1
        # Build the overlap tail for the next chunk.
        if carry_overlap:
            words = text.split()
            tail = words[-OVERLAP_WORDS:] if len(words) > OVERLAP_WORDS else words
            current = [" ".join(tail)]
            current_words = len(tail)
        else:
            current = []
            current_words = 0
        return [chunk]

    for sent in sentences:
        sw = len(sent.split())
        if current_words + sw > MAX_CHUNK_WORDS and current_words > 0:
            chunks += flush(carry_overlap=True)
        current.append(sent)
        current_words += sw
        if current_words >= TARGET_CHUNK_WORDS:
            chunks += flush(carry_overlap=True)

    chunks += flush(carry_overlap=False)
    return chunks


def build_chunks(text: str) -> list[Chunk]:
    """Chunk the whole document, section by section."""
    chunks: list[Chunk] = []
    next_id = 0
    for title, body in split_into_sections(text):
        section_chunks = chunk_section(title, body, next_id)
        chunks.extend(section_chunks)
        next_id += len(section_chunks)
    return chunks


# --------------------------------------------------------------------------- #
# The pipeline
# --------------------------------------------------------------------------- #
class RAGPipeline:
    def __init__(
        self,
        pdf_path: str = DEFAULT_PDF,
        embed_model_name: str = EMBED_MODEL_NAME,
        llm_model: Optional[str] = None,
    ):
        self.pdf_path = pdf_path
        self.embed_model_name = embed_model_name
        # If not overridden, resolve the model from whichever API key is set.
        self.llm_model = llm_model or active_model()
        self._embedder: Optional[SentenceTransformer] = None
        self.index: Optional[faiss.Index] = None
        self.chunks: list[Chunk] = []
        # Why the most recent LLM call returned nothing (None = it succeeded).
        # Lets the UI say "quota exceeded", not a misleading "no key set".
        self.last_llm_error: Optional[str] = None

    # -- embedding model (lazy load: it is the slowest import) -------------- #
    @property
    def embedder(self) -> SentenceTransformer:
        if self._embedder is None:
            print(f"[rag] loading embedding model: {self.embed_model_name}")
            self._embedder = SentenceTransformer(self.embed_model_name)
        return self._embedder

    def _embed(self, texts: list[str]) -> np.ndarray:
        """Encode texts to L2-normalised float32 vectors (cosine via dot product)."""
        vecs = self.embedder.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return vecs.astype("float32")

    # -- Stage 4 & 5: build embeddings + FAISS index ----------------------- #
    def build(self, force: bool = False) -> "RAGPipeline":
        """Build (or load from cache) the chunk metadata and FAISS index."""
        if not force and os.path.exists(INDEX_PATH) and os.path.exists(META_PATH):
            return self.load()

        print("[rag] extracting and cleaning PDF text ...")
        text = clean_text(extract_text(self.pdf_path))

        print("[rag] chunking ...")
        self.chunks = build_chunks(text)
        print(f"[rag] created {len(self.chunks)} chunks")

        print("[rag] embedding chunks ...")
        embeddings = self._embed([c.text for c in self.chunks])
        dim = embeddings.shape[1]

        print(f"[rag] building FAISS IndexFlatIP (dim={dim}) ...")
        index = faiss.IndexFlatIP(dim)   # inner product == cosine on unit vectors
        index.add(embeddings)
        self.index = index

        self._save()
        return self

    def _save(self) -> None:
        # NOTE: faiss.write_index() uses a C++ file writer that cannot open
        # paths containing non-ASCII characters on Windows (this project lives
        # under a Cyrillic "Документы" folder). We therefore serialise the index
        # to a byte buffer and write it with Python's open(), which handles
        # Unicode paths correctly.
        index_bytes = faiss.serialize_index(self.index).tobytes()
        with open(INDEX_PATH, "wb") as f:
            f.write(index_bytes)
        meta = {
            "embed_model": self.embed_model_name,
            "chunks": [
                {"chunk_id": c.chunk_id, "section": c.section, "text": c.text}
                for c in self.chunks
            ],
        }
        with open(META_PATH, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        print(f"[rag] saved index -> {INDEX_PATH}")
        print(f"[rag] saved chunks -> {META_PATH}")

    def load(self) -> "RAGPipeline":
        # Mirror of _save(): read raw bytes with Python, deserialise with faiss.
        with open(INDEX_PATH, "rb") as f:
            index_bytes = f.read()
        self.index = faiss.deserialize_index(
            np.frombuffer(index_bytes, dtype="uint8")
        )
        with open(META_PATH, "r", encoding="utf-8") as f:
            meta = json.load(f)
        self.chunks = [
            Chunk(chunk_id=c["chunk_id"], section=c["section"], text=c["text"])
            for c in meta["chunks"]
        ]
        return self

    # -- Stage 6: retrieval ------------------------------------------------- #
    def retrieve(
        self, query: str, k: int = 4, min_score: float = 0.0
    ) -> list[RetrievedChunk]:
        """Return the top-k chunks above min_score, most similar first."""
        if self.index is None:
            raise RuntimeError("Index not built. Call build() or load() first.")
        qvec = self._embed([query])
        scores, idxs = self.index.search(qvec, k)
        results: list[RetrievedChunk] = []
        for score, idx in zip(scores[0], idxs[0]):
            if idx == -1 or score < min_score:
                continue
            results.append(RetrievedChunk(chunk=self.chunks[idx], score=float(score)))
        return results

    # -- Stage 7: generation ----------------------------------------------- #
    def _build_prompt(self, query: str, contexts: list[RetrievedChunk]) -> str:
        blocks = []
        for r in contexts:
            blocks.append(f"[Source: {r.chunk.section}]\n{r.chunk.text}")
        context_str = "\n\n---\n\n".join(blocks)
        return (
            "Answer the user's question using ONLY the context passages below.\n"
            "Cite the section titles you used in square brackets, e.g. "
            "[4. The Roman Military]. If the answer is not contained in the "
            "context, say so plainly instead of guessing.\n\n"
            f"=== CONTEXT ===\n{context_str}\n\n"
            f"=== QUESTION ===\n{query}\n\n"
            "=== ANSWER ==="
        )

    # Default system prompt shared by both providers.
    SYSTEM_PROMPT = (
        "You are a precise history assistant. You answer strictly from the "
        "provided context and cite the section titles used."
    )

    # "Ask the Emperor" mode: same retrieval, same grounding rules, but the
    # answer is voiced by a historical figure. Style changes; facts must not.
    PERSONAS: dict[str, dict] = {
        "historian": {
            "title": "Modern historian (default)",
            "emoji": "📖",
            "system": None,  # falls back to SYSTEM_PROMPT
        },
        "marcus_aurelius": {
            "title": "Marcus Aurelius — Stoic emperor",
            "emoji": "🏛️",
            "system": (
                "You are Marcus Aurelius, Roman emperor and Stoic philosopher, "
                "reflecting in the quiet of your campaign tent. Speak in the "
                "first person: measured, meditative, addressing the reader as "
                "a fellow student of life. You may refer to Rome as 'my "
                "empire' and to Romans as 'my people'. STRICT RULES: every "
                "factual claim must come from the provided context passages "
                "only — never from outside knowledge; cite the section titles "
                "in square brackets exactly like a scholar would, e.g. "
                "[4. The Roman Military]; if the context does not contain the "
                "answer, admit it with Stoic composure instead of inventing."
            ),
        },
        "cicero": {
            "title": "Cicero — orator of the Republic",
            "emoji": "🗣️",
            "system": (
                "You are Marcus Tullius Cicero, Rome's greatest orator, "
                "addressing the Senate. Speak in the first person with "
                "rhetorical flair: vivid openings, rhetorical questions, an "
                "occasional Latin flourish (translated in parentheses). "
                "STRICT RULES: every factual claim must come from the provided "
                "context passages only — never from outside knowledge; cite "
                "the section titles in square brackets, e.g. "
                "[2. From Republic to Empire]; if the context does not contain "
                "the answer, concede the point gracefully instead of inventing."
            ),
        },
        "legionary": {
            "title": "Veteran legionary — soldier's view",
            "emoji": "⚔️",
            "system": (
                "You are a grizzled veteran centurion of the Roman legions, "
                "explaining things plainly over a cup of cheap wine. Blunt, "
                "practical, a little wry; you respect facts the way you "
                "respect orders. STRICT RULES: every factual claim must come "
                "from the provided context passages only — never from outside "
                "knowledge; cite the section titles in square brackets, e.g. "
                "[4. The Roman Military]; if the context does not contain the "
                "answer, say so straight instead of inventing."
            ),
        },
        # Easter egg: unlocked by clicking the "67" on the Timeline tab.
        "emperor67": {
            "title": "Emperor Six-Seven — gen-alpha caesar",
            "emoji": "🗿",
            "system": (
                "You are Emperor Six-Seven (Imperator Sixtus Septimus LXVII), "
                "a generation-alpha Roman emperor with terminal brainrot. "
                "You ALWAYS answer in English, in pure gen-alpha brainrot "
                "slang, and you commit to it HARD: drop 'six seven' / '6 7' "
                "constantly, plus 'skibidi', 'sigma', 'rizz' / 'rizzler', "
                "'cringe', 'based', 'aura +1000', 'chupapi munyanyo', "
                "'tun tun tun sahur', 'NPC behavior', 'no cap', 'fr fr', "
                "'lowkey', 'cooked', 'massive W', 'it's giving', 'ohio'. "
                "Short chaotic hype sentences, emoji like 🗿🔥💀🥶, occasional "
                "ALL CAPS. BUT deep down you respect the imperial archives: "
                "STRICT RULES: every factual claim must come from the "
                "provided context passages only — never from outside "
                "knowledge; cite the section titles in square brackets after "
                "the facts they support, e.g. [4. The Roman Military]; if "
                "the context does not contain the answer, say the scrolls "
                "don't have it (mad cringe 💀) instead of inventing."
            ),
        },
    }

    def persona_system(self, persona: Optional[str]) -> str:
        """Resolve the system prompt for a persona key (None -> default)."""
        spec = self.PERSONAS.get(persona or "historian")
        if spec and spec["system"]:
            return spec["system"]
        return self.SYSTEM_PROMPT

    def _call_llm(self, user_prompt: str, system: Optional[str] = None) -> Optional[str]:
        """
        Dispatch a chat request to whichever provider has an API key set.
        Returns the answer text, or None if no provider is configured / a call
        fails (so the caller can fall back to extractive mode).
        """
        provider = llm_provider()
        if provider is None:
            self.last_llm_error = "no API key set"
            return None
        for attempt in (1, 2, 3):
            try:
                if provider == "gemini":
                    result = self._call_gemini(user_prompt, system)
                else:
                    result = self._call_anthropic(user_prompt, system)
                self.last_llm_error = None
                return result
            except Exception as e:  # network/auth/quota/etc.
                self.last_llm_error = _short_llm_error(e)
                transient = "503" in str(e) or "UNAVAILABLE" in str(e)
                if transient and attempt < 3:
                    print(f"[rag] LLM overloaded (attempt {attempt}); retrying …")
                    time.sleep(2 * attempt)
                    continue
                print(f"[rag] LLM call failed ({e}); falling back to extractive answer.")
                break
        return None

    def _call_gemini(self, user_prompt: str, system: Optional[str]) -> str:
        """Call Google Gemini (or Gemma) via the google-genai SDK."""
        from google import genai
        from google.genai import types

        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        client = genai.Client(api_key=api_key)

        # Gemma models (huge free-tier quota) accept neither system_instruction
        # nor thinking_config, so the system prompt is folded into the request.
        if GEMINI_MODEL.startswith("gemma"):
            contents = (
                f"[Instructions]\n{system}\n\n{user_prompt}" if system else user_prompt
            )
            config = types.GenerateContentConfig(
                max_output_tokens=2048, temperature=0.2
            )
        else:
            contents = user_prompt
            config = types.GenerateContentConfig(
                system_instruction=system,
                max_output_tokens=2048,
                temperature=0.2,
                # Gemini 2.5 models enable "thinking" by default, and those
                # hidden reasoning tokens are billed against max_output_tokens —
                # which can truncate or even empty out the visible answer.
                # We disable thinking so the whole budget goes to the response.
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            )
        resp = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=config,
        )
        text = (resp.text or "").strip()
        if not text:
            # Defensive: surface why nothing came back instead of a blank box.
            reason = ""
            try:
                reason = str(resp.candidates[0].finish_reason)
            except Exception:
                pass
            return f"(Gemini returned no text. finish_reason={reason or 'unknown'})"
        return text

    def _call_anthropic(self, user_prompt: str, system: Optional[str]) -> str:
        """Call Anthropic Claude via the anthropic SDK."""
        import anthropic

        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        kwargs = {
            "model": ANTHROPIC_MODEL,
            "max_tokens": 2048,
            "messages": [{"role": "user", "content": user_prompt}],
        }
        if system:
            kwargs["system"] = system
        msg = client.messages.create(**kwargs)
        return "".join(b.text for b in msg.content if b.type == "text").strip()

    def _extractive_answer(self, contexts: list[RetrievedChunk]) -> str:
        """Fallback: return the top retrieved passage(s) verbatim with citations."""
        if not contexts:
            return "No relevant passage was found in the document."
        reason = (self.last_llm_error or "no LLM key set").rstrip(".")
        lines = [f"(Extractive fallback — {reason}. Most relevant passages:)\n"]
        for r in contexts[:2]:
            lines.append(f"[{r.chunk.section}] (score={r.score:.3f})\n{r.chunk.text}\n")
        return "\n".join(lines)

    def answer(
        self,
        query: str,
        k: int = 4,
        use_llm: bool = True,
        min_score: float = 0.0,
        persona: Optional[str] = None,
    ) -> Answer:
        """Full RAG: retrieve context, then generate an answer.

        `persona` selects a voice from PERSONAS ("Ask the Emperor" mode);
        retrieval and grounding rules are identical for every persona.
        """
        t0 = time.time()
        contexts = self.retrieve(query, k=k, min_score=min_score)

        if use_llm and contexts:
            prompt = self._build_prompt(query, contexts)
            text = self._call_llm(prompt, system=self.persona_system(persona))
            if text is not None:
                return Answer(query, text, contexts, "rag", time.time() - t0, self.llm_model)

        text = self._extractive_answer(contexts)
        return Answer(query, text, contexts, "extractive", time.time() - t0, "none")

    def answer_without_rag(self, query: str) -> Answer:
        """Baseline: ask the LLM the same question with NO retrieved context."""
        t0 = time.time()
        text = self._call_llm(query)  # no system prompt, no injected context
        if text is None:
            reason = self.last_llm_error or "no API key set"
            text = f"(Baseline 'no-RAG' answer unavailable: {reason})"
        return Answer(query, text, [], "no-context", time.time() - t0, self.llm_model)


# --------------------------------------------------------------------------- #
# CLI entry point: build the index
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build the RAG index from the PDF.")
    parser.add_argument("--force", action="store_true", help="rebuild even if cached")
    args = parser.parse_args()

    rag = RAGPipeline().build(force=args.force)
    print(f"\n[rag] ready: {len(rag.chunks)} chunks indexed.")
    # Quick sanity retrieval (no LLM call needed).
    demo_q = "How was the Roman army organised?"
    print(f"\n[rag] sample retrieval for: {demo_q!r}")
    for r in rag.retrieve(demo_q, k=3):
        preview = r.chunk.text[:120].replace("\n", " ")
        print(f"  score={r.score:.3f}  [{r.chunk.section}]  {preview}...")
