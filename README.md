# Nimbus Support Assistant

Nimbus is a secure AI support assistant for the official FastAPI documentation.
It answers documentation questions with citations, enforces server-side access
rules, and drafts support tickets that a user must explicitly confirm before
submission.

## Capstone goals

- Demonstrate that hybrid retrieval beats a keyword-only baseline.
- Keep R1 and R2 content strictly isolated.
- Keep p95 query latency below 6 seconds and average cost below $0.006/query.
- Prove the system with retrieval, safety, access-control, and ticket-agent evals.

## Corpus

- Source: `https://github.com/fastapi/fastapi`
- Documentation: `https://fastapi.tiangolo.com/`
- License: MIT
- Pinned snapshot: `05e6df7e906c3decba377c37548019973f40bf15` (selected 2026-11-22)
- Manifest: `docs/corpus-manifest.json`
- Reproducibility rule: ingestion uses the pinned Git commit, not the moving
  `master` branch.

## Initial layout

- `apps/api/` - FastAPI backend
- `apps/web/` - Next.js client
- `infra/` - Docker Compose and service configuration
- `docs/` - [project log](docs/PROJECT_LOG.md), architecture decisions, data
  card, evaluation evidence, and demo notes

## Status

The FastAPI documentation corpus is loaded, and a PostgreSQL keyword-retrieval
baseline with a small synthetic evaluation set is in place. Embeddings and
answer generation are the next major RAG stages. See the
[project log](docs/PROJECT_LOG.md) for progress and the next steps.
