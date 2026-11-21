from fastapi import FastAPI

app = FastAPI(
    title="Nimbus Support Assistant API",
    version="0.1.0",
)


@app.get("/health/live", tags=["health"])
async def liveness() -> dict[str, str]:
    """Confirm that the API process is accepting requests."""
    return {"status": "ok"}
