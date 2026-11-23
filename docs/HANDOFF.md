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
The last committed change is `2f6ee61` (`Evaluate OR keyword retrieval mode`).

The continuation brief is `Downloads/Nimbus-Transfer-Brief.pdf`. Its optional
companion `NIMBUS_TRANSFER.md` was not present beside the PDF when checked, so
the work is being reconstructed from the PDF requirements.

## Start here (Step 3)

Step 3 was completed on 2026-11-23. Its exact command results are recorded in
milestone 12 of `PROJECT_LOG.md`. Continue with the remaining odd-fence chunk
investigation, then proceed to M1 in `IMPLEMENTATION_PLAN.md`.

One planned check did not run: Ruff is absent from the API environment. Do not
report lint/format as passing until Ruff is added to the development setup and
the checks actually run.

## Open findings (planned for later milestones)

- **M5:** 600 lexical-token chunks plus contextual prefixes may exceed the
  embedding model's 512-token limit. Measure with the selected model tokenizer
  and likely cap at about 400-450 tokens. Include headings in searchable text.
- **M5-M6:** HNSW with a joined access filter may return fewer than `k` rows;
  evaluate iterative scans or denormalized access tags on chunks.
- **M4:** the evaluation set is synthetic; add roughly 100 real questions with
  source and licensing/provenance details.
- **Housekeeping:** decide whether to exclude release notes and measure impact;
  filter stale-commit documents after re-pinning; consolidate on one
  `database_url()`; trim internal fields from search responses; bind Compose
  ports to `127.0.0.1`; write an ADR for one-transaction ingestion.
- **Fence follow-up:** the count of chunks with an odd number of triple-
  backtick delimiters dropped from 104 to 58 after re-ingestion, but is not yet
  zero. Chunk windowing may split long fenced blocks; inspect samples before
  deciding whether to preserve/reopen fences across chunk boundaries.

## Session log

### 2026-11-23

- Read the transfer brief and confirmed the optional companion file was not
  available in Downloads.
- Implemented Step 1 changes from the brief. Targeted tests ran:
  `uv run --project apps/api pytest apps/api/tests evals -q` - **24 passed**.
- Applied migration 0003, re-ingested 158 documents/2,265 chunks, and ran AND
  and OR retrieval evaluations. Full results and diagnostic counts are in
  milestone 12 of `PROJECT_LOG.md`.
- Ruff was unavailable, so lint and formatting checks remain unverified. No
  commit was made.
