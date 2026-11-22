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
snapshot of the official FastAPI documentation. The project has a PostgreSQL
keyword-search baseline and evaluation scaffold, but it is **not yet a complete
RAG assistant**: embeddings and answer generation have not been implemented.

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

1. Expand realistic retrieval questions and diagnose query-wording
   sensitivity, especially for code examples.
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
