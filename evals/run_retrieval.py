"""Run the PostgreSQL full-text retrieval baseline against labeled JSONL questions."""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

import psycopg
from nimbus_api.config import database_url
from nimbus_api.retrieval import PERSONA_ACCESS, search_chunks

ROOT = Path(__file__).resolve().parents[1]
MAX_CANDIDATE_CHUNKS = 20


def load_questions(path: Path) -> list[dict[str, Any]]:
    questions: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for line_number, raw_line in enumerate(path.read_text().splitlines(), start=1):
        if not raw_line.strip():
            continue
        try:
            item = json.loads(raw_line)
        except json.JSONDecodeError as error:
            raise ValueError(f"{path}:{line_number}: invalid JSON: {error}") from error
        if not isinstance(item, dict):
            raise TypeError(f"{path}:{line_number}: each question must be a JSON object")

        required = {
            "id",
            "query",
            "relevant_source_paths",
            "persona",
            "slice",
            "provenance",
        }
        missing = required - item.keys()
        if missing:
            raise ValueError(f"{path}:{line_number}: missing fields: {sorted(missing)}")
        unknown = item.keys() - required - {"notes", "expected_code_sources"}
        if unknown:
            raise ValueError(f"{path}:{line_number}: unknown fields: {sorted(unknown)}")
        if not isinstance(item["id"], str) or not item["id"].strip():
            raise ValueError(f"{path}:{line_number}: id must be a non-empty string")
        if not isinstance(item["query"], str) or len(item["query"].strip()) < 3:
            raise ValueError(f"{path}:{line_number}: query must contain at least 3 characters")
        if not isinstance(item["persona"], str) or item["persona"] not in PERSONA_ACCESS:
            raise ValueError(f"{path}:{line_number}: persona must be guest, R1, or R2")
        if not isinstance(item["slice"], str) or item["slice"] not in {"general", "short_query"}:
            raise ValueError(f"{path}:{line_number}: unsupported slice {item['slice']!r}")
        if not isinstance(item["provenance"], str) or item["provenance"] not in {
            "real",
            "synthetic",
        }:
            raise ValueError(f"{path}:{line_number}: provenance must be real or synthetic")
        if not isinstance(item["relevant_source_paths"], list) or not item["relevant_source_paths"]:
            raise ValueError(f"{path}:{line_number}: relevant_source_paths must be non-empty")
        if not all(
            isinstance(source_path, str) and source_path
            for source_path in item["relevant_source_paths"]
        ):
            raise ValueError(f"{path}:{line_number}: source paths must be non-empty strings")
        if len(set(item["relevant_source_paths"])) != len(item["relevant_source_paths"]):
            raise ValueError(f"{path}:{line_number}: relevant source paths must be unique")
        if "expected_code_sources" in item:
            expected_code_sources = item["expected_code_sources"]
            if not isinstance(expected_code_sources, list) or not expected_code_sources:
                raise ValueError(
                    f"{path}:{line_number}: expected_code_sources must be a non-empty list"
                )
            if not all(isinstance(source, str) and source for source in expected_code_sources):
                raise ValueError(
                    f"{path}:{line_number}: expected code source paths must be non-empty strings"
                )
            if len(set(expected_code_sources)) != len(expected_code_sources):
                raise ValueError(f"{path}:{line_number}: expected code source paths must be unique")
        if item["id"] in seen_ids:
            raise ValueError(f"{path}:{line_number}: duplicate id {item['id']!r}")
        seen_ids.add(item["id"])
        questions.append(item)

    if not questions:
        raise ValueError(f"No evaluation questions found in {path}")
    return questions


def retrieve_keyword_baseline(
    connection: psycopg.Connection[Any],
    question: dict[str, Any],
    limit: int,
    query_mode: str = "and",
) -> list[dict[str, Any]]:
    # Reuse production search so the evaluation measures the same retrieval logic.
    return search_chunks(
        connection, question["query"], question["persona"], limit, query_mode=query_mode
    )


def top_k_documents(passages: list[dict[str, Any]], k: int) -> list[dict[str, Any]]:
    """Keep each page's best-ranked passage, then return the first k pages."""
    seen_paths: set[str] = set()
    documents: list[dict[str, Any]] = []
    for passage in passages:
        source_path = passage["source_path"]
        if source_path not in seen_paths:
            seen_paths.add(source_path)
            documents.append(passage)
            if len(documents) == k:
                break
    return documents


def score_code_retrieval(
    passages: list[dict[str, Any]], expected_code_sources: list[str], k: int
) -> float:
    """Return 1 when a top-k passage contains one of the expected code files."""
    top_content = "\n".join(str(passage["content"]) for passage in passages[:k])
    return float(
        any(
            f"[Example source: {source_path}]" in top_content
            for source_path in expected_code_sources
        )
    )


def score_retrieval(retrieved: list[str], relevant: set[str], k: int) -> dict[str, float]:
    top_k = retrieved[:k]
    hits = [1 if source_path in relevant else 0 for source_path in top_k]
    recall = sum(hits) / len(relevant)
    reciprocal_rank = next((1.0 / rank for rank, hit in enumerate(hits, start=1) if hit), 0.0)
    dcg = sum(hit / math.log2(rank + 1) for rank, hit in enumerate(hits, 1))
    ideal_hits = min(len(relevant), k)
    idcg = sum(1.0 / math.log2(rank + 1) for rank in range(1, ideal_hits + 1))
    return {"recall": recall, "ndcg": dcg / idcg if idcg else 0.0, "mrr": reciprocal_rank}


def aggregate(rows: list[dict[str, Any]]) -> dict[str, float | int]:
    if not rows:
        return {"questions": 0, "recall_at_k": 0.0, "ndcg_at_k": 0.0, "mrr": 0.0}
    return {
        "questions": len(rows),
        "recall_at_k": mean(row["metrics"]["recall"] for row in rows),
        "ndcg_at_k": mean(row["metrics"]["ndcg"] for row in rows),
        "mrr": mean(row["metrics"]["mrr"] for row in rows),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument(
        "--candidates",
        type=int,
        default=MAX_CANDIDATE_CHUNKS,
        help="maximum ranked chunks to consider before collapsing to distinct pages (k to 20)",
    )
    parser.add_argument(
        "--query-mode",
        choices=("and", "or"),
        default="and",
        help="use strict all-term matching (and) or experimental any-term matching (or)",
    )
    args = parser.parse_args()
    if args.k < 1:
        parser.error("--k must be at least 1")
    if not args.k <= args.candidates <= MAX_CANDIDATE_CHUNKS:
        parser.error(f"--candidates must be between --k and {MAX_CANDIDATE_CHUNKS}")

    questions = load_questions(args.dataset)
    results = []
    with psycopg.connect(database_url()) as connection:
        for question in questions:
            passages = retrieve_keyword_baseline(
                connection, question, args.candidates, query_mode=args.query_mode
            )
            # Rank source pages by their best chunk, so one verbose page cannot
            # consume several of the evaluation's top-k relevance slots.
            top_documents = top_k_documents(passages, args.k)
            retrieved = [passage["source_path"] for passage in top_documents]
            metrics = score_retrieval(
                retrieved,
                set(question["relevant_source_paths"]),
                args.k,
            )
            result = {
                "id": question["id"],
                "provenance": question["provenance"],
                "slice": question["slice"],
                "retrieved_source_paths": retrieved,
                "candidate_chunks": len(passages),
                "metrics": metrics,
            }
            if "expected_code_sources" in question:
                result["expected_code_sources"] = question["expected_code_sources"]
                result["code_hit_at_k"] = score_code_retrieval(
                    passages[: args.k], question["expected_code_sources"], args.k
                )
            results.append(result)

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for result in results:
        grouped["overall"].append(result)
        grouped[f"provenance:{result['provenance']}"].append(result)
        grouped[f"slice:{result['slice']}"].append(result)

    report = {
        "baseline": f"postgresql_full_text_ts_rank_cd_{args.query_mode}",
        "query_mode": args.query_mode,
        "k": args.k,
        "candidate_chunks": args.candidates,
        "dataset": str(args.dataset),
        "summary": {key: aggregate(rows) for key, rows in sorted(grouped.items())},
        "results": results,
    }
    code_rows = [result for result in results if "code_hit_at_k" in result]
    if code_rows:
        report["code_example_summary"] = {
            "questions": len(code_rows),
            "hit_at_k": mean(result["code_hit_at_k"] for result in code_rows),
        }
    rendered = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n")
    print(rendered)


if __name__ == "__main__":
    main()
