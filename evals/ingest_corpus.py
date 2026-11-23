"""Fetch the pinned FastAPI docs snapshot and load Markdown chunks into Postgres."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import psycopg
import yaml
from nimbus_api.config import database_url
from nimbus_api.guardrails import GUARDRAILS_VERSION, should_flag_chunk
from nimbus_api.pii import PII_VERSION, mask_pii
from psycopg.types.json import Jsonb

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "docs" / "corpus-manifest.json"
SYNTHETIC_COMMIT = "nimbus-cloud-v1"
SYNTHETIC_ENDING = "Synthetic document for Nimbus capstone testing. Not real policy."
TOKEN_PATTERN = re.compile(r"\w+|[^\w\s]", re.UNICODE)
MAX_CHUNK_LEXICAL_TOKENS = 600
CHUNK_OVERLAP_TOKENS = 80
PARSER_VERSION = "markdown-includes-fences-v3"
CHUNKER_VERSION = "heading-paragraph-lexical-600-fence-repair-v3"
FENCE_PATTERN = re.compile(r"(`{3,}|~{3,})")
INCLUDE_PATTERN = re.compile(r"(?m)^[ \t]*\{\*[ \t]*(?P<body>[^\r\n]*?)[ \t]*\*\}[ \t]*$")
INCLUDE_OPTION_PATTERN = re.compile(
    r'\s*(?:hl\[[0-9,: \-]+\]|ln\[[0-9,: \-]+\]|title\["[^"\r\n]*"\])'
)


@dataclass(frozen=True)
class SyntheticDocument:
    entry: dict[str, Any]
    body: str
    content_hash: str


def split_front_matter(markdown: str, source: str = "<document>") -> tuple[dict, str]:
    """Parse a YAML front-matter mapping and return only the answer-bearing body."""
    lines = markdown.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"{source}: expected YAML front matter at the start of the file")
    try:
        closing = next(index for index in range(1, len(lines)) if lines[index].strip() == "---")
    except StopIteration as error:
        raise ValueError(f"{source}: missing closing front-matter delimiter") from error
    metadata = yaml.safe_load("\n".join(lines[1:closing]))
    if not isinstance(metadata, dict):
        raise TypeError(f"{source}: front matter must be a YAML mapping")
    return metadata, "\n".join(lines[closing + 1 :]).strip()


def validate_synthetic_manifest(manifest_path: Path) -> tuple[dict, list[SyntheticDocument]]:
    """Validate the full manifest and source files before making database changes."""
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise TypeError(f"{manifest_path}: manifest must be a JSON object")
    if manifest.get("schema_version") != 1 or not isinstance(manifest.get("corpus_id"), str):
        raise ValueError(f"{manifest_path}: unsupported or missing schema_version/corpus_id")
    entries = manifest.get("documents")
    if not isinstance(entries, list) or not entries:
        raise ValueError(f"{manifest_path}: documents must be a non-empty array")

    required = {
        "id",
        "source_path",
        "title",
        "audience",
        "region",
        "kind",
        "pair",
        "question",
        "expected_canary_facts",
    }
    frontmatter_fields = {
        "id",
        "title",
        "audience",
        "region",
        "kind",
        "pair",
        "canary_facts",
    }
    ids: set[str] = set()
    source_paths: set[str] = set()
    validated: list[SyntheticDocument] = []
    pairs: dict[str, list[dict[str, Any]]] = {}
    root = manifest_path.resolve().parent

    for index, entry in enumerate(entries):
        prefix = f"{manifest_path}: documents[{index}]"
        if not isinstance(entry, dict):
            raise TypeError(f"{prefix} must be an object")
        missing = required - entry.keys()
        if missing:
            raise ValueError(f"{prefix} is missing fields: {sorted(missing)}")
        for key in ("id", "source_path", "title"):
            if not isinstance(entry[key], str) or not entry[key].strip():
                raise ValueError(f"{prefix}.{key} must be a non-empty string")
        if entry["id"] in ids:
            raise ValueError(f"{prefix}: duplicate id {entry['id']!r}")
        if entry["source_path"] in source_paths:
            raise ValueError(f"{prefix}: duplicate source_path {entry['source_path']!r}")
        ids.add(entry["id"])
        source_paths.add(entry["source_path"])
        if entry["audience"] not in {"public", "internal"}:
            raise ValueError(f"{prefix}: invalid audience {entry['audience']!r}")
        if entry["region"] not in {"global", "R1", "R2"}:
            raise ValueError(f"{prefix}: invalid region {entry['region']!r}")
        if entry["kind"] not in {"policy", "runbook", "poisoned", "pii", "glossary"}:
            raise ValueError(f"{prefix}: invalid kind {entry['kind']!r}")
        if entry["pair"] is not None and (
            not isinstance(entry["pair"], str) or not entry["pair"].strip()
        ):
            raise ValueError(f"{prefix}.pair must be null or a non-empty string")
        question = entry["question"]
        if entry["kind"] in {"policy", "runbook"}:
            if not isinstance(question, str) or not question.strip():
                raise ValueError(f"{prefix}: policy/runbook entries need a question")
        elif question is not None:
            raise ValueError(f"{prefix}: only policy/runbook entries may have questions")
        if not isinstance(entry["expected_canary_facts"], dict):
            raise TypeError(f"{prefix}.expected_canary_facts must be an object")

        relative = Path(entry["source_path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"{prefix}: source_path must stay inside the synthetic corpus")
        path = (root / relative).resolve()
        if not path.is_relative_to(root):
            raise ValueError(f"{prefix}: source_path escapes the synthetic corpus")
        if not path.is_file():
            raise ValueError(f"{prefix}: source file does not exist: {entry['source_path']}")
        raw = path.read_text(encoding="utf-8")
        front_matter, body = split_front_matter(raw, str(path))
        if not frontmatter_fields.issubset(front_matter):
            missing_frontmatter = frontmatter_fields - front_matter.keys()
            raise ValueError(f"{path}: missing front-matter fields {sorted(missing_frontmatter)}")
        expected_front_matter = {
            "id": entry["id"],
            "title": entry["title"],
            "audience": entry["audience"],
            "region": entry["region"],
            "kind": entry["kind"],
            "pair": entry["pair"],
            "canary_facts": entry["expected_canary_facts"],
        }
        for key, expected in expected_front_matter.items():
            if front_matter.get(key) != expected:
                raise ValueError(
                    f"{path}: front-matter {key}={front_matter.get(key)!r} "
                    f"does not match manifest value {expected!r}"
                )
        if not body.endswith(SYNTHETIC_ENDING):
            raise ValueError(f"{path}: body must end with the synthetic-document disclaimer")
        word_count = len(re.findall(r"\b[\w'-]+\b", body))
        if not 120 <= word_count <= 300:
            raise ValueError(f"{path}: body must contain 120-300 words (found {word_count})")
        validated.append(
            SyntheticDocument(
                entry=entry,
                body=body,
                content_hash=hashlib.sha256(raw.encode("utf-8")).hexdigest(),
            )
        )
        if entry["pair"] is not None:
            pairs.setdefault(entry["pair"], []).append(entry)

    for pair_id, pair_entries in pairs.items():
        if (
            len(pair_entries) != 2
            or {entry["region"] for entry in pair_entries} != {"R1", "R2"}
            or len({entry["question"] for entry in pair_entries}) != 1
        ):
            raise ValueError(
                f"{manifest_path}: pair {pair_id!r} must have R1/R2 entries sharing a question"
            )
    return manifest, validated


def ingest_synthetic(manifest_path: Path) -> dict[str, Any]:
    manifest, documents = validate_synthetic_manifest(manifest_path)
    loaded_chunks = 0
    flagged_chunks = 0
    pii_masked: dict[str, int] = {}

    with psycopg.connect(database_url()) as connection, connection.transaction():
        for document in documents:
            entry = document.entry
            title_result = mask_pii(entry["title"])
            body_result = mask_pii(document.body)
            for result in (title_result, body_result):
                for category, count in result.counts.items():
                    pii_masked[category] = pii_masked.get(category, 0) + count
            title = title_result.text
            chunks = make_chunks(body_result.text)
            connection.execute(
                """
                DELETE FROM documents
                WHERE source_commit = %s AND source_path = %s AND content_hash <> %s
                """,
                (SYNTHETIC_COMMIT, entry["source_path"], document.content_hash),
            )
            document_id = connection.execute(
                """
                INSERT INTO documents (
                    source_url, source_commit, source_path, title, audience, region,
                    content_hash, metadata
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (source_commit, source_path, content_hash)
                DO UPDATE SET title = EXCLUDED.title, metadata = EXCLUDED.metadata
                RETURNING id
                """,
                (
                    f"synthetic://nimbus-cloud/{entry['id']}",
                    SYNTHETIC_COMMIT,
                    entry["source_path"],
                    title,
                    entry["audience"],
                    entry["region"],
                    document.content_hash,
                    Jsonb(
                        {
                            "source": "synthetic",
                            "kind": entry["kind"],
                            "pair": entry["pair"],
                            "id": entry["id"],
                        }
                    ),
                ),
            ).fetchone()[0]
            connection.execute("DELETE FROM chunks WHERE document_id = %s", (document_id,))
            for ordinal, chunk in enumerate(chunks):
                content = str(chunk["content"])
                flagged = should_flag_chunk(content)
                flagged_chunks += int(flagged)
                embedding_input = f"{title}: {content}"
                content_hash = "sha256:" + hashlib.sha256(content.encode("utf-8")).hexdigest()
                processing = Jsonb(
                    {
                        "parser_version": PARSER_VERSION,
                        "chunker_version": CHUNKER_VERSION,
                        "pii_masker": PII_VERSION,
                        "injection_detector": GUARDRAILS_VERSION,
                    }
                )
                connection.execute(
                    """
                    INSERT INTO chunks (
                        document_id, ordinal, heading, content, token_count,
                        embedding_input, content_hash, processing, flagged
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (document_id, ordinal)
                    DO UPDATE SET heading = EXCLUDED.heading,
                                  content = EXCLUDED.content,
                                  token_count = EXCLUDED.token_count,
                                  embedding_input = EXCLUDED.embedding_input,
                                  content_hash = EXCLUDED.content_hash,
                                  processing = EXCLUDED.processing,
                                  flagged = EXCLUDED.flagged
                    """,
                    (
                        document_id,
                        ordinal,
                        None,
                        content,
                        chunk["token_count"],
                        embedding_input,
                        content_hash,
                        processing,
                        flagged,
                    ),
                )
            loaded_chunks += len(chunks)

    return {
        "corpus_id": manifest["corpus_id"],
        "source_commit": SYNTHETIC_COMMIT,
        "documents_loaded": len(documents),
        "chunks_loaded": loaded_chunks,
        "flagged_chunks": flagged_chunks,
        "pii_masked": pii_masked,
    }


def checkout_pinned_source(repository: str, commit: str, destination: Path) -> Path:
    if destination.exists() and not (destination / ".git").exists():
        raise RuntimeError(
            f"{destination} exists but is not a Git checkout; move it aside or choose another path"
        )
    if not destination.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["git", "init", str(destination)], check=True, capture_output=True, text=True
        )
        subprocess.run(
            ["git", "-C", str(destination), "remote", "add", "origin", repository],
            check=True,
            capture_output=True,
            text=True,
        )

    subprocess.run(
        ["git", "-C", str(destination), "fetch", "--depth", "1", "origin", commit],
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "-C", str(destination), "checkout", "--force", "--detach", commit],
        check=True,
        capture_output=True,
        text=True,
    )
    actual_commit = subprocess.run(
        ["git", "-C", str(destination), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if actual_commit != commit:
        raise RuntimeError(f"Expected source commit {commit}, got {actual_commit}")
    return destination


def markdown_title(markdown: str, fallback: str) -> str:
    for line in markdown.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def expand_code_includes(markdown: str, docs_base: Path, source_root: Path) -> str:
    """Replace FastAPI's code include directives with safe, labeled code blocks.

    FastAPI's include paths are relative to ``docs/en``. The pinned corpus uses
    examples under ``docs_src/`` and one reference under ``fastapi/``. Resolve
    only inside those approved checkout roots, and reject unsupported options
    rather than silently dropping directive information.
    """
    allowed_roots = tuple(
        (source_root / directory).resolve() for directory in ("docs_src", "fastapi")
    )

    def replace(match: re.Match[str]) -> str:
        body = match.group("body").strip()
        path_match = re.match(r"(?P<path>\S+)(?P<options>.*)\Z", body)
        if not path_match:
            raise RuntimeError("Found an empty code include directive")

        relative_path = path_match.group("path")
        options = path_match.group("options").strip()
        while options:
            option_match = INCLUDE_OPTION_PATTERN.match(options)
            if not option_match:
                raise RuntimeError(f"Unsupported options in code include directive: {body}")
            options = options[option_match.end() :].strip()

        candidate = (docs_base / relative_path).resolve()
        if not any(candidate.is_relative_to(allowed_root) for allowed_root in allowed_roots):
            raise RuntimeError(
                f"Code include must resolve inside an approved source directory: {relative_path}"
            )
        if not candidate.is_file():
            raise RuntimeError(f"Code include file does not exist: {relative_path}")

        code = candidate.read_text(encoding="utf-8").rstrip("\n")
        # Use a longer Markdown fence if source code itself contains backticks.
        longest_fence = max((len(run) for run in re.findall(r"`+", code)), default=0)
        fence = "`" * max(3, longest_fence + 1)
        language = candidate.suffix.removeprefix(".")
        source_label = candidate.relative_to(source_root.resolve()).as_posix()
        return f"[Example source: {source_label}]\n{fence}{language}\n{code}\n{fence}"

    return INCLUDE_PATTERN.sub(replace, markdown)


def markdown_sections(markdown: str) -> list[tuple[str, str]]:
    """Return heading-tagged paragraphs, excluding front matter and heading syntax."""
    lines = markdown.splitlines()
    if lines and lines[0].strip() == "---":
        try:
            closing = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
            lines = lines[closing + 1 :]
        except StopIteration:
            pass

    sections: list[tuple[str, str]] = []
    heading = ""
    paragraph: list[str] = []
    open_fence: tuple[str, int] | None = None

    def flush_paragraph() -> None:
        text = "\n".join(paragraph).strip()
        if text:
            sections.append((heading, text))
        paragraph.clear()

    for line in lines:
        if open_fence is not None:
            # Inside a code block, Markdown-looking headings and blank lines
            # are literal source and must stay together in this section.
            paragraph.append(line.rstrip())
            bare_fence = re.fullmatch(r"[ \t]*(`{3,}|~{3,})[ \t]*", line)
            if bare_fence:
                delimiter = bare_fence.group(1)
                if delimiter[0] == open_fence[0] and len(delimiter) >= open_fence[1]:
                    open_fence = None
            continue

        # A fence can have an info string (for example ```python), but must
        # start the line; ordinary inline backticks are not block delimiters.
        indent = len(line) - len(line.lstrip(" "))
        opening = FENCE_PATTERN.match(line.lstrip(" ")) if indent <= 3 else None
        if opening:
            delimiter = opening.group(1)
            open_fence = (delimiter[0], len(delimiter))
            paragraph.append(line.rstrip())
            continue

        if re.match(r"^#{1,6}\s+", line):
            flush_paragraph()
            heading = re.sub(r"^#{1,6}\s+", "", line).strip()
        elif line.strip():
            paragraph.append(line.rstrip())
        else:
            flush_paragraph()
    flush_paragraph()
    return sections


def _fence_state_at(text: str, position: int) -> tuple[str, int, str, str | None] | None:
    """Return the active Markdown fence immediately before a character offset.

    The saved opening line lets a continuation chunk reopen the same language
    fence rather than leaving the code fragment looking like ordinary prose.
    """
    open_fence: tuple[str, int, str, str | None] | None = None
    offset = 0
    previous_line = ""
    for line in text.splitlines(keepends=True):
        content = line.rstrip("\r\n")
        # A boundary inside a line has not reached that line's delimiter yet.
        if offset + len(content) > position:
            break

        if open_fence is None:
            indent = len(content) - len(content.lstrip(" "))
            opening = FENCE_PATTERN.match(content.lstrip(" ")) if indent <= 3 else None
            if opening:
                delimiter = opening.group(1)
                label = previous_line.strip()
                if not re.fullmatch(r"\[Example source: [^\]\r\n]+\]", label):
                    label = None
                open_fence = (delimiter[0], len(delimiter), content, label)
        else:
            bare_fence = re.fullmatch(r"[ \t]*(`{3,}|~{3,})[ \t]*", content)
            if bare_fence:
                delimiter = bare_fence.group(1)
                if delimiter[0] == open_fence[0] and len(delimiter) >= open_fence[1]:
                    open_fence = None

        offset += len(line)
        previous_line = content
    return open_fence


def _repair_fence_boundaries(text: str, start: int, end: int) -> str:
    """Make a substring independently renderable if it starts/ends in code."""
    opening = _fence_state_at(text, start)
    closing = _fence_state_at(text, end)
    prefix = ""
    if opening:
        if opening[3]:
            prefix += f"{opening[3]}\n"
        prefix += f"{opening[2]}\n"
    suffix = f"\n{closing[0] * closing[1]}" if closing else ""
    return prefix + text[start:end] + suffix


def split_long_text(text: str, max_tokens: int) -> list[str]:
    """Split only oversized paragraphs, enforcing a hard lexical-token cap.

    Prefer line boundaries (useful for Markdown tables and code) when they are
    reasonably close to the cap. Fall back to exact token boundaries for a
    single very long line. Overlap is measured in the same lexical tokens as
    the cap, rather than whitespace-separated words.
    """
    matches = list(TOKEN_PATTERN.finditer(text))
    if len(matches) <= max_tokens:
        return [text]

    overlap = min(CHUNK_OVERLAP_TOKENS, max_tokens - 1)
    if max_tokens <= CHUNK_OVERLAP_TOKENS:
        # A nearly-full-window overlap would advance only one token at a time.
        overlap = max_tokens // 5
    chunks: list[str] = []
    start = 0
    while start < len(matches):
        end = min(start + max_tokens, len(matches))

        if end < len(matches):
            # A line break between tokens marks a useful Markdown row/code-line
            # boundary. Avoid tiny chunks by considering boundaries only in the
            # latter half of this window.
            min_end = start + max(1, (end - start) // 2)
            line_ends = [
                index
                for index in range(min_end, end)
                if "\n" in text[matches[index - 1].end() : matches[index].start()]
            ]
            if line_ends:
                end = line_ends[-1]

        chunk_start = matches[start].start()
        # Re-open/close code fences added for chunk isolation consume tokens
        # too, so shorten this window until the repaired chunk still honors
        # the same hard lexical-token cap.
        while True:
            chunk_end = matches[end - 1].end()
            chunk = _repair_fence_boundaries(text, chunk_start, chunk_end)
            if len(TOKEN_PATTERN.findall(chunk)) <= max_tokens:
                break
            if end - start <= 1:
                raise ValueError("max_tokens is too small to preserve a Markdown fence")
            end -= 1
        chunks.append(chunk)
        if end == len(matches):
            break

        next_start = max(start + 1, end - overlap)
        # If possible, start the overlap at a line boundary so table rows and
        # code lines are not needlessly cut at the beginning of a chunk.
        line_starts = [
            index
            for index in range(start + 1, next_start + 1)
            if "\n" in text[matches[index - 1].end() : matches[index].start()]
        ]
        if line_starts:
            next_start = line_starts[-1]
        start = next_start

    return chunks


def make_chunks(markdown: str) -> list[dict[str, str | int | None]]:
    chunks: list[dict[str, str | int | None]] = []
    current_heading: str | None = None
    current_parts: list[str] = []
    current_tokens = 0

    def flush() -> None:
        nonlocal current_parts, current_tokens
        if current_parts:
            body = "\n\n".join(current_parts).strip()
            chunks.append(
                {
                    "heading": current_heading,
                    "content": body,
                    "token_count": max(1, len(TOKEN_PATTERN.findall(body))),
                }
            )
        current_parts = []
        current_tokens = 0

    for heading, paragraph in markdown_sections(markdown):
        if heading != current_heading:
            flush()
            current_heading = heading or None
        for part in split_long_text(paragraph, MAX_CHUNK_LEXICAL_TOKENS):
            part_tokens = len(TOKEN_PATTERN.findall(part))
            if current_parts and current_tokens + part_tokens > MAX_CHUNK_LEXICAL_TOKENS:
                flush()
            current_parts.append(part)
            current_tokens += part_tokens
    flush()
    return chunks


def source_page_url(relative_path: Path) -> str:
    page = relative_path.with_suffix("")
    if page.name == "index":
        page = page.parent
    suffix = "/".join(page.parts)
    return f"https://fastapi.tiangolo.com/{suffix + '/' if suffix else ''}"


def ingest(source_root: Path, manifest: dict) -> dict:
    commit = manifest["source_commit"]
    docs_dir = source_root / manifest["documentation_root"]
    if not docs_dir.is_dir():
        raise RuntimeError(f"Documentation directory not found: {docs_dir}")

    files = sorted(docs_dir.rglob("*.md"))
    if not files:
        raise RuntimeError(f"No Markdown files found under {docs_dir}")
    excluded_paths = set(manifest.get("excluded_paths", []))
    selected_files = [
        path for path in files if path.relative_to(docs_dir).as_posix() not in excluded_paths
    ]
    if not selected_files:
        raise RuntimeError(f"No approved Markdown files found under {docs_dir}")

    loaded_documents = 0
    loaded_chunks = 0
    flagged_chunks = 0
    pii_masked: dict[str, int] = {}
    file_records = []
    with psycopg.connect(database_url()) as connection, connection.transaction():
        # Remove only explicitly excluded pages from this exact pinned snapshot.
        for excluded_path in excluded_paths:
            connection.execute(
                "DELETE FROM documents WHERE source_commit = %s AND source_path = %s",
                (commit, excluded_path),
            )

        for path in selected_files:
            source_markdown = path.read_text(encoding="utf-8")
            content_hash = hashlib.sha256(source_markdown.encode("utf-8")).hexdigest()
            relative_path = path.relative_to(docs_dir)
            source_path = relative_path.as_posix()
            markdown = expand_code_includes(
                source_markdown,
                docs_base=docs_dir.parent,
                source_root=source_root,
            )
            # Mask the complete expanded page before splitting so no sensitive
            # token can be divided across overlapping chunks.
            masked = mask_pii(markdown)
            markdown = masked.text
            for category, count in masked.counts.items():
                pii_masked[category] = pii_masked.get(category, 0) + count
            title = markdown_title(markdown, path.stem.replace("-", " ").title())
            title_masked = mask_pii(title)
            title = title_masked.text
            for category, count in title_masked.counts.items():
                pii_masked[category] = pii_masked.get(category, 0) + count
            chunks = make_chunks(markdown)
            if not chunks:
                continue

            # The exact pinned path is the replacement boundary, making reruns idempotent.
            connection.execute(
                """
                    DELETE FROM documents
                    WHERE source_commit = %s AND source_path = %s AND content_hash <> %s
                    """,
                (commit, source_path, content_hash),
            )
            document_id = connection.execute(
                """
                    INSERT INTO documents (
                        source_url, source_commit, source_path, title, audience, region,
                        content_hash, metadata
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (source_commit, source_path, content_hash)
                    DO UPDATE SET title = EXCLUDED.title, metadata = EXCLUDED.metadata
                    RETURNING id
                    """,
                (
                    source_page_url(relative_path),
                    commit,
                    source_path,
                    title,
                    manifest["default_access_tags"]["audience"],
                    manifest["default_access_tags"]["region"],
                    content_hash,
                    Jsonb({"license": manifest["license"], "format": "markdown"}),
                ),
            ).fetchone()[0]

            # Chunk boundaries may change when the chunker version changes.
            # Remove prior rows first so stale higher ordinals cannot survive
            # a re-ingestion with fewer chunks.
            connection.execute("DELETE FROM chunks WHERE document_id = %s", (document_id,))

            for ordinal, chunk in enumerate(chunks):
                # Keep original text for keyword search, but give future embeddings
                # its title/heading context so a passage still makes sense by itself.
                context_parts = [title]
                if chunk["heading"]:
                    context_parts.append(str(chunk["heading"]))
                embedding_input = " / ".join(context_parts) + ": " + str(chunk["content"])
                chunk_hash = (
                    "sha256:" + hashlib.sha256(str(chunk["content"]).encode("utf-8")).hexdigest()
                )
                processing = Jsonb(
                    {
                        "parser_version": PARSER_VERSION,
                        "chunker_version": CHUNKER_VERSION,
                        "pii_masker": PII_VERSION,
                        "injection_detector": GUARDRAILS_VERSION,
                    }
                )
                flagged = should_flag_chunk(str(chunk["content"]))
                flagged_chunks += int(flagged)
                connection.execute(
                    """
                        INSERT INTO chunks (
                            document_id, ordinal, heading, content, token_count,
                            embedding_input, content_hash, processing, flagged
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (document_id, ordinal)
                        DO UPDATE SET heading = EXCLUDED.heading,
                                      content = EXCLUDED.content,
                                      token_count = EXCLUDED.token_count,
                                      embedding_input = EXCLUDED.embedding_input,
                                      content_hash = EXCLUDED.content_hash,
                                      processing = EXCLUDED.processing,
                                      flagged = EXCLUDED.flagged
                        """,
                    (
                        document_id,
                        ordinal,
                        chunk["heading"],
                        chunk["content"],
                        chunk["token_count"],
                        embedding_input,
                        chunk_hash,
                        processing,
                        flagged,
                    ),
                )

            loaded_documents += 1
            loaded_chunks += len(chunks)
            file_records.append(
                {
                    "source_path": source_path,
                    "content_sha256": content_hash,
                    "chunks": len(chunks),
                }
            )

    return {
        "corpus_name": manifest["corpus_name"],
        "source_repository": manifest["source_repository"],
        "source_commit": commit,
        "documentation_root": manifest["documentation_root"],
        "excluded_paths": sorted(excluded_paths),
        "documents_loaded": loaded_documents,
        "chunks_loaded": loaded_chunks,
        "flagged_chunks": flagged_chunks,
        "pii_masked": pii_masked,
        "files": file_records,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--checkout-dir",
        type=Path,
        default=ROOT / "data" / "raw" / "fastapi",
        help="where to fetch the pinned upstream repository (default: ignored data/raw/fastapi)",
    )
    parser.add_argument(
        "--source-dir",
        type=Path,
        help="use an existing checkout instead of fetching the pinned commit",
    )
    parser.add_argument(
        "--report",
        type=Path,
        help="write the ingestion report here",
    )
    parser.add_argument(
        "--synthetic",
        type=Path,
        help="ingest a validated Nimbus Cloud synthetic manifest instead of FastAPI docs",
    )
    args = parser.parse_args()
    if args.synthetic and args.source_dir:
        parser.error("--synthetic cannot be combined with --source-dir")
    if args.synthetic:
        report = ingest_synthetic(args.synthetic.resolve())
        default_report = ROOT / "data" / "processed" / "synthetic-ingestion-report.json"
    else:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        if args.source_dir:
            source_root = args.source_dir.resolve()
            actual_commit = subprocess.run(
                ["git", "-C", str(source_root), "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            if actual_commit != manifest["source_commit"]:
                raise RuntimeError(
                    f"--source-dir must be at pinned commit {manifest['source_commit']}; "
                    f"found {actual_commit}"
                )
        else:
            source_root = checkout_pinned_source(
                manifest["source_repository"], manifest["source_commit"], args.checkout_dir
            )
        report = ingest(source_root.resolve(), manifest)
        default_report = ROOT / "data" / "processed" / "corpus-ingestion-report.json"
    report_path = (args.report or default_report).resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        f"Loaded {report['documents_loaded']} documents and {report['chunks_loaded']} chunks; "
        f"flagged {report['flagged_chunks']}; PII masks: "
        f"{json.dumps(report['pii_masked'], sort_keys=True)}. Report: {report_path}"
    )


if __name__ == "__main__":
    main()
