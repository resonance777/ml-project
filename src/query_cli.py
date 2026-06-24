"""
query_cli.py
============
Interactive command-line interface for the Roman Empire RAG system.

Usage
-----
    # Interactive REPL:
    python src/query_cli.py

    # One-shot question:
    python src/query_cli.py -q "Why did the Western Roman Empire fall?"

    # Tuning:
    python src/query_cli.py -q "..." -k 5          # retrieve top-5 chunks
    python src/query_cli.py -q "..." --show-context # print retrieved passages
    python src/query_cli.py -q "..." --no-llm       # extractive mode only

The first run builds/loads the FAISS index; subsequent runs reuse the cache.
Set ANTHROPIC_API_KEY (e.g. in a .env file) to get LLM-generated answers;
without it, the CLI returns the most relevant retrieved passages (extractive).
"""

from __future__ import annotations

import argparse
import os
import sys

# Allow running both as "python src/query_cli.py" and from inside src/.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rag_pipeline import RAGPipeline, llm_provider  # noqa: E402


def print_answer(ans, show_context: bool) -> None:
    print("\n" + "=" * 70)
    print(f"Q: {ans.question}")
    print("-" * 70)
    print(ans.answer)
    print("-" * 70)
    print(
        f"[mode={ans.mode}  model={ans.model}  "
        f"retrieved={len(ans.contexts)}  latency={ans.latency_s:.2f}s]"
    )
    if show_context and ans.contexts:
        print("\nRetrieved context:")
        for i, r in enumerate(ans.contexts, 1):
            preview = r.chunk.text.replace("\n", " ")
            if len(preview) > 240:
                preview = preview[:240] + "..."
            print(f"  {i}. score={r.score:.3f}  [{r.chunk.section}]")
            print(f"     {preview}")
    print("=" * 70 + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask questions about the Roman Empire (RAG).")
    parser.add_argument("-q", "--question", help="ask a single question and exit")
    parser.add_argument("-k", type=int, default=4, help="number of chunks to retrieve")
    parser.add_argument("--no-llm", action="store_true", help="extractive mode (no LLM call)")
    parser.add_argument("--show-context", action="store_true", help="print retrieved passages")
    parser.add_argument("--min-score", type=float, default=0.0, help="minimum cosine score filter")
    args = parser.parse_args()

    print("[cli] loading RAG pipeline ...")
    rag = RAGPipeline().build()  # builds on first run, loads cache afterwards
    provider = llm_provider()
    llm_status = f"on ({provider}: {rag.llm_model})" if provider and not args.no_llm else "off (extractive)"
    print(f"[cli] ready ({len(rag.chunks)} chunks). LLM={llm_status}")

    use_llm = not args.no_llm

    if args.question:
        ans = rag.answer(args.question, k=args.k, use_llm=use_llm, min_score=args.min_score)
        print_answer(ans, args.show_context)
        return

    # Interactive REPL
    print("\nType a question, or 'quit' to exit. Prefix with 'ctx:' to show context.\n")
    while True:
        try:
            line = input("ask> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nbye!")
            break
        if not line:
            continue
        if line.lower() in {"quit", "exit", "q"}:
            print("bye!")
            break
        show_ctx = args.show_context
        if line.lower().startswith("ctx:"):
            show_ctx = True
            line = line[4:].strip()
        ans = rag.answer(line, k=args.k, use_llm=use_llm, min_score=args.min_score)
        print_answer(ans, show_ctx)


if __name__ == "__main__":
    main()
