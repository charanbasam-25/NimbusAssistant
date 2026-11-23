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
a PostgreSQL keyword-search baseline, retrieval evaluation harness, ingestion
PII masking, input guardrails, and flagged-chunk filtering. It is not yet a
full RAG assistant: no embeddings, vector retrieval, authentication,
answer-generating LLM, or access-controlled regional corpus are implemented.
The last committed change is `5cb2422` (`Repair chunk fences and establish
CI`); M1 changes are currently uncommitted.

## Start here (Step 3)

The original Step 3 checks were completed on 2026-11-23 and recorded in
milestone 12 of `PROJECT_LOG.md`. The odd-fence investigation confirmed that
long code blocks were split at the chunk size cap. Fence repair wraps each
split fragment independently and repeats included-example source labels when a
continuation reopens a fence. Local M0 checks passed, and hosted CI run
`45211237914` passed on commit `5cb2422`.

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
- **Hosted CI:** run `45211237914` passed on `5cb2422`; subsequent M1 changes
  have not yet been committed or checked by hosted CI.

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
  600. CI workflow was created in this continuation.

### 2026-11-23 - hosted CI and M1

- Verified GitHub Actions CI run `45211237914`: **passed** for pushed commit
  `5cb2422` (`Repair chunk fences and establish CI`).
- Added a versioned PII masker, request guardrails, `chunks.flagged` migration
  and retrieval exclusion. Masking runs over each expanded document before
  chunking; processing metadata records the PII and detector versions.
- Fence repair now repeats `[Example source: ...]` before a reopened included
  code fence. Added a regression that checks every fragment of a long example
  keeps its source label. The chunker version is
  `heading-paragraph-lexical-600-fence-repair-v3`.
- Re-ingested the pinned snapshot: 158 documents, 2,270 chunks, 0 flagged
  chunks. The lexical cap remains 600; SQL confirms 0 over-cap chunks and 0
  odd triple-backtick chunks. The ingestion report contains 13 `secret`
  pattern masks from the FastAPI security examples and no other mask category.
  Corpus scan found no unsafe/injection flags. Example-domain emails were
  retained; the two Luhn-valid card-shaped matches were ISBN/URL identifiers
  and are excluded by the context-aware card check; no phone or IBAN matches
  were found.
- Updated the database integration test to derive Alembic's current head from
  `apps/api/alembic.ini`; migration `0004_chunk_flagged` is current. The
  refreshed keyword baselines remain synthetic: AND Recall@5 **0.733**, nDCG@5
  **0.626**, MRR **0.589**, code hit@5 **4/9**; OR Recall@5 **0.667**, nDCG@5
  **0.488**, MRR **0.430**, code hit@5 **3/9**.
- Final local Ruff and pytest commands/results are recorded in milestone 14
  of `PROJECT_LOG.md`. M1 changes remain uncommitted; propose, but do not run,
  commit message: `Add PII masking, input guardrails and injection flagging (M1)`.
