"""Validate owner-labeled real retrieval datasets against the pinned corpus."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from nimbus_api.pii import contains_pii

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "data" / "processed" / "corpus-ingestion-report.json"
SYNTHETIC_DATASET = ROOT / "evals" / "datasets" / "retrieval.jsonl"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        item = json.loads(line)
        if not isinstance(item, dict):
            raise TypeError(f"{path}:{line_number}: expected an object")
        records.append(item)
    return records


def validate_datasets(
    answerable_path: Path,
    unanswerable_path: Path,
    report_path: Path = REPORT_PATH,
    synthetic_path: Path = SYNTHETIC_DATASET,
) -> dict[str, int]:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    source_paths = {entry["source_path"] for entry in report["files"]}
    answerable = read_jsonl(answerable_path)
    unanswerable = read_jsonl(unanswerable_path)
    synthetic_ids = {item["id"] for item in read_jsonl(synthetic_path)}
    seen: set[str] = set()

    def validate_common(item: dict[str, Any], row_number: int, is_answerable: bool) -> None:
        required = {
            "id",
            "query",
            "persona",
            "slice",
            "provenance",
            "source_url",
            "license",
            "label_status",
            "notes",
        }
        if is_answerable:
            required.add("relevant_source_paths")
        else:
            required.add("reason")
        missing = required - item.keys()
        if missing:
            raise ValueError(f"row {row_number}: missing fields {sorted(missing)}")
        for field in ("id", "query", "source_url", "license", "notes"):
            if not isinstance(item[field], str) or not item[field].strip():
                raise ValueError(f"row {row_number}: {field} must be a non-empty string")
        if item["persona"] not in {"guest", "R1", "R2"}:
            raise ValueError(f"row {row_number}: invalid persona")
        if not item["source_url"].startswith(("https://", "http://")):
            raise ValueError(f"row {row_number}: source_url must be HTTP(S)")
        if item["provenance"] == "real" and item["label_status"] != "confirmed":
            raise ValueError(f"row {row_number}: real provenance requires confirmed label_status")
        if item["provenance"] not in {"real", "synthetic"}:
            raise ValueError(f"row {row_number}: invalid provenance")
        if len(item["query"]) > 300:
            raise ValueError(f"row {row_number}: query exceeds 300 characters")
        if contains_pii(item["query"]):
            raise ValueError(f"row {row_number}: query contains PII")
        if item["slice"] not in {"general", "short_query"}:
            raise ValueError(f"row {row_number}: invalid slice")
        if item["id"] in seen or item["id"] in synthetic_ids:
            raise ValueError(f"row {row_number}: duplicate/overlapping id {item['id']!r}")
        seen.add(item["id"])
        if is_answerable:
            paths = item["relevant_source_paths"]
            if not isinstance(paths, list) or not paths:
                raise ValueError(f"row {row_number}: answerable labels need relevant source paths")
            missing_paths = set(paths) - source_paths
            if missing_paths:
                raise ValueError(
                    f"row {row_number}: unknown pinned source paths {sorted(missing_paths)}"
                )
        elif item["reason"] != "not covered by pinned docs":
            raise ValueError(f"row {row_number}: unexpected unanswerable reason")

    for index, item in enumerate(answerable, 1):
        validate_common(item, index, True)
    for index, item in enumerate(unanswerable, len(answerable) + 1):
        validate_common(item, index, False)
    return {"answerable": len(answerable), "unanswerable": len(unanswerable)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--answerable", type=Path, default=ROOT / "evals/datasets/retrieval_real.jsonl"
    )
    parser.add_argument(
        "--unanswerable", type=Path, default=ROOT / "evals/datasets/unanswerable_real.jsonl"
    )
    args = parser.parse_args()
    counts = validate_datasets(args.answerable, args.unanswerable)
    print(
        f"Validated {counts['answerable']} answerable and {counts['unanswerable']} unanswerable records."
    )


if __name__ == "__main__":
    main()
