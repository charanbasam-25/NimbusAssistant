"""Tests for source-page and included-code retrieval evaluation."""

import json

import pytest

from run_retrieval import load_questions, score_code_retrieval


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
