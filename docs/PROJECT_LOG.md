# Nimbus project log

This is the chronological learning journal for Nimbus. It records what we did,
why we did it, how we checked it, and what is still left to do. It is written
for the project team and for the capstone report—not as a replacement for the
source code or architecture decisions.

## How to keep this log useful

- Add an entry when a meaningful project step is finished, not after every
  small code edit.
- Explain new technical terms in plain language the first time they appear.
- Record the files changed and the checks actually run. Do not say a feature is
  complete just because its code exists.
- Record important choices and their reasons in `docs/adr/`; link to the ADR
  from the relevant log entry.
- Record blockers with evidence, impact, and status. When resolved, record the
  fix and how we verified it; do not mark an open blocker as resolved just
  because a fix was proposed.
- Record important learning questions in the learning notes below. Capture
  each concept and the explanation or project example that clarified it.
  Treat these as topics to revisit, not as a measure of the user's ability;
  omit incidental questions and private data.
- Keep credentials, passwords, API keys, and private user data out of this file.
- Do not commit changes until the project owner asks for a commit.

## Project status at a glance

Nimbus is a FastAPI support-assistant capstone. Its current corpus is a pinned
snapshot of the official FastAPI documentation: 158 Markdown documents and,
after milestone 14 re-ingestion, 2,270 chunks. M2 adds 38 synthetic Nimbus
Cloud documents (153 chunks) for region/access tests. M3 implements EdDSA
tokens and access-scoped search; live guest and invalid-token checks pass.
The three demo users are seeded, and live R1 login was verified on 2026-11-24.
Nimbus is **not yet a complete RAG assistant**: embeddings
and answer generation have not been implemented.

## Milestones

### 1. Local project and service foundation

**Goal:** Create a local development environment and a place for the API and
its data services to run.

**What we set up:**

- FastAPI as the backend framework.
- Docker Compose services for PostgreSQL with pgvector, Redis, Prometheus, and
  Grafana.
- An initial API liveness route at `GET /health/live`.
- Git and the Nimbus GitHub repository. The user asked that we not commit
  further changes without explicit permission.

**Why Docker:** Docker Compose starts the supporting services with consistent
configuration, without requiring each service to be installed and maintained
separately on the Mac.

### 2. Database schema and migrations

**Goal:** Create the database structure that later features can use.

**What we added:** Alembic migrations define tables for users, documents,
chunks, tickets, query logs, and events. The schema enables PostgreSQL full-text
search and pgvector storage. Alembic is the tool that applies versioned database
schema changes; a migration is one recorded change to that schema.

### 3. Choose and load a reproducible documentation corpus

**Goal:** Use a real, traceable source instead of arbitrary PDFs so retrieval
results can be checked against source material.

**Decision:** Use a pinned commit of the official FastAPI documentation. The
choice and its consequences are recorded in
[`ADR 001`](adr/001-fastapi-corpus.md); corpus version and exclusions are in
[`corpus-manifest.json`](corpus-manifest.json).

**What we loaded:** 158 Markdown documents and 2,020 chunks from the pinned
snapshot. The ingestion report is written under the ignored
`data/processed/` directory; the upstream checkout is under ignored
`data/raw/`.

### 4. Chunking and chunk provenance

**Goal:** Split source pages into passages that can be searched and later
embedded, while preserving enough context to identify where each passage came
from and how it was prepared.

**Current chunking baseline:** The ingestion code groups Markdown paragraphs
under their headings, with a hard cap of 600 regex-counted lexical tokens.
Oversized paragraphs use token-based windows with up to 80 lexical tokens of
overlap; the splitter prefers line boundaries where possible. This is an
initial setting, not proven optimal.

**What each stored chunk now records:**

- Original passage text (`content`) and the document's heading.
- An `embedding_input` made from the document title, heading, and passage;
  this is the contextualized text intended for a future embedding model.
- A SHA-256 hash of the original passage and a `processing` object containing
  parser/chunker version identifiers.
- Existing Nimbus source identity and classification: source path/commit,
  audience, and region.

The additive schema change is in
[`0002_chunk_provenance.py`](../apps/api/migrations/versions/0002_chunk_provenance.py).
The 384-dimensional vector column exists, but embeddings have **not** been
generated. Accordingly, `embedding_spec` and vector values remain empty.
Tenant and role fields from the cohort's example were not copied because they
do not match Nimbus's current access design.

### 5. Keyword retrieval and first evaluation

**Goal:** Build a measurable retrieval step before adding vector search or
answer generation.

**What we added:**

- `POST /v1/retrieval/search` searches chunk text with PostgreSQL English
  full-text search and returns ranked passages with source metadata.
- The public route searches as `guest` only. A caller cannot claim an R1/R2
  persona until Nimbus has authentication to determine the caller's access.
- Six synthetic questions in
  [`evals/datasets/retrieval.jsonl`](../evals/datasets/retrieval.jsonl).
- An evaluation runner that reports Recall@5, nDCG@5, and MRR. The initial
  synthetic run reported Recall@5 **1.00**, nDCG@5 **0.73**, and MRR **0.64**;
  the report is at
  [`evals/reports/keyword-baseline.json`](../evals/reports/keyword-baseline.json).

These scores describe only this small synthetic set. They are not evidence of
real user-question quality. The evaluation questions and relevance labels need
to be expanded and checked against actual support questions before making
quality claims.

### 6. Inspect sample chunk boundaries — 2026-11-22

**Goal:** Check stored chunks against representative source Markdown before
creating embeddings.

**What we inspected:** All 34 stored chunks from `tutorial/body.md`,
`tutorial/metadata.md`, and `advanced/opentelemetry.md` (11, 12, and 11 chunks,
respectively). The samples include prose, code fences, and a Markdown table.

**Initial corpus scan:** We ran the original `make_chunks` logic in memory over
all 158 included Markdown files in the pinned checkout (2,020 simulated
chunks). Two pages contain standard pipe-style Markdown tables:
`tutorial/metadata.md` and `advanced/opentelemetry.md`. **110 of 2,020
simulated chunks exceed 600 tokens**: 107 are from `release-notes.md`, and one
each from `deployment/server-workers.md`, `index.md`, and
`tutorial/metadata.md`. This scan identified why the word-window fallback did
not enforce the target.

**Findings:**

- Prose chunks generally stayed under their headings and grouped related
  paragraphs. The request-body chunks and the OpenTelemetry setup example read
  coherently in the stored text.
- `tutorial/metadata.md`, chunk ordinal 2, contains a markup-heavy table and has
  a stored lexical token count of **819**, above the nominal 600 target. The
  full scan shows this is not isolated: 110 simulated chunks exceed the target,
  mostly because long release-note paragraphs are split using whitespace word
  windows whose punctuation-heavy text can still exceed the lexical-token
  limit.
- At the time of this inspection, Markdown code includes such as
  `{* ../../docs_src/... *}` were stored literally rather than expanded. This
  was resolved in milestone 8 below.

**Conclusion:** The original chunker was a reasonable prose baseline but did
not enforce its size target. The updated chunker now enforces 600 lexical
tokens, and code includes are expanded. Retrieval quality for table- and
code-answer questions still needs evaluation.

**Blockers and status:**

1. **Chunk size target not enforced — resolved and verified.** Original
   evidence: stored `tutorial/metadata.md` chunk ordinal 2 had 819 lexical
   tokens, and the old chunker produced 110 over-target chunks in a full-corpus
   simulation. The new splitter has tests; after re-ingestion, the database
   contains 2,197 chunks, maximum token count 600, and zero chunks over the
   limit.
2. **Code examples remained include references — resolved and verified in
   milestone 8.** The ingestion step expands supported directives to fenced
   code blocks, restricted to the pinned checkout's `docs_src/` and `fastapi/`
   directories. Tests cover successful expansion, missing files, and path
   escape. The corpus scan expanded 455 directives; database checks confirmed
   the known body example is stored and its literal directive is gone.

**Next:** Inspect representative refreshed chunks and evaluate code-answer
retrieval before starting embeddings.

### 7. Enforce the lexical chunk limit — 2026-11-22

**Goal:** Keep ordinary paragraph grouping, but guarantee oversized paragraph
chunks do not exceed the configured lexical-token limit.

**What changed:** `evals/ingest_corpus.py` now splits oversized paragraphs by
the same lexical-token definition used for `token_count`, using 80-token
overlap and preferring line breaks when available (useful for table rows and
code lines). The chunker version was updated. Re-ingestion now removes a
document's old chunk rows before inserting its newly computed chunks, avoiding
stale higher ordinals if the chunk count changes. Added regression tests in
`evals/test_ingest_corpus.py`.

**How we checked it:** `uv run --project apps/api pytest
evals/test_ingest_corpus.py` passed (3 tests). An in-memory pass over all 158
included Markdown files generated 2,197 chunks with **0 above 600 tokens**.
The corpus was then re-ingested from the pinned checkout: 158 documents and
2,197 chunks loaded. A read-only database query verified 2,197 stored chunks,
maximum token count 600, and zero above the limit. `tutorial/metadata.md`
produced 12 chunks (maximum 600 tokens); `advanced/opentelemetry.md` produced
11 (maximum 332).

**Blocker / resolution:** The lexical size-cap issue is resolved and verified
in the database. The code-include blocker is resolved in milestone 8.

**Next:** Inspect table and release-note examples from the refreshed database,
and compare code-answer retrieval against the labeled evaluation questions. Do
not commit until requested.

### 8. Expand included code examples — 2026-11-22

**Goal:** Make code referenced by FastAPI Markdown include directives
available to retrieval, without allowing paths to escape the pinned checkout.

**What changed:** `evals/ingest_corpus.py` now recognizes standalone include
directives, supports upstream `hl[...]`, `ln[...]`, and `title[...]`
annotations, resolves paths from `docs/en`, and inserts a labeled fenced code
block. Resolved paths must remain under the pinned checkout's `docs_src/` or
`fastapi/` directory. Missing files, unsafe paths, and unsupported options
fail ingestion clearly. The parser version was updated.

**How we checked it:** All 13 API and ingestion tests passed. The resolver
expanded all 455 standalone includes across the 158 included Markdown files;
the full simulation had no remaining directives and produced 2,270 chunks,
none above 600 tokens. Re-ingestion loaded 158 documents and 2,270 chunks. A
read-only database check confirmed 0 chunks above 600 tokens. In
`tutorial/body.md`, 3 stored chunks contain the expanded
`docs_src/body/tutorial001.py` example and 0 contain the old literal include.

**Blocker / resolution:** The include-reference blocker is resolved for the
supported upstream syntax and approved source roots. No commit was made.

**Next:** Inspect code-example retrieval results and update the evaluation
questions if needed, then choose and record the embedding model.

### 9. Smoke-test retrieval of included code — 2026-11-22

**Goal:** Check whether keyword retrieval can return the newly stored code
examples, not only whether ingestion expanded them.

**What changed:** Added three synthetic code-retrieval probes to
`evals/datasets/retrieval.jsonl` for a Pydantic request body, JWT bearer auth,
and multiple-file upload. Their labels point to the relevant source pages; the
notes identify the expected included source file.

**How we checked it:** The PostgreSQL full-text evaluation passed all three
source-page labels at rank 1. The overall nine-question synthetic set scored
Recall@5 **1.00**, nDCG@5 **0.862**, and MRR **0.815**. We also inspected the
actual top-ranked passages: with the focused technical-term probes, all three
expected code examples appeared in the rank-1 passage. This is only a small
synthetic smoke test, not evidence of real-user retrieval quality.

**Blocker / resolution:** Include ingestion is resolved. Keyword retrieval is
still sensitive to query wording: a more natural body question found the right
page but not the specific `tutorial001.py` chunk in the top five, while a
natural JWT question returned no matches. The focused technical-term probes
worked. Add realistic paraphrases to the evaluation set and improve retrieval
before claiming robust code-example search.

**Next:** Expand the synthetic evaluation with natural phrasings and diagnose
keyword-query brittleness before comparing vector retrieval.

### 10. Measure natural-language code retrieval — 2026-11-22

**Goal:** Extend retrieval evaluation beyond source-page hits and measure
whether the expected included-code passage itself appears in the top results.

**What changed:** Added six natural-language paraphrases for request-body,
JWT, and file-upload code questions. Evaluation records can now include
`expected_code_sources`; `run_retrieval.py` reports `code_hit_at_k` per
question plus a code-example hit rate. The JSON schema and tests were updated.

**How we checked it:** All 17 API and evaluation tests passed. The 15-question
synthetic set ran successfully: overall source-page Recall@5 was **0.733**,
nDCG@5 **0.626**, and MRR **0.589**. Of 9 code-example checks, code hit@5 was
**4/9**. The three focused technical-term probes hit their expected code
passages (3/3); natural paraphrases hit only 1/6, and only 2/6 retrieved the
expected source page at all. This is a small synthetic diagnostic set, not a
quality claim about real user questions.

**Finding:** The production query uses PostgreSQL `plainto_tsquery('english',
...)`; PostgreSQL connects surviving query words with AND, so adding a synonym
or a word absent from the indexed page can eliminate otherwise relevant
matches. See [PostgreSQL text-search controls](https://www.postgresql.org/docs/18/textsearch-controls.html).

**Blocker / resolution:** Code include ingestion works; keyword retrieval is
not robust to these natural paraphrases yet. The new code-passage metric makes
that failure visible separately from source-page retrieval. Test a controlled
keyword-query improvement against this same set before comparing embeddings.

**Next:** Compare one measured keyword-query adjustment with the current
baseline, retaining both source-page and code-passage metrics.

### 11. Compare an OR-term keyword query — 2026-11-22

**Goal:** Test whether allowing any query term to match improves the natural
paraphrase failures without changing the production default.

**What changed:** Added an experimental `query_mode="or"` to the shared search
function and `--query-mode or` to the evaluation runner. It builds an OR query
from individually normalized terms using PostgreSQL text-search functions.
The default remains the original AND query; the API does not opt into the
experiment.

**How we checked it:** The same 15 synthetic questions were evaluated in both
modes. AND scored source-page Recall@5 **0.733**, nDCG@5 **0.626**, MRR **0.589**,
and code hit@5 **4/9**. OR scored Recall@5 **0.533**, nDCG@5 **0.429**, MRR
**0.394**, and code hit@5 **3/9**. OR did retrieve the expected upload code for
both natural upload paraphrases (2/6 natural code checks versus 1/6 under AND),
but it lost many focused and general matches. All 19 tests passed, and the OR
evaluation ran successfully against the local database.

**Blocker / resolution:** Global OR matching is not a suitable replacement for
the AND baseline on this set. Keep AND as production default; retain OR only as
an evaluation option. The paraphrase failures likely need semantic retrieval
or a carefully measured hybrid rather than indiscriminately broadening terms.

**Next:** The original comparison retrieved only five candidate chunks. The
updated evaluator in milestone 12 considers up to 20 candidates before page
deduplication, so those earlier OR scores are not directly comparable with the
new scores.

### 12. Harden Markdown fences and page-level evaluation — 2026-11-23

**Goal:** Keep fenced code intact during Markdown parsing, require an explicit
region on every user row, and prevent repeated chunks from one document from
occupying multiple evaluation page slots.

**What changed:** `markdown_sections()` now tracks backtick and tilde fences;
inside a fence, headings and blank lines remain code, and only a bare matching
fence of equal or greater length closes it. The parser version is
`markdown-includes-fences-v3`. Migration `0003_user_region_required` makes
`users.home_region` non-null. The retrieval evaluator fetches up to 20 candidate
chunks, collapses those to each page's best-ranked chunk, and scores the top-k
distinct pages. `code_hit_at_k` continues to use the top-k chunks. Added five
regression tests and documented the change in the evaluation guide and new
implementation, handoff, and synthetic-corpus documents.

**How we checked it:** `uv sync --project apps/api --all-groups` completed;
`uv run --project apps/api pytest apps/api/tests evals -q` passed (**24
passed**); `git diff --check` passed. Alembic applied
`0003_user_region_required`; `\d users` showed `home_region` as `not null` and
`alembic_version` as `0003_user_region_required`. Re-ingestion loaded 158
documents and 2,265 chunks from pinned commit
`05e6df7e906c3decba377c37548019973f40bf15`.

Before/after database checks: chunks with a heading matching `^(\d+)!` fell
from **9 to 0**; chunks with an odd count of triple-backtick delimiters fell
from **104 to 58**. The latter dropped by 46 chunks but remains nonzero, so
some code chunks still have unpaired delimiters and need investigation before
claiming fully fence-balanced chunking.

With `k=5` and up to 20 candidate chunks, the AND run scored Recall@5 **0.733**,
nDCG@5 **0.626**, MRR **0.589**, and code hit@5 **4/9**. OR scored Recall@5
**0.600**, nDCG@5 **0.462**, MRR **0.417**, and code hit@5 **3/9**. AND remains
the stronger keyword baseline on this 15-question synthetic set. Reports are
at `evals/reports/keyword-baseline.json` and
`evals/reports/keyword-baseline-or.json`.

**Blockers / resolutions:** The first migration command built a database URL
without escaping reserved characters in the password and failed to resolve
the host. URL-encoding the username/password fixed the connection; the
migration then ran successfully. Ruff lint/format checks could not run because
`ruff` is not installed in the API environment; no lint result is claimed.

**Next:** With fence balance and local M0 checks verified, complete M0 by
checking the hosted GitHub Actions run after the owner authorizes a push; then
continue with M1 PII masking, guardrails, and flagged-chunk filtering.

### 13. Repair fences across chunk windows and establish CI — 2026-11-23

**Goal:** Make every oversized code passage independently renderable, then
establish repeatable lint, unit, migration, and PostgreSQL/pgvector checks.

**What changed:** Investigation of the milestone 12 SQL rows showed that the
58 odd-fence chunks were partial windows cut from long included code examples.
The window splitter now tracks an active fence at both character boundaries,
reopens/closes a fragment as needed, and budgets those added markers inside the
lexical-token cap. Small test windows also use a smaller overlap so progress
does not collapse to one token at a time. Added tests for backtick and tilde
fences. Added Ruff to the dev group, centralized URL construction in
`nimbus_api.config`, made `POSTGRES_*` the canonical source and percent-encoded
each component, and made Alembic load the same configuration. Added a marked
database integration test and a GitHub Actions workflow that checks Ruff,
formatting, unit tests, Alembic migrations, and pgvector integration.

**How we checked it:** The focused chunker suite passed (11 tests). A full
in-memory scan of the pinned snapshot produced 2,265 chunks, maximum
`token_count` 600, zero over-cap chunks, and zero chunks with an odd triple-
backtick count. After re-ingestion, the SQL diagnostic returned 0 odd-fence
chunks, 0 chunks above 600 tokens, and 2,265 total chunks (maximum 600).
`uv sync --project apps/api --locked --all-groups` completed. Ruff lint and
format checks both passed. Unit tests passed (**30 passed, 1 deselected**),
the marked PostgreSQL/pgvector integration test passed (**1 passed**), and
`uv run alembic upgrade head` completed using the shared config. The workflow
has not yet run on GitHub because this work remains uncommitted and unpushed.

**Decision / open question:** `POSTGRES_USER`, `POSTGRES_PASSWORD`, and
`POSTGRES_DB` are the canonical inputs when present. A standalone
`DATABASE_URL` remains supported when those components are absent and must use
percent-encoded credentials. The project has one shared builder for API,
ingestion, evaluation, and migrations.

**Blocker / resolution:** Previously, a manually interpolated migration URL
failed when a password contained reserved URL characters. The shared builder
now percent-encodes user, password, and database separately; unit tests
confirm psycopg parses the original values correctly, and Alembic plus the
database integration check passed locally.

**Hosted CI:** GitHub Actions run `45211237914` passed on commit `5cb2422`.
M1 was committed as `b7279ff`; its hosted CI run `45218348110` passed.

**Next:** Complete local M1 verification, update the data card and report the
proposed commit message without committing until asked.

### 14. Mask PII and add guardrails — 2026-11-23

**Goal:** Reduce sensitive-data exposure in indexed passages, reject common
prompt-injection/unsafe-URL queries, and keep suspicious corpus chunks out of
retrieval.

**What changed:** Added `pii.py` with ordered secret/email/IBAN/card/phone
masking and category counts. Whole expanded documents are masked before
chunking; titles are derived from sanitized text. The 13 hex-secret pattern
occurrences in the FastAPI security examples are masked; example-domain
addresses are preserved. Corpus inspection found two Luhn-valid numeric
identifiers in an ISBN key and a URL path; card matching now excludes these
contexts. No other PII categories matched the corpus.

Added `guardrails.py` with ordered input rejection (empty, length, injection,
unsafe URL, abuse), base64-decoded injection detection, link-local and metadata
URL blocking, and chunk flagging. The search API checks queries before database
access. Migration `0004_chunk_flagged` adds the boolean flag; PostgreSQL search
filters flagged chunks. Processing metadata records `pii-v1` and
`guardrails-v1`.

Fence repair now repeats an included-example's `[Example source: ...]` label
before reopening a fence in a continuation chunk. Its version is
`heading-paragraph-lexical-600-fence-repair-v3`. Regression tests assert all
fragments of a long included example retain their source label. The integration
test derives the expected migration head from `apps/api/alembic.ini`.

**How we checked it:** Hosted CI run `45211237914` passed for commit
`5cb2422`. Local corpus scan found 158 documents / 2,270 chunks, 0 flagged
chunks, and 13 secret masks; no email, phone, or IBAN values were masked. After
re-ingestion the database query confirmed 158 documents, 2,270 chunks, 0
flagged, 0 above 600 tokens, 0 with odd triple-backtick counts, and
`0004_chunk_flagged` as the current migration. Re-ran both retrieval baselines:
AND Recall@5 **0.733**, nDCG@5 **0.626**, MRR **0.589**, code hit@5 **4/9**; OR
Recall@5 **0.667**, nDCG@5 **0.488**, MRR **0.430**, code hit@5 **3/9**.

**Verification commands:** `uv run --project apps/api ruff format --config
apps/api/pyproject.toml apps/api evals`; `uv run --project apps/api ruff
check --config apps/api/pyproject.toml apps/api evals`; unit tests with
`uv run --project apps/api pytest apps/api/tests evals -q -m "not integration"`;
result: **91 passed, 1 deselected**. The marked PostgreSQL/pgvector integration
test passed (**1 passed, 73 deselected**); and both
`evals/run_retrieval.py` baseline invocations. Exact final test totals are
recorded here from the final rerun.

**Decision / open question:** Pattern matching is not a guarantee of complete
PII detection. The current data card describes the actual behavior and
limitations. M3 access evaluation must build cases from every manifest item
with a `question` and compare documents by `source_path`; with the current
synthetic spec this is expected to produce 51 distinct-question cases.

**Blocker / resolution:** The initial card scan also matched an ISBN-like key
and a long numeric URL component as cards. Context-aware exclusions were added,
then the whole corpus scan and re-ingestion reported no card masks.

**Next:** Review the changes and, when explicitly authorized, commit as
`Add PII masking, input guardrails and injection flagging (M1)`.

### 15. Add Nimbus Cloud synthetic corpus and ingestion — 2026-11-23

**Goal:** Add fictional paired regional policies and internal runbooks so
retrieval and access control can be measured without presenting synthetic
material as real service policy.

**What changed:** Added 38 front-matter Markdown files and a manifest under
`data/synthetic/`: 14 public regional policy pages, 6 paired internal regional
runbooks, 7 global internal runbooks, 5 poisoned pages, 5 synthetic PII pages,
and 1 glossary. `evals/ingest_corpus.py --synthetic` validates manifest tags,
front matter, paths, word counts, and pair questions before storage, then
reuses masking, chunking, and flagging. Added manifest/validation tests.

**How we checked it:** Synthetic ingestion loaded **38 documents / 153
chunks** after the realistic-body revision, flagged **5** chunks in the five
poisoned documents, and masked one value in each requested PII category
(card, email, IBAN, phone, secret). SQL
checks found none of the five raw canary values in `chunks.content`; FastAPI
remained at **158 documents / 2,270 chunks / 0 flagged / 13 secret masks**.
Guest retrieval returned 20 public-global results and no regional/internal
result. The synthetic manifest has 17 distinct questions and every pair shares
one exact question.

**Decision / open question:** The first access-evaluation run had recall
**0.882** because two questions were ambiguous against the much larger FastAPI
corpus. Rewording those two questions to match their runbook concepts raised
expected-document recall to **1.000** without changing access rules.

**Blocker / resolution:** None for M2. All five poisoned sources have at least
one flagged chunk, so their content is not returned by normal retrieval.

**Next:** Finish M3 live account-seed/login verification after a local seed
password is configured; do not commit until requested.

### 16. Add login, EdDSA tokens, access-scoped search and access eval — 2026-11-23

**Goal:** Make the caller's verified account region, rather than a body field
or the question text, determine which content can be searched.

**What changed:** Added a single access-rules module, Argon2 password handling,
Ed25519 key generation and EdDSA JWT verification, login and `/me` routes,
strict request models, 401 handling for any invalid presented token, and
persona-scoped retrieval. Added guarded key/user scripts and a manifest-grounded
access evaluator that compares source paths.

**How we checked it:** `uv run --project apps/api ruff format --config
apps/api/pyproject.toml apps/api evals` and the matching `ruff check` both
passed. `uv run --project apps/api pytest apps/api/tests evals -q` passed
**127 tests** (1 integration test deselected); the separately run integration
test passed (**1 passed**). `uv run alembic upgrade head` completed. Access
evaluation: **51 cases, 0 leaks** (guest/R1/R2 each 0), expected-document
recall **1.000**. The API live check returned guest `/me` as 200 and rejected
`Bearer junk` with 401 and `WWW-Authenticate: Bearer`. JWT files were created
with directory mode 0700, private-key mode 0600, and public-key mode 0644.

**Hosted CI:** GitHub Actions run number 3 (`45228066997`) passed for commit
`e2ed82a` (M3).

**2026-11-24 follow-ups:** All 38 synthetic bodies were rewritten as
topic-specific hosting documentation with their payloads, front matter,
manifest values, and final disclaimer preserved. The validator rejects bodies
containing `canary` or `retrieval exercise`; the pair test now verifies that
regional files differ on exactly one fact line. Synthetic re-ingestion loaded
38 documents / 153 chunks, flagged 5 poisoned chunks, and masked one synthetic
value in each PII category. The access evaluation again reported 51 cases, 0
leaks, and 1.000 expected-document recall.

Migration `0005_users_email_lower_unique` adds a unique index on
`lower(users.email)` and fails with a remediation message if case-normalized
duplicates exist. The database was upgraded to this head, and the integration
test verifies the index. Auth tests cover missing/unreadable key files as 503,
bad tokens as 401, and cached settings with explicit cache clearing.

The first seed attempt exited 2 because the local `SEED_PASSWORD` was missing
or shorter than 12 characters. After the owner configured a valid value
locally, `uv run --project apps/api python scripts/seed_users.py` seeded or
updated three accounts. Live API checks returned login **200**, `/me` **200`
with persona **R1**, and wrong-password login **401**. The password was never
displayed or recorded.

**Decision / open question:** Guests use the global-public scope; R1/R2 users
also see internal content for their own region. A token's signed region is
authoritative. No answer-generation model or vector search is included yet.

**Blocker / resolution:** The initial seed attempt was blocked by the missing
or too-short local `SEED_PASSWORD`. The owner configured a qualifying value
locally; the seed script then upserted all three demo users. Live R1 login,
`/me`, and wrong-password behavior were verified as 200/R1/401. No credential
was exposed in output or documentation. No blocker remains for Part A.

**Next:** Part A is verified. Review its uncommitted changes before starting
Part B (M4); do not commit until asked.

### 17. Start real-question evaluation data collection (M4) — 2026-11-24

**Goal:** Build a reproducible, separately reported retrieval evaluation set
from real FastAPI questions without committing raw third-party post text or
inventing owner labels.

**What changed:** Added `evals/collect_questions.py`, offline fixture tests,
owner-confirmed Markdown batch format, a gated `scripts/build_real_dataset.py`,
dataset validation, real-question schema fields, and evaluation instructions.
Added ADR 002 explaining paraphrases and source attribution. Prepared the first
25 review proposals in `evals/labeling/batch-01.md`.

**How we checked it:** The Stack Exchange API collector fetched and cached two
pages under ignored `data/raw/questions/`, and produced **189 candidates** on
2026-11-24. The offline collector/workflow tests passed (**16 passed** in the
targeted run). GitHub Discussions was not queried because `GH_TOKEN` was not
available. Raw responses and candidate excerpts are ignored and were not
staged. No real or unanswerable dataset rows have been exported.

**Decision / open question:** Candidate labels are proposals only. The owner
must check every paraphrase, answerability decision, and relevant pinned page,
then tick each row. The builder ignores unticked candidates. Real AND/OR
baselines, short-query results, and the M4 target counts remain pending those
human confirmations; no retrieval score is claimed for real questions.

**Blocker / resolution:** Human confirmation is an intentional quality gate,
not a software failure. The first 25 candidates are ready for review. This
session stops here so labels are not inferred on the owner's behalf.

**Next:** Review `evals/labeling/batch-01.md`, edit the proposed JSON labels,
and tick only confirmed rows. Continue with subsequent batches after the first
batch is reviewed. Do not commit until asked.

### 18. Adopt the seven-step evaluation process (docs only) — 2026-11-24

**Goal:** Make Nimbus evaluation a documented feedback loop with human-verified
data, calibrated judging, reproducible comparisons, and trace privacy.

**What changed:** Added `docs/EVAL_PROCESS.md` with purpose, artifacts, and exit
criteria for each of seven steps. Updated `docs/IMPLEMENTATION_PLAN.md` with
M4b, M4 key facts, judge calibration, V2 benchmark/error coding, M11 monitoring,
M12 final evaluation, the Week 2 sequence, and the ~8-hour Core increase. Added
error-analysis and synthetic-dimension templates, ignored `evals/traces/`, and
linked the process from the data card. No evaluation code or datasets changed.

**How we checked it:** A structural check confirmed all seven sections have
purpose/artifacts/exit criteria, every template exists, `evals/traces/` is
ignored, and there are no trace files. `git diff --check` passed. The required
commands returned:

- `uv run --project apps/api ruff format --config apps/api/pyproject.toml apps/api evals` — **39 files left unchanged**.
- `uv run --project apps/api ruff check --config apps/api/pyproject.toml apps/api evals` — **all checks passed**.
- `uv run --project apps/api pytest apps/api/tests evals -q` — **145 passed, 1 deselected**.

**Decision / open question:** Keep v0, first error coding, and judge calibration
in Core. If time is short, move expansion beyond 40 synthetic tuples and
automated weekly sampling to Should have. The requested commit is only
proposed; no commit was made.

**Blocker / resolution:** None for this docs-only change. M4 labels remain
owner-confirmation-gated as recorded in milestone 17.

**Next:** Implement milestones in the new plan; begin with owner review of M4
labels, then M4b v0 and immediate error coding.

### 19. Ticket Agent spec + harness plan (docs only) — 2026-11-24

**Goal:** Specify a safe, catalog-driven ticket handoff and extend the planned
evaluation harness to test stateful agents, not just retrieval outputs.

**What changed:** Added `docs/specs/ticket-agent.md` (A1–A5) and the six-topic
`data/tickets/topics.yaml` catalog. Added the Harness section (B1–B11) to
`docs/EVAL_PROCESS.md`, including task/trial terms, regression/capability
suites, graders, grader self-tests, simulated-user behavior, isolation, report
fields, and a YAML task template. Updated the plan for M4b harness core, M7
answers suite, M9 schema/tools, M10 form UI, M12 agent evaluation, and the
budget trade-off; ignored `evals/transcripts/`. This change is docs/config only;
no harness or Ticket Agent code was implemented.

**How we checked it:** PyYAML parsed the catalog; six topic IDs are unique,
every topic has at most two fields, and all catalog field types are among
`text`, `textarea`, and `select`. Structural checks found A1–A5 and B1–B11,
verified the plan updates and transcript ignore, and found no transcript files.
`git diff --check` passed. Ruff format left **39 files unchanged**, Ruff check
passed, and pytest reported **145 passed, 1 deselected**.

**Decision / open question:** The ticket catalog and harness are specifications
only; implementation remains in M4b/M7/M9/M10/M12. The adjusted Core estimate
is **48–56 hours**, approximately **8–16 hours above** the original 32–40-hour
budget. Preserve the prior cut line: keep v0/error coding/calibration Core;
move expansion beyond 40 synthetic tuples and automated weekly sampling to
Should have.

**Blocker / resolution:** None for this documentation/configuration change.

**Next:** Implement the plan in milestone order, starting with owner-confirmed
M4 labels and M4b v0/harness. No commit was made. Proposed commit:
`Add Ticket Agent spec, topic catalog and eval harness plan`.

## Concepts in plain language

- **Corpus:** the collection of documents Nimbus is allowed to search.
- **Chunk:** one passage cut from a source document for retrieval.
- **Embedding input:** the exact text that a future embedding model will turn
  into a vector. Nimbus adds title/heading context but keeps the original text
  separately.
- **Retrieval:** finding and ranking passages relevant to a question.
- **Evaluation:** comparing the retrieved source pages with manually labeled
  relevant pages to see whether retrieval changes helped.
- **RAG:** retrieval-augmented generation. Nimbus has begun the retrieval part;
  it does not yet generate answers grounded in retrieved passages.

## Learning notes

This is a lightweight record of concepts the project owner asks about and may
want to revisit. Questions help us identify what should be explained clearly;
they are not a judgment about the learner. This is not a transcript: omit
incidental questions, credentials, and personal information. Add a short
explanation and a concrete Nimbus example when available.

### 2026-11-22 — Chunking quality and validation

- **Question:** How can we tell whether chunks were split at sensible places,
  and what chunking strategy did we use?
- **Key idea:** The current baseline groups Markdown paragraphs under headings
  toward a lexical-token target, with an overlapping-window fallback for an
  oversized paragraph. A target alone does not prove good boundaries; compare
  stored chunks with their source and test whether related context stays
  together. The table-size and unresolved-include findings are tracked above.
- **Nimbus example:** The 34 inspected FastAPI documentation chunks were
  mostly coherent for prose, but exposed dense-table and code-include cases
  that need explicit handling and verification.

### 2026-11-22 — Keyword search, BM25, and PostgreSQL

- **Question:** Is the current search keyword search, and is it BM25? Is BM25
  specific to PostgreSQL?
- **Key idea:** Nimbus currently uses PostgreSQL full-text query and ranking
  (`plainto_tsquery` with `ts_rank_cd`): it is lexical keyword retrieval, but
  not BM25. BM25 is a ranking function used by multiple search systems, not a
  PostgreSQL-only concept. Evaluation can compare approaches on the same
  labeled questions.

### 2026-11-22 — Parsing versus chunking

- **Question:** Why did we not parse documents before chunking, and how are
  those steps different?
- **Key idea:** Parsing extracts structured text and metadata from a source;
  chunking divides extracted content into retrieval-sized passages. The
  current Markdown ingestion reads Markdown and groups its content; it is not
  a general-purpose parser for PDFs or other formats. Revisit parsing if the
  corpus expands to formats that need it.

### 2026-11-22 — Tables in the corpus

- **Question:** How many tables are in the source corpus?
- **Answer:** A scan for standard pipe-style Markdown table separators found
  tables on two pages: `tutorial/metadata.md` and `advanced/opentelemetry.md`.
  This does not count HTML tables or other tabular formatting. The oversized
  chunk scan also showed that tables are not the main source of target
  violations; most are from the long `release-notes.md` page.

### 2026-11-22 — Choosing a corpus for the capstone

- **Question:** Should Nimbus keep using FastAPI documentation, or switch to
  another dataset?
- **Key idea:** Dataset suitability depends on the claim the capstone needs to
  support. FastAPI docs are a reproducible public documentation-Q&A corpus and
  are useful for building and comparing retrieval. They do not, by themselves,
  demonstrate quality on a realistic company support desk or private policies.
- **Nimbus direction:** Keep the pinned FastAPI corpus as the development and
  retrieval benchmark for now; consider adding a small, clearly labeled
  synthetic support-policy corpus later if the capstone needs to demonstrate
  that use case. Evaluate the two domains separately rather than mixing them
  into one score.

### 2026-11-22 — Resolving included code examples

- **Question:** How can we make code examples referenced by Markdown include
  directives available to retrieval?
- **Key idea:** During ingestion, recognize standalone FastAPI directive lines
  (`{* ../../docs_src/... *}`), resolve them relative to the pinned checkout's
  `docs/en` directory, and allow only files under its `docs_src/` or
  `fastapi/` directories.
  Replace the directive with a fenced code block and a source-path label; the
  `hl[...]` annotation marks highlighted lines in the rendered docs and does
  not mean other source lines should be omitted from retrieval.
- **Safety and verification:** The resolver is implemented and tested. It
  rejects missing or escaping paths and supports the upstream annotations.
  Re-ingestion confirmed the `tutorial/body.md` example is stored as code and
  its literal include directive is gone.

## Next milestones

1. Implement vector retrieval and compare it with the unchanged AND baseline
   using source-page and code-passage metrics.
2. Choose an embedding model and record its revision, vector dimensions,
   normalization, and cost/device constraints before generating vectors.
3. Implement vector retrieval and compare it with the keyword baseline.
4. Add answer generation that uses retrieved passages, then evaluate grounding
   and abstention separately from retrieval quality.
5. Expand the evaluation set with real, appropriately approved support
   questions and human-verified source labels.

## Entry template for future milestones

Copy this section at the end of the file when a meaningful step is complete:

```markdown
### N. Short milestone name — YYYY-MM-DD

**Goal:** What problem were we trying to solve?

**What changed:** Which feature/files changed, in plain language?

**Why:** What concept or trade-off motivated the change?

**How we checked it:** Commands, tests, or manual checks actually run, and the
observed result.

**Decision / open question:** What was decided, and what remains unresolved?

**Blocker / resolution:** Evidence and impact of any blocker; status; if
resolved, the fix and how it was verified. Write “None” if there was no blocker.

**Next:** The next small project step.
```
