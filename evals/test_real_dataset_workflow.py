"""Tests for gated real-label export and dataset validation."""

import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_real_dataset import confirmed_records
from validate_real_datasets import validate_datasets


def _candidate(source_id: str, confirmed: bool, answerable: bool) -> str:
    label = {
        "source_id": source_id,
        "source_url": f"https://stackoverflow.com/q/{source_id}",
        "query": "How does FastAPI validate request data?",
        "answerable": answerable,
        "relevant_source_paths": ["tutorial/body.md"] if answerable else [],
        "slice": "general",
        "provenance": "real",
        "license": "CC BY-SA 4.0",
    }
    return (
        f"### Candidate {source_id}\n\n"
        f"- [{'x' if confirmed else ' '}] Confirmed\n\n"
        "```json\n"
        f"{json.dumps(label)}\n"
        "```\n"
    )


def test_builder_ignores_unconfirmed_rows_and_exports_confirmed_labels(tmp_path) -> None:
    batch = tmp_path / "batch-01.md"
    batch.write_text(_candidate("123", False, True) + _candidate("124", True, True))

    answerable, unanswerable = confirmed_records([batch])

    assert [row["id"] for row in answerable] == ["real-so-124"]
    assert answerable[0]["label_status"] == "confirmed"
    assert answerable[0]["source_url"] == "https://stackoverflow.com/q/124"
    assert unanswerable == []


def test_builder_emits_unanswerable_reason_and_requires_label(tmp_path) -> None:
    batch = tmp_path / "batch-01.md"
    batch.write_text(_candidate("125", True, False))

    answerable, unanswerable = confirmed_records([batch])

    assert answerable == []
    assert unanswerable[0]["reason"] == "not covered by pinned docs"


def test_builder_rejects_confirmed_candidate_with_no_label_json(tmp_path) -> None:
    batch = tmp_path / "batch-01.md"
    batch.write_text("### Candidate 1\n- [x] Confirmed\n")

    with pytest.raises(ValueError, match="no JSON label block"):
        confirmed_records([batch])


def test_prepared_batch_has_25_parseable_candidate_labels() -> None:
    batch = Path(__file__).resolve().parent / "labeling" / "batch-01.md"
    content = batch.read_text(encoding="utf-8")
    sections = re.findall(r"(?ms)^### Candidate\b.*?(?=^### Candidate\b|\Z)", content)

    assert len(sections) == 25
    for section in sections:
        blocks = re.findall(r"```json\s*(.*?)\s*```", section, flags=re.DOTALL)
        assert len(blocks) == 1
        label = json.loads(blocks[0])
        assert {"source_id", "source_url", "query", "answerable"} <= label.keys()


def test_dataset_validator_checks_paths_pii_and_overlap(tmp_path) -> None:
    report = tmp_path / "report.json"
    report.write_text(json.dumps({"files": [{"source_path": "tutorial/body.md"}]}))
    synthetic = tmp_path / "synthetic.jsonl"
    synthetic.write_text('{"id":"synthetic-1"}\n')
    answerable = tmp_path / "answerable.jsonl"
    unanswerable = tmp_path / "unanswerable.jsonl"
    unanswerable.write_text("")
    row = {
        "id": "real-so-123",
        "query": "How does FastAPI validate request data?",
        "relevant_source_paths": ["tutorial/body.md"],
        "persona": "guest",
        "slice": "general",
        "provenance": "real",
        "source_url": "https://stackoverflow.com/q/123",
        "license": "CC BY-SA 4.0",
        "label_status": "confirmed",
        "notes": "paraphrased; attribution: https://stackoverflow.com/q/123",
    }
    answerable.write_text(json.dumps(row) + "\n")

    assert validate_datasets(answerable, unanswerable, report, synthetic) == {
        "answerable": 1,
        "unanswerable": 0,
    }

    row["query"] = "Call me at +1 (415) 555-2671"
    answerable.write_text(json.dumps(row) + "\n")
    with pytest.raises(ValueError, match="PII"):
        validate_datasets(answerable, unanswerable, report, synthetic)


def test_dataset_validator_rejects_unknown_paths_and_duplicate_ids(tmp_path) -> None:
    report = tmp_path / "report.json"
    report.write_text(json.dumps({"files": [{"source_path": "tutorial/body.md"}]}))
    synthetic = tmp_path / "synthetic.jsonl"
    synthetic.write_text('{"id":"same-id"}\n')
    answerable = tmp_path / "answerable.jsonl"
    unanswerable = tmp_path / "unanswerable.jsonl"
    unanswerable.write_text("")
    row = {
        "id": "same-id",
        "query": "A valid question about FastAPI?",
        "relevant_source_paths": ["not-in-pinned-corpus.md"],
        "persona": "guest",
        "slice": "general",
        "provenance": "real",
        "source_url": "https://stackoverflow.com/q/123",
        "license": "CC BY-SA 4.0",
        "label_status": "confirmed",
        "notes": "paraphrased",
    }
    answerable.write_text(json.dumps(row) + "\n")

    with pytest.raises(ValueError, match="duplicate/overlapping id"):
        validate_datasets(answerable, unanswerable, report, synthetic)

    row["id"] = "real-so-999"
    answerable.write_text(json.dumps(row) + "\n")
    with pytest.raises(ValueError, match="unknown pinned source paths"):
        validate_datasets(answerable, unanswerable, report, synthetic)
