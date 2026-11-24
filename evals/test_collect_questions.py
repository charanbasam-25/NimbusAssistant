"""Offline tests for the Stack Exchange candidate collector."""

import json

from collect_questions import filter_questions, parse_question, plain_text


def test_parses_html_and_preserves_candidate_provenance() -> None:
    raw = json.loads(
        __import__("pathlib")
        .Path(__file__)
        .with_name("fixtures")
        .joinpath("stackoverflow_questions_sample.json")
        .read_text(encoding="utf-8")
    )
    candidate = parse_question(raw["items"][0], collected_on="2026-11-24")

    assert candidate is not None
    assert candidate["source_id"] == "701"
    assert candidate["body_excerpt"] == (
        "I need to add a custom header to one endpoint response. What is the recommended approach?"
    )
    assert candidate["license"] == "CC BY-SA 4.0"
    assert candidate["collected_on"] == "2026-11-24"
    assert candidate["has_accepted_answer"] is True


def test_filters_duplicates_other_library_cloud_and_low_quality_questions() -> None:
    raw = json.loads(
        __import__("pathlib")
        .Path(__file__)
        .with_name("fixtures")
        .joinpath("stackoverflow_questions_sample.json")
        .read_text(encoding="utf-8")
    )
    candidates = filter_questions(raw["items"], collected_on="2026-11-24")

    assert [candidate["source_id"] for candidate in candidates] == ["701", "705"]
    assert candidates[0]["score"] > candidates[1]["score"]


def test_rejects_questions_without_accepted_answer_or_score_threshold() -> None:
    item = {
        "question_id": 88,
        "title": "How should I configure a FastAPI dependency?",
        "body": "<p>I need to understand dependency injection for my application.</p>",
        "tags": ["fastapi"],
        "score": 1,
        "accepted_answer_id": None,
    }

    assert parse_question(item) is None


def test_rejects_code_dump_and_non_english_question() -> None:
    code_dump = {
        "question_id": 89,
        "title": "FastAPI code problem",
        "body": "<pre><code>" + ("print('hello world')\n" * 30) + "</code></pre>",
        "tags": ["fastapi"],
        "score": 9,
        "accepted_answer_id": 90,
    }
    non_english = {
        "question_id": 90,
        "title": "¿Cómo puedo usar FastAPI?",
        "body": "<p>¿Cómo puedo configurar esta aplicación para ejecutar una ruta?</p>",
        "tags": ["fastapi"],
        "score": 10,
        "accepted_answer_id": 91,
    }

    assert parse_question(code_dump) is None
    assert parse_question(non_english) is None


def test_plain_text_counts_code_separately() -> None:
    text, code_chars = plain_text("<p>Explanation</p><pre><code>x = 1</code></pre>")

    assert "Explanation" in text
    assert "x = 1" in text
    assert code_chars == 5
