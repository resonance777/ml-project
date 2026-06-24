"""
evaluate.py
===========
Runs a fixed suite of diverse historical questions through the RAG pipeline and
reports:

* Retrieval accuracy   -> did the expected source section appear in the top-k?
* Relevance score      -> cosine similarity of the best retrieved chunk.
* Latency              -> wall-clock time per query.
* Answers              -> the generated (or extractive) answer per question.

It also writes a Markdown report to docs/results.md so the numbers can be
dropped straight into the project documentation. Works with or without an
ANTHROPIC_API_KEY (LLM answers when present, extractive passages otherwise).

Run:
    python src/evaluate.py
"""

from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rag_pipeline import PROJECT_ROOT, RAGPipeline, llm_provider  # noqa: E402

# Each item: (question, substring expected to appear in a correct source section)
EVAL_QUESTIONS = [
    ("When and how was Rome founded according to tradition?", "Origins"),
    ("How was the Roman legion organised and equipped?", "Military"),
    ("What goods did Rome trade and with whom?", "Economy"),
    ("What was the role of slaves in Roman society?", "Society"),
    ("How did Christianity become the official religion of Rome?", "Religion"),
    ("What engineering innovations are the Romans known for?", "Engineering"),
    ("Why did the Western Roman Empire fall in 476 CE?", "Decline"),
    ("Who were the Five Good Emperors?", "Emperors"),
    ("What rights did Roman women have?", "Women"),
    ("What was the Crisis of the Third Century?", "Crisis"),
]


def run_eval(k: int = 4, use_llm: bool = True) -> str:
    rag = RAGPipeline().build()
    llm_on = bool(llm_provider()) and use_llm

    lines = []
    lines.append("# RAG Evaluation Results\n")
    lines.append(f"- Embedding model: `{rag.embed_model_name}`")
    lines.append(f"- LLM: `{rag.llm_model if llm_on else 'extractive fallback (no API key)'}`")
    lines.append(f"- Chunks indexed: {len(rag.chunks)}")
    lines.append(f"- top-k: {k}\n")

    hits = 0
    top1_scores = []
    latencies = []

    for q, expect in EVAL_QUESTIONS:
        t0 = time.time()
        retrieved = rag.retrieve(q, k=k)
        retrieve_t = time.time() - t0

        sections = [r.chunk.section for r in retrieved]
        hit = any(expect.lower() in s.lower() for s in sections)
        hits += int(hit)
        top1 = retrieved[0].score if retrieved else 0.0
        top1_scores.append(top1)

        ans = rag.answer(q, k=k, use_llm=use_llm)
        latencies.append(ans.latency_s)

        lines.append(f"## Q: {q}")
        lines.append(f"- Expected section keyword: `{expect}` -> "
                     f"**{'HIT' if hit else 'MISS'}**")
        lines.append(f"- Top-1 cosine score: `{top1:.3f}`  | retrieval time: `{retrieve_t*1000:.0f} ms`")
        lines.append(f"- Retrieved sections: {', '.join(f'[{s}]' for s in sections)}")
        lines.append(f"- Answer latency: `{ans.latency_s:.2f}s`  (mode: {ans.mode})")
        lines.append("")
        lines.append("**Answer:**")
        lines.append("")
        lines.append(ans.answer)
        lines.append("\n---\n")

    n = len(EVAL_QUESTIONS)
    avg_top1 = sum(top1_scores) / n
    avg_lat = sum(latencies) / n
    summary = [
        "## Summary metrics\n",
        f"- **Retrieval accuracy (expected section in top-{k})**: "
        f"{hits}/{n} = {hits / n * 100:.0f}%",
        f"- **Average top-1 cosine relevance**: {avg_top1:.3f}",
        f"- **Average answer latency**: {avg_lat:.2f}s",
        "",
    ]
    # Put summary near the top of the report (after the 5 header lines).
    report = "\n".join(lines[:5] + summary + lines[5:])

    out_path = os.path.join(PROJECT_ROOT, "docs", "results.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(report)

    print("\n".join(summary))
    print(f"[eval] full report written to {out_path}")
    return report


if __name__ == "__main__":
    run_eval()
