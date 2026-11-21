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
- Reproducibility rule: ingestion will use a pinned Git commit, recorded in the
  corpus manifest.

## Initial layout

- `apps/api/` - FastAPI backend
- `apps/web/` - Next.js client
- `infra/` - Docker Compose and service configuration
- `docs/` - architecture decisions, data card, evaluation evidence, and demo notes

## Status

Week 1 - corpus selected and repository initialized.
