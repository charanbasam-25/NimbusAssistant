"""Tests for source-page and included-code retrieval evaluation."""

import json

import pytest

from run_retrieval import load_questions, score_code_retrieval, top_k_documents


def test_code_score_hits_when_expected_source_is_in_top_k() -> None:
    passages = [
        {"content": "The concept is here."},
        {"content": "[Example source: docs_src/body/tutorial001.py]\n```py\n...\n```"},
    ]

    assert score_code_retrieval(passages, ["docs_src/body/tutorial001.py"], k=2) == 1.0


def test_code_score_misses_when_expected_source_is_below_k() -> None:
    passages = [
        {"content": "[Example source: docs_src/other.py]"},
        {"content": "[Example source: docs_src/body/tutorial001.py]"},
    ]

    assert score_code_retrieval(passages, ["docs_src/body/tutorial001.py"], k=1) == 0.0


def test_loader_accepts_code_source_labels(tmp_path) -> None:
    question = {
        "id": "synthetic-code-test",
        "query": "Pydantic request body example",
        "relevant_source_paths": ["tutorial/body.md"],
        "expected_code_sources": ["docs_src/body/tutorial001.py"],
        "persona": "guest",
        "slice": "general",
        "provenance": "synthetic",
    }
    dataset = tmp_path / "questions.jsonl"
    dataset.write_text(json.dumps(question) + "\n", encoding="utf-8")

    assert load_questions(dataset)[0]["expected_code_sources"] == [
        "docs_src/body/tutorial001.py"
    ]


def test_loader_rejects_empty_code_source_labels(tmp_path) -> None:
    question = {
        "id": "synthetic-code-test",
        "query": "Pydantic request body example",
        "relevant_source_paths": ["tutorial/body.md"],
        "expected_code_sources": [],
        "persona": "guest",
        "slice": "general",
        "provenance": "synthetic",
    }
    dataset = tmp_path / "questions.jsonl"
    dataset.write_text(json.dumps(question) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="expected_code_sources"):
        load_questions(dataset)


def test_top_k_documents_does_not_spend_slots_on_repeated_pages() -> None:
    passages = [
        {"source_path": "a.md", "ordinal": 0},
        {"source_path": "a.md", "ordinal": 1},
        {"source_path": "a.md", "ordinal": 2},
        {"source_path": "b.md", "ordinal": 0},
        {"source_path": "c.md", "ordinal": 0},
    ]

    assert top_k_documents(passages, 2) == [passages[0], passages[3]]


def test_top_k_documents_keeps_each_pages_best_rank() -> None:
    passages = [
        {"source_path": "b.md", "score": 0.9},
        {"source_path": "a.md", "score": 0.8},
        {"source_path": "b.md", "score": 0.7},
    ]

    assert top_k_documents(passages, 2) == passages[:2]
