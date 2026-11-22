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
under their headings, up to 600 regex-counted lexical tokens. An oversized
paragraph is split into windows of about 450 words with up to 80 words of
overlap. These are initial settings, not proven optimal settings.

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

## Next milestones

1. Review the chunking choices and decide whether to keep them or compare an
   alternative using the same evaluation questions.
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

**Next:** The next small project step.
```
