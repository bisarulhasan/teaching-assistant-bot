"""Lightweight eval harness for Noor — measures answer quality objectively.

Designed to be mostly DETERMINISTIC (no eval-LLM), so it runs fast and light:

  - page_hit         : was an expected page actually retrieved?  (retrieval quality)
  - citation_precision: of the sources Noor *shows*, fraction that are expected pages
                        (catches the "too many sources" problem)
  - citation_recall  : fraction of expected pages that Noor cited
  - section_hit      : was the expected section (e.g. "1G") retrieved?
  - keyword_coverage : fraction of must-include facts present in the answer

Usage:
  # full run (retrieval + generation) — needs Weaviate + Ollama
  python -m src.evaluation.harness

  # fast retrieval-only (no LLM) — needs only Weaviate
  python -m src.evaluation.harness --retrieval-only

  # limit to N entries
  python -m src.evaluation.harness --limit 5

Requires the stack up:  docker compose up -d   (and Ollama for a full run).
"""

import argparse
import json
from pathlib import Path

from src.ingestion.embedder import get_weaviate_client
from src.retrieval.bm25_retriever import BM25Retriever
from src.retrieval.hybrid_retriever import hybrid_search
from src.retrieval.reranker import rerank_chunks
from src.generation.generator import generate_answer
from src.config.settings import RETRIEVAL_TOP_K, RERANK_TOP_K

DATASET = "data/eval/golden_maths.json"
OUTPUT = "data/eval/harness_results.json"


def load_dataset(path: str) -> list[dict]:
    with open(path) as f:
        data = json.load(f)
    print(f"Loaded {len(data['entries'])} entries (v{data['version']}) from {path}")
    return data["entries"]


def score_entry(entry: dict, reranked: list[dict], sources: list[dict], answer: str) -> dict:
    expected = set(entry.get("expected_pages", []))
    retrieved_pages = {c["metadata"].get("page") for c in reranked}
    shown_pages = {s.get("page") for s in sources}

    page_hit = bool(expected & retrieved_pages) if expected else None
    cite_precision = (len(shown_pages & expected) / len(shown_pages)) if shown_pages else None
    cite_recall = (len(shown_pages & expected) / len(expected)) if expected else None

    section = entry.get("expected_section")
    section_hit = (
        any(c["metadata"].get("section") == section for c in reranked) if section else None
    )

    kws = entry.get("must_include", [])
    coverage = (
        sum(1 for k in kws if k.lower() in (answer or "").lower()) / len(kws) if kws else None
    )

    return {
        "id": entry["id"],
        "question": entry["question"],
        "expected_pages": sorted(expected),
        "shown_pages": sorted(p for p in shown_pages if p),
        "num_sources": len(sources),
        "page_hit": page_hit,
        "citation_precision": cite_precision,
        "citation_recall": cite_recall,
        "section_hit": section_hit,
        "keyword_coverage": coverage,
    }


def run(dataset_path: str = DATASET, retrieval_only: bool = False, limit: int | None = None) -> dict:
    entries = load_dataset(dataset_path)
    if limit:
        entries = entries[:limit]

    client = get_weaviate_client()
    rows = []
    try:
        bm25 = BM25Retriever(client)
        for i, e in enumerate(entries, 1):
            print(f"  [{i}/{len(entries)}] {e['question'][:60]}")
            filters = {
                "year": e.get("year"),
                "subject": e.get("subject"),
                "course": e.get("course"),
            }
            candidates = hybrid_search(
                e["question"], client, bm25, top_k=RETRIEVAL_TOP_K, filters=filters
            )
            reranked = rerank_chunks(e["question"], candidates, top_k=RERANK_TOP_K)

            if retrieval_only:
                sources, answer = [], ""
            else:
                result = generate_answer(e["question"], reranked, prompt_key="rag_answer_with_reranking")
                sources, answer = result["sources"], result["answer"]

            rows.append(score_entry(e, reranked, sources, answer))
    finally:
        client.close()

    summary = aggregate(rows, retrieval_only)
    out = {"retrieval_only": retrieval_only, "n": len(rows), "summary": summary, "rows": rows}
    Path(OUTPUT).parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w") as f:
        json.dump(out, f, indent=2)
    report(summary, rows, retrieval_only)
    return out


def _mean(values: list) -> float | None:
    vals = [v for v in values if v is not None]
    return round(sum(vals) / len(vals), 3) if vals else None


def aggregate(rows: list[dict], retrieval_only: bool) -> dict:
    metrics = ["page_hit", "citation_precision", "citation_recall", "section_hit", "keyword_coverage"]
    if retrieval_only:
        metrics = ["page_hit", "section_hit"]
    out = {}
    for m in metrics:
        vals = [(1.0 if r[m] else 0.0) if isinstance(r[m], bool) else r[m] for r in rows]
        out[m] = _mean(vals)
    out["avg_sources_shown"] = _mean([r["num_sources"] for r in rows]) if not retrieval_only else None
    return out


def report(summary: dict, rows: list[dict], retrieval_only: bool) -> None:
    print("\n" + "=" * 60)
    print("EVAL HARNESS — " + ("retrieval only" if retrieval_only else "full"))
    print("=" * 60)
    for k, v in summary.items():
        if v is not None:
            print(f"  {k:22s}: {v}")
    # flag the weakest entries
    misses = [r for r in rows if r["page_hit"] is False]
    if misses:
        print(f"\n  Page-misses ({len(misses)}):")
        for r in misses:
            print(f"    - {r['id']}: expected {r['expected_pages']}, retrieved nothing matching")
    print("=" * 60)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--retrieval-only", action="store_true", help="skip generation (no LLM)")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--dataset", default=DATASET)
    args = ap.parse_args()
    run(args.dataset, retrieval_only=args.retrieval_only, limit=args.limit)
