import json
import shutil
from collections import Counter, defaultdict
from pathlib import Path

import pytest
from ingest_corpus import split_front_matter, validate_synthetic_manifest

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "data" / "synthetic"
MANIFEST = CORPUS / "manifest.json"


def _single_document_fixture(tmp_path: Path) -> tuple[Path, dict]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    entry = next(
        document
        for document in manifest["documents"]
        if document["id"] == "deployment-rollback-global"
    )
    relative = Path(entry["source_path"])
    (tmp_path / relative.parent).mkdir(parents=True)
    shutil.copyfile(CORPUS / relative, tmp_path / relative)
    manifest["documents"] = [entry]
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path, entry


def test_synthetic_manifest_has_38_documents_and_17_questions() -> None:
    manifest, documents = validate_synthetic_manifest(MANIFEST)

    assert manifest["corpus_id"] == "nimbus-cloud-synthetic"
    assert len(documents) == 38
    assert len({item.entry["question"] for item in documents if item.entry["question"]}) == 17
    counts = Counter(item.entry["kind"] for item in documents)
    assert counts == {"policy": 14, "runbook": 13, "poisoned": 5, "pii": 5, "glossary": 1}


def test_every_pair_shares_one_question_and_body_except_canary_fact() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    pairs: dict[str, list[dict]] = defaultdict(list)
    for entry in manifest["documents"]:
        if entry["pair"] is not None:
            pairs[entry["pair"]].append(entry)
    assert len(pairs) == 10

    for pair_entries in pairs.values():
        assert len({entry["question"] for entry in pair_entries}) == 1
        bodies = []
        for entry in pair_entries:
            metadata, body = split_front_matter((CORPUS / entry["source_path"]).read_text())
            assert metadata["canary_facts"] == entry["expected_canary_facts"]
            bodies.append(
                body.replace(
                    next(line for line in body.splitlines() if line.startswith("Canary fact:")),
                    "Canary fact: [REGIONAL VALUE].",
                )
            )
        assert bodies[0] == bodies[1]


def test_every_synthetic_document_has_the_required_body_length() -> None:
    _, documents = validate_synthetic_manifest(MANIFEST)
    for document in documents:
        words = document.body.split()
        assert 120 <= len(words) <= 300, document.entry["source_path"]


def test_synthetic_validation_rejects_front_matter_tag_mismatch(tmp_path) -> None:
    manifest_path, _ = _single_document_fixture(tmp_path)
    data = json.loads(manifest_path.read_text())
    data["documents"][0]["region"] = "R1"
    manifest_path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ValueError, match="front-matter region"):
        validate_synthetic_manifest(manifest_path)


def test_synthetic_validation_rejects_invalid_region(tmp_path) -> None:
    manifest_path, _ = _single_document_fixture(tmp_path)
    data = json.loads(manifest_path.read_text())
    data["documents"][0]["region"] = "R3"
    manifest_path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ValueError, match="invalid region"):
        validate_synthetic_manifest(manifest_path)


def test_synthetic_validation_rejects_missing_file(tmp_path) -> None:
    manifest_path, _ = _single_document_fixture(tmp_path)
    data = json.loads(manifest_path.read_text())
    data["documents"][0]["source_path"] = "internal/missing.md"
    manifest_path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ValueError, match="source file does not exist"):
        validate_synthetic_manifest(manifest_path)
