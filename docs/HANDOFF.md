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
full RAG assistant: embeddings, vector retrieval, and answer generation are
not implemented. M2 synthetic pages and M3 authentication/access-scoped search
are implemented. The three local demo users are seeded, and live R1 login was
verified on 2026-11-24. Recent commits are `853f21a` (auth/synthetic corpus),
`ee626f5` (real-question workflow), and `8408bb2` (Ticket Agent/eval harness
specifications). Hosted CI run 4 passed; the current commit is `8408bb2`.

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
- **M4:** Stack Exchange collection returned 189 candidates on 2026-11-24.
  Owner confirmation is pending in `evals/labeling/batch-01.md`; there are no
  confirmed real labels or real baselines yet.
- **Housekeeping:** decide whether to exclude release notes and measure impact;
  filter stale-commit documents after re-pinning; trim internal fields from
  search responses; bind Compose ports to `127.0.0.1`; write an ADR for
  one-transaction ingestion.
- **Hosted CI:** run `45218348110` passed on `b7279ff`.

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
  of `PROJECT_LOG.md`. M1 was committed as `b7279ff`.

### 2026-11-23 - start M2/M3

- Verified previous-push CI run `45218348110`: **passed** for commit
  `b7279ff`. This is the first check in the M2/M3 continuation.
- Read this handoff, the project-log rules, and
  `docs/specs/nimbus-cloud-synthetic.md` before starting implementation.

### 2026-11-23 - M2/M3 implementation and verification

- Added 38 synthetic Nimbus Cloud Markdown documents and a validating
  manifest-driven ingestion mode. Database ingestion loaded 38 documents / 153
  chunks, flagged 5 poison chunks, and masked one synthetic value for each of
  card, email, IBAN, phone, and secret. No raw canary value remained in chunk
  content. FastAPI docs re-ingestion remained at 158 documents / 2,270 chunks,
  0 flags, and 13 secret masks.
- Added EdDSA authentication, Argon2 password utilities, access-scoped search,
  key generation, user seeding, and source-path access evaluation. Evaluation
  reports 51 cases, 0 leaks, and 1.000 expected-document recall. Two low-recall
  questions were made more specific after an initial 0.882 recall result.
- Added guardrail normalization for zero-width characters/base64 padding and
  set the query limit to 1,000 characters. Created local JWT keys with
  directory/private/public modes 0700/0600/0644. These keys are ignored by Git.
- `uv run alembic upgrade head` completed. Ruff format/check passed. The
  non-integration suite passed **127 tests** (1 integration test deselected);
  the separate marked PostgreSQL/pgvector test passed (**1 passed**). Live
  `GET /me` as guest returned 200; `Bearer junk` returned 401 with a bearer
  challenge. Guest search returned no regional or internal documents.
- Demo users were not seeded because local `.env` has no `SEED_PASSWORD`.
  Authenticated live R1 login remains pending the owner setting a local value
  of at least 12 characters. Do not request or record that value in chat.
- No commit was made. Proposed commits (do not run until explicitly asked):
  `Add Nimbus Cloud synthetic corpus and ingestion (M2)` and
  `Add login, EdDSA tokens, access-scoped search and access eval (M3)`.

### 2026-11-24 - M2/M3 follow-ups

- Verified hosted CI run number 3 (`45228066997`) passed for M3 commit
  `e2ed82a` and recorded the result in milestone 16 before Part A changes.
- Rewrote all 38 synthetic bodies as topic-specific hosting documentation;
  preserved the front matter, manifest, adversarial/PII payloads, and closing
  disclaimer. Validation now rejects the terms `canary` and `retrieval
  exercise`; paired regional bodies are checked for exactly one changed fact
  line. Ingestion reports 38 documents / 153 chunks, 5 flagged chunks, and 1
  mask each for card/email/IBAN/phone/secret. Access evaluation is 51 cases, 0
  leaks, recall 1.000.
- Added migration `0005_users_email_lower_unique`, with duplicate-email
  detection and an integration assertion for the expression index. Authentication
  now caches token settings; missing/unreadable key files return 503 while bad
  tokens remain 401.
- Initial live user seeding could not proceed: the seed command exited 2
  because `SEED_PASSWORD` was missing or shorter than 12 characters. The
  owner later configured a qualifying value locally; do not ask them to share
  it.
- `uv run --project apps/api ruff format --config apps/api/pyproject.toml
  apps/api evals` and matching `ruff check` passed. The full non-integration
  suite passed **134 tests** (1 deselected); the marked PostgreSQL integration
  test passed (**1 passed**). `uv run alembic upgrade head` applied migration
  0005. Access evaluation remains **51 cases / 0 leaks / 1.000 recall**. SQL
  checks found five flagged poisoned sources, zero raw PII values in chunks,
  and zero regional/internal results in guest search.
- No commit was made for these follow-ups. Continue at Part A's live-login
  check after a valid local seed password is configured, then proceed to M4
  only after the owner reviews these Part A results.
- **Resolution (2026-11-24):** `uv run --project apps/api python
  scripts/seed_users.py` seeded or updated three users. Live API verification
  returned login **200**, `/me` **200** with persona **R1**, and wrong-password
  login **401**. The API process was stopped afterward. No password was logged
  or recorded. The only remaining Part A changes are uncommitted.

### 2026-11-24 - M4 real-question collection (in progress)

- Added the Stack Exchange API collector and fetched two pages. It saved
  responses and 189 filtered candidates in ignored `data/raw/questions/`;
  GitHub Discussions was skipped because `GH_TOKEN` was not available.
- Added offline parser/filter tests, the owner-confirmation batch workflow,
  JSONL export and validation tools, optional provenance fields in the
  retrieval loader/schema, and M4 instructions. Added ADR 002 for
  paraphrase-plus-link attribution; raw third-party bodies are not committed.
- Prepared 25 proposals in `evals/labeling/batch-01.md`. They remain
  unconfirmed, so no real datasets or baselines have been created/run. Human
  confirmation is the next gate. Do not commit until asked.

### 2026-11-24 - Adopt seven-step eval process (docs/templates only)

- Added `docs/EVAL_PROCESS.md` with seven iterative steps, each with purpose,
  artifacts, and exit criteria. Error coding runs after v0 and feeds later
  judge/synthetic design; regression cases flow back into the datasets.
- Updated the plan with M4b (~3 h), M4 expected facts, calibrated M7 judge
  gate (+2 h), M6/V2 benchmark and hybrid error coding, M11 weekly review and
  panels (+1 h), and M12 final benchmark/error coding (+2 h). Week 2 now covers
  M4, M4b, and M5–M7; approximately 8 Core hours were added. If behind, keep
  v0, error coding, and calibration Core; move beyond 40 synthetic tuples and
  automated weekly sampling to Should have.
- Added error-analysis README/taxonomy/header-only CSV and the synthetic
  dimension grid; added `evals/traces/` to `.gitignore`; linked the process from
  the implementation plan and data card. No eval code or dataset rows changed
  in this docs-only follow-up. Earlier uncommitted M4 and Part A changes remain
  in the worktree.
- Structural checks confirmed seven complete step sections, all templates,
  trace ignore, and zero trace files; `git diff --check` passed. Ruff format:
  **39 files left unchanged**; Ruff check: **all checks passed**; pytest:
  **145 passed, 1 deselected**. No commit was made.
- Proposed commit (do not run): `Adopt 7-step eval process`.

### 2026-11-24 - Ticket Agent spec and harness addendum (docs/config only)

- Confirmed `docs/EVAL_PROCESS.md` exists and applied its seven-step feedback
  loop before adding the harness specification. Added a Ticket Agent design
  covering A1–A5 and a six-topic YAML catalog. The harness contract now covers
  B1–B11 and cites Anthropic's “Demystifying evals for AI agents”.
- Updated `docs/IMPLEMENTATION_PLAN.md`: M4b harness core (+3 h), M7 answers
  suite, M9 Ticket Agent and ticket-column migration, M10 form UI, M12 a
  simulated-user suite of about 30 balanced tasks (3 trials, pass@1/pass^3,
  +3 h), plus M9/M10 effort and the CI regression-suite gate. Corrected the
  estimate to 56–64 Core hours (the existing 40–48 h Core estimate plus ~16 h
  of eval/agent/harness work), about 16–24 h over the original 32–40 h budget.
  Preserved the cut line: v0/error coding/calibration stay Core; expansion
  beyond 40 tuples
  and automated weekly sampling move to Should have.
- PyYAML validation found six unique topic IDs, no topic with more than two
  fields, and only `text`/`textarea`/`select` types. Structural checks found
  A1–A5 and B1–B11, the planned milestone edits, and transcript ignore; no
  transcript files exist. `git diff --check` passed. Ruff format left **39
  files unchanged**; Ruff check passed; pytest reported **145 passed, 1
  deselected**.
- This turn changed docs/config only; no harness or ticket implementation was
  added. Earlier uncommitted Part A/M4 work remains in the worktree. No commit
  was made. Proposed commit: `Add Ticket Agent spec, topic catalog and eval
  harness plan`.
- Harness reports are specified to include pass@1/pass^k, partial-credit mean,
  p50/p95 latency, token usage, and estimated cost for every suite; one-trial
  deterministic suites report pass@1 and pass^1.

### 2026-11-24 - Small fixes after 8408bb2

- Updated the batch-01 workflow test to validate 25 candidate sections and
  exactly one parseable JSON label block per candidate, without asserting
  anything about confirmation ticks.
- `current_claims` now maps `ValueError` (including `UnicodeDecodeError`) from
  token-settings loading to the same 503 configuration response as `OSError`;
  added a Unicode decoding regression test.
- Recorded commits `853f21a`, `ee626f5`, and `8408bb2`, and hosted CI run 4
  passing, with current commit `8408bb2`. Fixed the milestone 16 Markdown
  emphasis typo and corrected the Core estimate to 56–64 hours (40–48 h
  existing estimate plus ~16 h additions), 16–24 h above the 32–40 h budget.
- Checks run: Ruff format reported **39 files left unchanged**; Ruff check
  passed; `uv run --project apps/api pytest apps/api/tests evals -q` passed
  (**146 passed, 1 deselected**).
- No commit made. Proposed commit: `Fix batch test, auth key errors and plan
  hours`.
