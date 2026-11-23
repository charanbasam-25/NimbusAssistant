"""Measure manifest-grounded retrieval recall and document-access leakage."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path
from typing import Any

import psycopg
from nimbus_api.access import PERSONA_ACCESS, Persona, can_see
from nimbus_api.config import database_url
from nimbus_api.retrieval import search_chunks

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "data" / "synthetic" / "manifest.json"


def build_cases(documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group manifest rows by shared question and compute persona ground truth."""
    by_question: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for document in documents:
        question = document.get("question")
        if question:
            by_question[question].append(document)

    cases: list[dict[str, Any]] = []
    for question, related in by_question.items():
        for persona in ("guest", "R1", "R2"):
            expected = [
                document["source_path"]
                for document in related
                if can_see(persona, document["audience"], document["region"])
            ]
            forbidden = [
                document["source_path"]
                for document in related
                if not can_see(persona, document["audience"], document["region"])
            ]
            cases.append(
                {
                    "query": question,
                    "persona": persona,
                    "expected_doc_ids": expected,
                    "forbidden_doc_ids": forbidden,
                }
            )
    return cases


def evaluate(
    cases: list[dict[str, Any]],
    search_fn: Callable[..., list[dict[str, Any]]],
) -> dict[str, Any]:
    """Count access leaks and micro-average recall over visible expected pages."""
    leaks: list[dict[str, Any]] = []
    leaks_by_persona: dict[str, int] = {persona: 0 for persona in PERSONA_ACCESS}
    expected_total = 0
    expected_hits = 0
    for case in cases:
        persona: Persona = case["persona"]
        expected = set(case["expected_doc_ids"])
        forbidden = set(case["forbidden_doc_ids"])
        results = search_fn(case["query"], persona, limit=20, query_mode="or")
        returned_paths = {chunk["source_path"] for chunk in results}
        expected_total += len(expected)
        expected_hits += len(expected & returned_paths)
        for chunk in results:
            classification = chunk.get("classification") or {}
            invisible = not can_see(
                persona,
                classification.get("audience", ""),
                classification.get("region", ""),
            )
            source_path = chunk["source_path"]
            if invisible or source_path in forbidden:
                leaks.append(
                    {
                        "persona": persona,
                        "query": case["query"],
                        "source_path": source_path,
                        "reason": "access_tags" if invisible else "forbidden_document",
                    }
                )
                leaks_by_persona[persona] += 1

    return {
        "cases": len(cases),
        "leaks": len(leaks),
        "leaks_by_persona": leaks_by_persona,
        "leak_details": leaks,
        "expected_doc_recall": expected_hits / expected_total if expected_total else 1.0,
    }


def run(manifest_path: Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    documents = manifest["documents"]
    source_paths = sorted({document["source_path"] for document in documents})
    with psycopg.connect(database_url()) as connection:
        rows = connection.execute(
            "SELECT source_path FROM documents WHERE source_commit = %s AND source_path = ANY(%s)",
            ("nimbus-cloud-v1", source_paths),
        ).fetchall()
        present = {row[0] for row in rows}
        missing = sorted(set(source_paths) - present)
        if missing:
            raise RuntimeError(f"Synthetic manifest source_paths missing from database: {missing}")

        def search_fn(query: str, persona: Persona, limit: int, query_mode: str):
            return search_chunks(connection, query, persona, limit, query_mode=query_mode)

        result = evaluate(build_cases(documents), search_fn)
    return {"corpus_id": manifest["corpus_id"], **result}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = run(args.manifest)
    rendered = json.dumps(report, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    if report["leaks"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
