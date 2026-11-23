import psycopg
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from nimbus_api.config import database_url
from nimbus_api.retrieval import search_chunks

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
