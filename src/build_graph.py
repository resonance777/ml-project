"""
build_graph.py
==============
Extract a knowledge graph and a timeline of dated events from the Roman Empire
source document, using the same LLM provider as the RAG pipeline.

For every document section the LLM returns strict JSON with:
  * entities  — people, battles, places, institutions, concepts
  * relations — (source, relation, target) triples between those entities
  * events    — dated events {year, era, label} for the timeline

The merged result is cached to data/graph.json so the Streamlit app can render
the graph instantly and without an API key. Re-run this script (with a key set)
to regenerate:

    python src/build_graph.py [--force]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from content import SECTIONS  # noqa: E402
from rag_pipeline import (  # noqa: E402
    ANTHROPIC_MODEL,
    DATA_DIR,
    GEMINI_MODEL,
    llm_provider,
)

GRAPH_PATH = os.path.join(DATA_DIR, "graph.json")

ENTITY_TYPES = ["person", "battle", "place", "institution", "concept"]

EXTRACT_PROMPT = """\
You are building a knowledge graph from a historical text about the Roman Empire.
Read the section below and extract:

1. "entities": the important proper entities mentioned. Each entity:
   {{"label": "<short canonical name>", "type": "<one of: person, battle, place, institution, concept>"}}
   Use canonical names (e.g. "Julius Caesar", not "Caesar's"). 5-12 entities.

2. "relations": factual relations BETWEEN the entities you listed. Each:
   {{"source": "<entity label>", "relation": "<2-4 word verb phrase>", "target": "<entity label>"}}
   Only use labels that appear in your "entities" list. 4-10 relations.

3. "events": dated events for a timeline. Each:
   {{"year": <positive integer>, "era": "BCE" or "CE", "label": "<event, max 8 words>"}}
   Extract EVERY event that has an explicit year in the text — do not skip any.
   A year range like "235-284 CE" gives one event per endpoint. If the text has
   no explicit years, return an empty list.

Return ONLY a valid JSON object with keys "entities", "relations", "events".
No markdown fences, no commentary.

=== SECTION: {title} ===
{body}
"""


# --------------------------------------------------------------------------- #
# LLM call (own call with a large output budget — graphs are token-hungry)
# --------------------------------------------------------------------------- #
def _call_llm_json(prompt: str) -> dict:
    provider = llm_provider()
    if provider == "gemini":
        from google import genai
        from google.genai import types

        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        client = genai.Client(api_key=api_key)
        resp = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=8192,
                temperature=0.1,
                response_mime_type="application/json",
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )
        raw = resp.text or ""
    elif provider == "anthropic":
        import anthropic

        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        msg = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=8192,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = "".join(b.text for b in msg.content if b.type == "text")
    else:
        raise RuntimeError(
            "No LLM API key set (GEMINI_API_KEY or ANTHROPIC_API_KEY). "
            "The graph is built once with an LLM and then cached."
        )

    # Strip accidental markdown fences and parse.
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip())
    return json.loads(raw)


# --------------------------------------------------------------------------- #
# Merge per-section extractions into one graph
# --------------------------------------------------------------------------- #
def _canon(label: str) -> str:
    """Normalisation key used to deduplicate entities across sections."""
    return re.sub(r"[^a-z0-9]", "", label.lower())


def _extract_section(title: str, body: str, max_attempts: int = 3) -> dict:
    """One section's extraction, with retries for rate limits / bad JSON."""
    for attempt in range(1, max_attempts + 1):
        try:
            return _call_llm_json(EXTRACT_PROMPT.format(title=title, body=body))
        except Exception as e:
            msg = str(e)
            if attempt == max_attempts:
                raise
            # Rate limit: respect the server's suggested delay if present.
            wait = 20.0 * attempt
            m = re.search(r"retry in (\d+(?:\.\d+)?)s", msg, re.IGNORECASE)
            if m:
                wait = float(m.group(1)) + 2
            print(f"[graph]   attempt {attempt} failed ({msg[:90]}…) — "
                  f"retrying in {wait:.0f}s")
            time.sleep(wait)


def build_graph() -> dict:
    entities: dict[str, dict] = {}   # canon key -> entity
    relations: list[dict] = []
    events: list[dict] = []
    seen_rel: set[tuple] = set()
    seen_evt: set[tuple] = set()
    failed: list[str] = []

    for title, paragraphs in SECTIONS:
        body = "\n\n".join(paragraphs)
        print(f"[graph] extracting: {title}")
        try:
            data = _extract_section(title, body)
        except Exception as e:
            print(f"[graph]   FAILED ({str(e)[:120]}) — skipping section")
            failed.append(title)
            continue

        local_labels: dict[str, str] = {}  # canon -> label as returned here
        for ent in data.get("entities", []):
            label = str(ent.get("label", "")).strip()
            etype = str(ent.get("type", "concept")).strip().lower()
            if not label:
                continue
            if etype not in ENTITY_TYPES:
                etype = "concept"
            key = _canon(label)
            local_labels[key] = label
            if key not in entities:
                entities[key] = {"label": label, "type": etype, "sections": [title]}
            elif title not in entities[key]["sections"]:
                entities[key]["sections"].append(title)

        for rel in data.get("relations", []):
            s, r, t = (
                str(rel.get("source", "")).strip(),
                str(rel.get("relation", "")).strip(),
                str(rel.get("target", "")).strip(),
            )
            sk, tk = _canon(s), _canon(t)
            # Keep only relations whose endpoints are known entities.
            if not r or sk not in entities or tk not in entities or sk == tk:
                continue
            sig = (sk, r.lower(), tk)
            if sig in seen_rel:
                continue
            seen_rel.add(sig)
            relations.append(
                {
                    "source": entities[sk]["label"],
                    "relation": r,
                    "target": entities[tk]["label"],
                    "section": title,
                }
            )

        for evt in data.get("events", []):
            try:
                year = int(evt.get("year"))
            except (TypeError, ValueError):
                continue
            era = str(evt.get("era", "CE")).upper()
            label = str(evt.get("label", "")).strip()
            if not label or era not in ("BCE", "CE"):
                continue
            sig = (year, era, _canon(label))
            if sig in seen_evt:
                continue
            seen_evt.add(sig)
            events.append(
                {"year": year, "era": era, "label": label, "section": title}
            )

    # A mostly-failed extraction must never clobber a good cached graph.
    if len(failed) > len(SECTIONS) // 3:
        raise RuntimeError(
            f"extraction failed for {len(failed)}/{len(SECTIONS)} sections "
            f"({', '.join(failed[:3])}…) — not saving a degraded graph. "
            "Wait for the API quota to reset (or set RAG_GEMINI_MODEL to "
            "another model) and re-run."
        )

    # Sort events on a single numeric axis: BCE years are negative.
    events.sort(key=lambda e: -e["year"] if e["era"] == "BCE" else e["year"])

    return {
        "entities": sorted(entities.values(), key=lambda e: e["label"]),
        "relations": relations,
        "events": events,
    }


def load_graph() -> dict | None:
    """Load the cached graph, or None if it is missing or empty."""
    if not os.path.exists(GRAPH_PATH):
        return None
    with open(GRAPH_PATH, "r", encoding="utf-8") as f:
        graph = json.load(f)
    return graph if graph.get("entities") else None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build data/graph.json with an LLM.")
    parser.add_argument("--force", action="store_true", help="rebuild even if cached")
    args = parser.parse_args()

    if os.path.exists(GRAPH_PATH) and not args.force:
        g = load_graph()
        print(
            f"[graph] cached graph exists: {len(g['entities'])} entities, "
            f"{len(g['relations'])} relations, {len(g['events'])} events. "
            "Use --force to rebuild."
        )
        sys.exit(0)

    graph = build_graph()
    with open(GRAPH_PATH, "w", encoding="utf-8") as f:
        json.dump(graph, f, ensure_ascii=False, indent=2)
    print(
        f"\n[graph] saved -> {GRAPH_PATH}\n"
        f"[graph] {len(graph['entities'])} entities, "
        f"{len(graph['relations'])} relations, {len(graph['events'])} events"
    )
