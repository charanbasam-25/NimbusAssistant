"""Regression tests for the Markdown chunker."""

import pytest

from ingest_corpus import (
    TOKEN_PATTERN,
    expand_code_includes,
    make_chunks,
    split_long_text,
)


def lexical_tokens(text: str) -> list[str]:
    """Use the chunker's token definition when checking its size guarantees."""
    return TOKEN_PATTERN.findall(text)


def test_oversized_paragraph_windows_never_exceed_lexical_token_limit() -> None:
    # Punctuation-heavy markup defeats word-count windows, so exercise the
    # exact token-count boundary with a long, single-line input.
    text = "<tag attr='value'> & " * 300

    chunks = split_long_text(text, max_tokens=50)

    assert len(chunks) > 1
    assert all(len(lexical_tokens(chunk)) <= 50 for chunk in chunks)


def test_oversized_table_prefers_complete_rows_and_overlaps_context() -> None:
    rows = [f"| cell-{index} | value-{index} |" for index in range(80)]
    text = "\n".join(rows)

    chunks = split_long_text(text, max_tokens=100)

    assert len(chunks) > 1
    assert all(len(lexical_tokens(chunk)) <= 100 for chunk in chunks)
    assert all(
        line.startswith("|") and line.endswith("|")
        for chunk in chunks
        for line in chunk.splitlines()
    )
    first_tokens = lexical_tokens(chunks[0])
    second_tokens = lexical_tokens(chunks[1])
    shared_overlap = next(
        size
        for size in range(min(len(first_tokens), len(second_tokens)), 0, -1)
        if first_tokens[-size:] == second_tokens[:size]
    )
    assert shared_overlap >= 80


def test_normal_paragraph_grouping_stays_unchanged() -> None:
    markdown = "# Intro\n\nFirst short paragraph.\n\nSecond short paragraph."

    chunks = make_chunks(markdown)

    assert len(chunks) == 1
    assert chunks[0]["heading"] == "Intro"
    assert chunks[0]["content"] == "First short paragraph.\n\nSecond short paragraph."


def test_code_include_expands_to_labeled_fenced_source(tmp_path) -> None:
    docs_base = tmp_path / "docs" / "en"
    docs_src = tmp_path / "docs_src"
    docs_base.mkdir(parents=True)
    docs_src.mkdir()
    (docs_src / "example.py").write_text("app = FastAPI()\n", encoding="utf-8")

    expanded = expand_code_includes(
        'Example:\n\n{* ../../docs_src/example.py hl[1] title["Example"] *}',
        docs_base,
        tmp_path,
    )

    assert "{*" not in expanded
    assert "[Example source: docs_src/example.py]" in expanded
    assert "```py\napp = FastAPI()\n```" in expanded


def test_code_include_rejects_paths_outside_docs_src(tmp_path) -> None:
    docs_base = tmp_path / "docs" / "en"
    docs_src = tmp_path / "docs_src"
    docs_base.mkdir(parents=True)
    docs_src.mkdir()

    with pytest.raises(RuntimeError, match="inside"):
        expand_code_includes("{* ../../secrets.txt *}", docs_base, tmp_path)


def test_code_include_rejects_missing_files(tmp_path) -> None:
    docs_base = tmp_path / "docs" / "en"
    docs_src = tmp_path / "docs_src"
    docs_base.mkdir(parents=True)
    docs_src.mkdir()

    with pytest.raises(RuntimeError, match="does not exist"):
        expand_code_includes("{* ../../docs_src/missing.py *}", docs_base, tmp_path)
