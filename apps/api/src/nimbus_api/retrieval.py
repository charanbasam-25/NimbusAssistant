"""PostgreSQL full-text search used as Nimbus's first retrieval baseline."""

from typing import Any, Literal

import psycopg

Persona = Literal["guest", "R1", "R2"]

# Each persona is allowed to search only documents with matching access tags.
# The API currently always uses "guest" until Nimbus has authenticated users.
PERSONA_ACCESS: dict[Persona, tuple[list[str], list[str]]] = {
    "guest": (["public"], ["global"]),
    "R1": (["public", "internal"], ["global", "R1"]),
    "R2": (["public", "internal"], ["global", "R2"]),
}


def search_chunks(
    connection: psycopg.Connection[Any], query: str, persona: Persona, limit: int = 5
) -> list[dict[str, Any]]:
    """Find matching passages and return them with their source details."""
    # Reject blank/tiny searches and unreasonable result counts before querying Postgres.
    normalized_query = query.strip()
    if len(normalized_query) < 3:
        raise ValueError("query must contain at least 3 non-whitespace characters")
    if not 1 <= limit <= 20:
        raise ValueError("limit must be between 1 and 20")

    audiences, regions = PERSONA_ACCESS[persona]
    rows = connection.execute(
        """
        -- Join each passage to its source document so the result can be cited/inspected.
        SELECT c.id, c.ordinal, c.heading, c.content, d.id, d.source_path,
               d.source_url, d.title, d.source_commit, c.embedding_input,
               c.content_hash, c.embedding_spec, c.processing, d.audience, d.region,
               -- PostgreSQL gives each match a ranking score; higher ranks come first.
               ts_rank_cd(c.search_text, q.query) AS score
        FROM chunks AS c
        JOIN documents AS d ON d.id = c.document_id
        -- Turn plain user text into terms PostgreSQL's English full-text search understands.
        CROSS JOIN (SELECT plainto_tsquery('english', %s) AS query) AS q
        WHERE c.search_text @@ q.query
          -- Apply the audience and region restrictions inside the search itself.
          AND d.audience = ANY(%s::text[])
          AND d.region = ANY(%s::text[])
        -- Stable tie-breakers make equally ranked results easier to reproduce.
        ORDER BY score DESC, d.source_path ASC, c.ordinal ASC
        LIMIT %s
        """,
        (normalized_query, audiences, regions, limit),
    ).fetchall()

    # Convert database rows into named fields, which are easier for FastAPI/UI clients to use.
    return [
        {
            "chunk_id": str(row[0]), "ordinal": row[1], "heading": row[2],
            "content": row[3], "document_id": str(row[4]), "source_path": row[5],
            "source_url": row[6], "title": row[7], "source_commit": row[8],
            "source_id": row[5], "source_rev": row[8],
            "record_id": f"{row[5]}@{row[8]}/{row[1]}",
            "embedding_input": row[9], "content_hash": row[10],
            "embedding_spec": row[11], "processing": row[12],
            "classification": {"audience": row[13], "region": row[14]},
            "score": float(row[15]),
        }
        for row in rows
    ]
