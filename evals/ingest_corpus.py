"""Fetch the pinned FastAPI docs snapshot and load Markdown chunks into Postgres."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from urllib.parse import quote

import psycopg
from dotenv import load_dotenv
from psycopg.types.json import Jsonb


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "docs" / "corpus-manifest.json"
TOKEN_PATTERN = re.compile(r"\w+|[^\w\s]", re.UNICODE)
MAX_CHUNK_LEXICAL_TOKENS = 600
CHUNK_OVERLAP_TOKENS = 80
PARSER_VERSION = "markdown-includes-v2"
CHUNKER_VERSION = "heading-paragraph-lexical-600-v2"
INCLUDE_PATTERN = re.compile(
    r"(?m)^[ \t]*\{\*[ \t]*(?P<body>[^\r\n]*?)[ \t]*\*\}[ \t]*$"
)
INCLUDE_OPTION_PATTERN = re.compile(
    r'\s*(?:hl\[[0-9,: \-]+\]|ln\[[0-9,: \-]+\]|title\["[^"\r\n]*"\])'
)


def database_url() -> str:
    load_dotenv(ROOT / ".env")
    configured_url = os.environ.get("DATABASE_URL")
    if configured_url:
        return configured_url.replace("postgresql+psycopg://", "postgresql://", 1)

    required = ("POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB")
    missing = [key for key in required if not os.environ.get(key)]
    if missing:
        raise RuntimeError(f"Missing database settings in .env: {', '.join(missing)}")
    user = quote(os.environ["POSTGRES_USER"], safe="")
    password = quote(os.environ["POSTGRES_PASSWORD"], safe="")
    database = quote(os.environ["POSTGRES_DB"], safe="")
    port = os.environ.get("POSTGRES_PORT", "5432")
    return f"postgresql://{user}:{password}@localhost:{port}/{database}"


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
                raise RuntimeError(
                    f"Unsupported options in code include directive: {body}"
                )
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
        longest_fence = max(
            (len(run) for run in re.findall(r"`+", code)), default=0
        )
        fence = "`" * max(3, longest_fence + 1)
        language = candidate.suffix.removeprefix(".")
        source_label = candidate.relative_to(source_root.resolve()).as_posix()
        return (
            f"[Example source: {source_label}]\n"
            f"{fence}{language}\n{code}\n{fence}"
        )

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

    def flush_paragraph() -> None:
        text = "\n".join(paragraph).strip()
        if text:
            sections.append((heading, text))
        paragraph.clear()

    for line in lines:
        if re.match(r"^#{1,6}\s+", line):
            flush_paragraph()
            heading = re.sub(r"^#{1,6}\s+", "", line).strip()
        elif line.strip():
            paragraph.append(line.rstrip())
        else:
            flush_paragraph()
    flush_paragraph()
    return sections


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

        chunks.append(text[matches[start].start() : matches[end - 1].end()])
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
    file_records = []
    with psycopg.connect(database_url()) as connection:
        with connection.transaction():
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
                title = markdown_title(source_markdown, path.stem.replace("-", " ").title())
                markdown = expand_code_includes(
                    source_markdown,
                    docs_base=docs_dir.parent,
                    source_root=source_root,
                )
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
                    chunk_hash = "sha256:" + hashlib.sha256(
                        str(chunk["content"]).encode("utf-8")
                    ).hexdigest()
                    processing = Jsonb(
                        {"parser_version": PARSER_VERSION, "chunker_version": CHUNKER_VERSION}
                    )
                    connection.execute(
                        """
                        INSERT INTO chunks (
                            document_id, ordinal, heading, content, token_count,
                            embedding_input, content_hash, processing
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (document_id, ordinal)
                        DO UPDATE SET heading = EXCLUDED.heading,
                                      content = EXCLUDED.content,
                                      token_count = EXCLUDED.token_count,
                                      embedding_input = EXCLUDED.embedding_input,
                                      content_hash = EXCLUDED.content_hash,
                                      processing = EXCLUDED.processing
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
        default=ROOT / "data" / "processed" / "corpus-ingestion-report.json",
        help="write the reproducibility report here",
    )
    args = parser.parse_args()
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
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        f"Loaded {report['documents_loaded']} documents and {report['chunks_loaded']} chunks "
        f"from commit {report['source_commit']}. Report: {args.report}"
    )


if __name__ == "__main__":
    main()
