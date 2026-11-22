import os
from pathlib import Path
from urllib.parse import quote

import psycopg
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from nimbus_api.retrieval import search_chunks

ROOT = Path(__file__).resolve().parents[4]
load_dotenv(ROOT / ".env")

app = FastAPI(
    title="Nimbus Support Assistant API",
    version="0.1.0",
)


@app.get("/health/live", tags=["health"])
async def liveness() -> dict[str, str]:
    """Confirm that the API process is accepting requests."""
    return {"status": "ok"}


class RetrievalRequest(BaseModel):
    query: str = Field(min_length=3, max_length=2000)
    limit: int = Field(default=5, ge=1, le=20)


def database_url() -> str:
    # Prefer a complete URL; otherwise build one from the individual Docker/.env settings.
    configured_url = os.environ.get("DATABASE_URL")
    if configured_url:
        return configured_url.replace("postgresql+psycopg://", "postgresql://", 1)

    required = ("POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB")
    missing = [key for key in required if not os.environ.get(key)]
    if missing:
        raise RuntimeError(f"Missing database settings: {', '.join(missing)}")
    user = quote(os.environ["POSTGRES_USER"], safe="")
    password = quote(os.environ["POSTGRES_PASSWORD"], safe="")
    database = quote(os.environ["POSTGRES_DB"], safe="")
    port = os.environ.get("POSTGRES_PORT", "5432")
    return f"postgresql://{user}:{password}@localhost:{port}/{database}"


@app.post("/v1/retrieval/search", tags=["retrieval"])
def retrieve(request: RetrievalRequest) -> dict[str, object]:
    """Search indexed documentation and return inspectable source passages."""
    try:
        # Open a short-lived connection for this request, run search, then close it.
        with psycopg.connect(database_url()) as connection:
            # Until authentication exists, callers cannot self-assert a privileged persona.
            results = search_chunks(connection, request.query, "guest", request.limit)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except (psycopg.Error, RuntimeError) as error:
        raise HTTPException(status_code=503, detail="Retrieval database is unavailable") from error
    # Return the query and access scope alongside the evidence for easy inspection.
    return {"query": request.query, "persona": "guest", "results": results}
