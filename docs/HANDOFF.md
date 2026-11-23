# Nimbus continuation handoff

## Working rules

- Do not commit unless the project owner explicitly asks.
- Record verified milestones in `PROJECT_LOG.md`; keep work in progress here.
- Never claim a test passed without running it; include the command and result.
- Document blockers with evidence, impact, and status, then record the verified
  resolution when one exists.
- Capture important learning questions in the project log, not incidental or
  private questions.
- Do not use employer material or real secrets. Clearly label synthetic data.

## Context

Nimbus is a FastAPI RAG support-assistant capstone. The current source is a
pinned snapshot of official FastAPI documentation, and the implementation has
a PostgreSQL keyword-search baseline and retrieval evaluation harness. It is
not yet a full RAG assistant: no embeddings, vector retrieval, authentication,
answer-generating LLM, or access-controlled regional corpus are implemented.
The last committed change is `cbfd363` (`Harden Markdown parsing and page-level
evaluation`).

## Start here (Step 3)

The original Step 3 checks were completed on 2026-11-23 and recorded in
milestone 12 of `PROJECT_LOG.md`. The odd-fence investigation confirmed that
long code blocks were split at the chunk size cap. Fence repair now wraps each
split fragment independently. Local M0 checks have passed; the hosted GitHub
Actions workflow still needs to run after an authorized push.

The implementation is locally verified, but do not report hosted CI as green
until the GitHub Actions run completes successfully.

## Open findings (planned for later milestones)

- **M5:** 600 lexical-token chunks plus contextual prefixes may exceed the
  embedding model's 512-token limit. Measure with the selected model tokenizer
  and likely cap at about 400-450 tokens. Include headings in searchable text.
- **M5-M6:** HNSW with a joined access filter may return fewer than `k` rows;
  evaluate iterative scans or denormalized access tags on chunks.
- **M4:** the evaluation set is synthetic; add roughly 100 real questions with
  source and licensing/provenance details.
- **Housekeeping:** decide whether to exclude release notes and measure impact;
  filter stale-commit documents after re-pinning; trim internal fields from
  search responses; bind Compose ports to `127.0.0.1`; write an ADR for
  one-transaction ingestion.
- **Hosted CI:** local unit, migration, integration, Ruff, and format checks
  passed; verify the GitHub Actions result after the owner authorizes a push.

## Session log

### 2026-11-23

- Read the supplied project brief; no companion Markdown instructions were
  available in the project context.
- Implemented Step 1 changes from the brief. Targeted tests ran:
  `uv run --project apps/api pytest apps/api/tests evals -q` - **24 passed**.
- Applied migration 0003, re-ingested 158 documents/2,265 chunks, and ran AND
  and OR retrieval evaluations. Full results and diagnostic counts are in
  milestone 12 of `PROJECT_LOG.md`.
- Ruff was not yet installed in that session; the following continuation adds
  it and records successful local checks. No commit was made.

### 2026-11-23 - continuation

- Corrected the handoff's current commit to `cbfd363` and removed an obsolete
  local-file reference.
- Inspected the 58 odd-fence rows with their path, ordinal, heading, token
  count, and text edges. Representative chunks ended/started inside the same
  included code example at roughly 600 tokens; all 58 were below the exact cap
  after line-boundary selection but were split by the size-window strategy.
- Added fence reopen/close repair and tests for both backtick and tilde fences.
  An in-memory scan of the pinned corpus now reports 2,265 chunks, maximum 600
  lexical tokens, and 0 odd triple-backtick chunks. Database re-ingestion and
  SQL verification remain to be run.
- Added the synthetic manifest shape and the shared questions/canary fields
  for all 10 internal runbook topics to the specification.
- Added Ruff and shared URL construction. `uv sync --project apps/api --locked
  --all-groups` completed; `ruff check` and `ruff format --check` passed.
- `uv run --project apps/api pytest apps/api/tests evals -q -m "not
  integration"` passed (30 passed, 1 deselected); the marked integration test
  passed (1 passed); `uv run alembic upgrade head` completed from `apps/api`.
- Re-ingested 158 documents/2,265 chunks. The SQL diagnostic reports 0 chunks
  with odd triple-backtick counts and 0 above 600 tokens; max `token_count` is
  600. CI workflow is created but has not run on GitHub yet. No commit was
  made.
