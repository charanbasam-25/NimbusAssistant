from uuid import uuid4

import pytest
from nimbus_api.retrieval import search_chunks


class FakeConnection:
    def __init__(self, rows):
        self.rows = rows
        self.parameters = None
        self.query = None

    def execute(self, query, parameters):
        self.query = query
        self.parameters = parameters
        return self

    def fetchall(self):
        return self.rows


def test_search_chunks_returns_passage_and_source_metadata() -> None:
    chunk_id, document_id = uuid4(), uuid4()
    connection = FakeConnection(
        [
            (
                chunk_id,
                2,
                "Request body",
                "A body is declared with a Pydantic model.",
                document_id,
                "tutorial/body.md",
                "https://fastapi.tiangolo.com/tutorial/body/",
                "Request Body",
                "pinned-sha",
                "Request Body / Request body: A body is declared with a Pydantic model.",
                "sha256:content-hash",
                None,
                {
                    "parser_version": "markdown-structure-v1",
                    "chunker_version": "heading-paragraph-600-token-v1",
                },
                "public",
                "global",
                0.75,
            )
        ]
    )

    result = search_chunks(connection, "  request body  ", "guest", 5)

    assert result == [
        {
            "chunk_id": str(chunk_id),
            "ordinal": 2,
            "heading": "Request body",
            "content": "A body is declared with a Pydantic model.",
            "document_id": str(document_id),
            "source_path": "tutorial/body.md",
            "source_url": "https://fastapi.tiangolo.com/tutorial/body/",
            "title": "Request Body",
            "source_commit": "pinned-sha",
            "source_id": "tutorial/body.md",
            "source_rev": "pinned-sha",
            "record_id": "tutorial/body.md@pinned-sha/2",
            "embedding_input": "Request Body / Request body: A body is declared with a Pydantic model.",
            "content_hash": "sha256:content-hash",
            "embedding_spec": None,
            "processing": {
                "parser_version": "markdown-structure-v1",
                "chunker_version": "heading-paragraph-600-token-v1",
            },
            "classification": {"audience": "public", "region": "global"},
            "score": 0.75,
        }
    ]
    assert connection.parameters == ("request body", ["public"], ["global"], 5)
    assert "AND NOT c.flagged" in connection.query


@pytest.mark.parametrize(
    "query,limit", [("  ", 5), ("ok", 5), ("a valid query", 0), ("a valid query", 21)]
)
def test_search_chunks_rejects_invalid_query_or_limit(query, limit) -> None:
    with pytest.raises(ValueError):
        search_chunks(FakeConnection([]), query, "guest", limit)


def test_search_chunks_applies_persona_scope() -> None:
    connection = FakeConnection([])

    search_chunks(connection, "security scopes", "R1", 5)

    assert connection.parameters[1:3] == (["public", "internal"], ["global", "R1"])


def test_or_query_mode_builds_any_term_query() -> None:
    connection = FakeConnection([])

    search_chunks(connection, "Pydantic body", "guest", 5, query_mode="or")

    assert "string_agg" in connection.query
    assert " | " in connection.query
    assert connection.parameters == ("Pydantic body", ["public"], ["global"], 5)


def test_search_chunks_rejects_unknown_query_mode() -> None:
    with pytest.raises(ValueError, match="query_mode"):
        search_chunks(FakeConnection([]), "valid query", "guest", 5, query_mode="other")
