# Nimbus API

FastAPI backend for the Nimbus Support Assistant.

## Local development

```bash
uv sync --all-groups
uv run fastapi dev src/nimbus_api/main.py
```

The service exposes `GET /health/live` for a process-level health check.
