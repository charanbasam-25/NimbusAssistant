"""Build real eval JSONL only from owner-confirmed Markdown review rows.

Each batch candidate contains a JSON label block. The owner must edit that
block and tick ``- [x] Confirmed`` before the row is eligible for export.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JSON_BLOCK = re.compile(r"```json\s*\n(?P<json>.*?)\n```", re.DOTALL)
SECTION = re.compile(
    r"(?m)^### Candidate (?P<number>\d+)\b(?P<body>.*?)(?=^### Candidate |\Z)", re.DOTALL
)


def confirmed_records(batch_paths: list[Path]) -> tuple[list[dict], list[dict]]:
    """Parse confirmed rows; unconfirmed candidate suggestions are ignored."""
    answerable: list[dict] = []
    unanswerable: list[dict] = []
    seen_ids: set[str] = set()
    for path in batch_paths:
        text = path.read_text(encoding="utf-8")
        for section in SECTION.finditer(text):
            body = section.group("body")
            if not re.search(r"(?m)^- \[x\] Confirmed\s*$", body, re.IGNORECASE):
                continue
            match = JSON_BLOCK.search(body)
            if not match:
                raise ValueError(
                    f"{path}: candidate {section.group('number')} has no JSON label block"
                )
            label = json.loads(match.group("json"))
            source_id = str(label.get("source_id", "")).strip()
            source_url = str(label.get("source_url", "")).strip()
            query = str(label.get("query", "")).strip()
            if not source_id or not source_url or not query:
                raise ValueError(
                    f"{path}: confirmed candidate needs source_id, source_url and query"
                )
            if source_id in seen_ids:
                raise ValueError(f"{path}: duplicate confirmed source_id {source_id!r}")
            seen_ids.add(source_id)
            common = {
                "id": f"real-so-{source_id}",
                "query": query,
                "persona": "guest",
                "slice": label.get("slice", "general"),
                "provenance": label.get("provenance", "real"),
                "source_url": source_url,
                "license": label.get("license", "CC BY-SA 4.0"),
                "label_status": "confirmed",
                "notes": label.get("notes", f"paraphrased; attribution: {source_url}"),
            }
            if label.get("answerable") is True:
                common["relevant_source_paths"] = label.get("relevant_source_paths", [])
                answerable.append(common)
            elif label.get("answerable") is False:
                common["reason"] = "not covered by pinned docs"
                unanswerable.append(common)
            else:
                raise ValueError(f"{path}: confirmed candidate needs answerable: true or false")
    return answerable, unanswerable


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in records),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("batches", nargs="+", type=Path)
    parser.add_argument(
        "--answerable", type=Path, default=ROOT / "evals/datasets/retrieval_real.jsonl"
    )
    parser.add_argument(
        "--unanswerable", type=Path, default=ROOT / "evals/datasets/unanswerable_real.jsonl"
    )
    args = parser.parse_args()
    answerable, unanswerable = confirmed_records(args.batches)
    write_jsonl(args.answerable, answerable)
    write_jsonl(args.unanswerable, unanswerable)
    print(
        f"Wrote {len(answerable)} answerable and {len(unanswerable)} unanswerable confirmed labels."
    )


if __name__ == "__main__":
    main()
