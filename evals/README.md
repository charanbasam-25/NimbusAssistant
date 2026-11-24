# Nimbus evaluation harness

Evaluation starts before RAG tuning so changes can be compared with a baseline.

## Retrieval question format

Create `evals/datasets/retrieval.jsonl`, one JSON object per question, following
`evals/schemas/retrieval-question.schema.json`. Keep the question wording intact
and record whether it came from a real user or is synthetic. Do not label
synthetic questions as real.

Example record:

```json
{"id":"synthetic-example-001","query":"How do I declare a request body?","relevant_source_paths":["docs/en/docs/tutorial/body.md"],"persona":"guest","slice":"general","provenance":"synthetic"}
```

`relevant_source_paths` are the source document paths expected to contain the
answer. We use paths rather than database UUIDs so labels remain stable when the
corpus is reloaded. Confirm each path against the pinned corpus before labeling.

## Ingest the pinned corpus

Load the exact commit recorded in `docs/corpus-manifest.json` into PostgreSQL:

```bash
uv --project apps/api run python evals/ingest_corpus.py
```

The command fetches the pinned FastAPI checkout into the Git-ignored
`data/raw/fastapi/` directory, reads only Markdown under the manifest's
documentation root, and stores source pages plus heading-aware chunks as
`public` / `global`. Re-running it updates the same pinned source records.
The JSON report, including source paths and SHA-256 hashes, is written under
`data/processed/` (also Git-ignored). Chunks are not embedded yet; this first
load prepares the corpus for keyword retrieval and later embedding work.

## Keyword baseline

The initial baseline uses PostgreSQL English full-text search (`tsvector` and
`ts_rank_cd`) over the chunks table. It applies the same audience and region
filter used by retrieval, then ranks source documents by their best matching
chunk. Later retrieval implementations can be measured against the same labels
and metrics.

The same retrieval function is available through FastAPI:

```bash
curl -X POST http://localhost:8000/v1/retrieval/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"FastAPI request body Pydantic model","limit":5}'
```

The response includes passage text, heading, source path/URL, document and chunk
IDs, pinned source commit, and a full-text rank score. The score is a ranking
signal, not confidence. This baseline returns evidence only; it does not call an
LLM or generate an answer. `evals/datasets/retrieval.jsonl` is a small synthetic
starter dataset; synthetic results must not be reported as real user-question
quality.

The public API route currently searches only as `guest`: callers cannot claim
an R1/R2 persona until Nimbus has an authenticated identity to determine it.

### What a Nimbus chunk record contains

The cohort's record is a template, so Nimbus maps it to its current single-corpus
design rather than adding its sample tenant and role policy:

- `source_id` is the document's source path; `source_rev` is the pinned source
  commit. The database also keeps its own UUID document ID.
- `chunk_id` is the database chunk UUID; `record_id` is a readable path/commit/
  ordinal identifier. `content` is the original passage text.
- `embedding_input` combines the document title, heading (when present), and
  passage text. That is the text a future embedding model should encode.
- `content_hash` is a SHA-256 hash of the original passage. `processing` records
  parser/chunker versions so we can identify how it was produced.
- `embedding` uses Nimbus's existing 384-dimensional pgvector column, and
  `embedding_spec` will identify the model/settings once we generate vectors.
  Both remain empty until that embedding step.
- `classification` maps to Nimbus's existing `audience` and `region` tags.
  `tenant_id` and `allowed_roles` are intentionally not added: they are not part
  of the current corpus/access design. The API searches only public/global docs.

Chunking groups Markdown paragraphs under their headings, with a hard cap of
600 regex-counted lexical tokens. Only oversized paragraphs are split, using
up to 80 lexical tokens of overlap and preferring line boundaries where
possible. Regression tests are in `evals/test_ingest_corpus.py`; run them with:

```bash
uv run --project apps/api pytest evals/test_ingest_corpus.py
```

The ingestion step also expands standalone FastAPI code-include directives
from the pinned checkout. It accepts only source paths under `docs_src/` or
`fastapi/`, and rejects missing files or paths outside those directories. The
resolver supports upstream `hl[...]`, `ln[...]`, and `title[...]` annotations;
highlight annotations do not filter out the rest of the source file.

The resolver and chunker were simulated against all 158 included files from
the pinned corpus: 455 includes expanded to 2,270 chunks, with none above 600
tokens. The corpus was re-ingested, so these are now the database chunks as
well. Chunk-size settings remain a baseline, not a proven optimum; code-answer
retrieval still needs to be checked against evaluation questions.

Run from the repository root after ingestion and after creating the labeled
dataset:

```bash
uv --project apps/api run python evals/run_retrieval.py \
  --dataset evals/datasets/retrieval.jsonl \
  --query-mode and \
  --output evals/reports/keyword-baseline.json
```

Use `--query-mode or` to run the experimental any-term matcher. The current
15-question synthetic comparison favored the default AND matcher overall, so
OR remains an evaluation option and is not used by the API.

By default, the page metric uses 5 distinct pages selected from up to 20
candidate chunks. To compare a smaller pool, pass `--candidates 5` explicitly.

The runner reads database settings from the root `.env` file. It reports
Recall@5, nDCG@5, and MRR overall, by provenance, and for the `short_query`
slice. Metrics are calculated at source-document level using binary relevance.
It fetches up to 20 ranked candidate chunks (configurable with
`--candidates`, which must be at least `--k`) and then keeps each page's best
rank, so multiple chunks from one page do not consume multiple top-k slots.
The report records the number of candidate chunks considered per question.
Code-example hit@k is intentionally still calculated over the first k chunks,
not the collapsed page list, because its label identifies an expected passage.

Questions can optionally include `expected_code_sources`, a list of source
paths expected inside returned code passages. For those rows, the report adds
`code_hit_at_k` per question and a `code_example_summary` hit rate. This is
separate from source-page Recall@k: a page can rank while its relevant code
chunk does not. The starter set has three focused technical-term probes and
six natural-language paraphrases; all are synthetic and are not a substitute
for real user questions.

## Planned suites

- Retrieval versus keyword baseline: 80 labeled questions, at least 60 real.
- Short-query slice: 25 questions, reported separately.
- Grounded answers: 30 questions, faithfulness target >= 0.90, including 10
  human checks.
- Unanswerable questions: 15, abstention target >= 90%.
- Access matrix and spoofing: about 40 cases, zero leaks.
- Red-team cases: 25, all blocked or refused.
- PII masking and log scan: 20 cases, zero PII in logs.
- Ticket handoff, categories, and security: separate suites defined as those
  features are implemented.

The real-question suite is not populated yet. Collect real FastAPI support
questions and their authoritative source pages before reporting capstone quality
results. Synthetic records can validate mechanics but must be reported
separately.

## Real-question collection and labeling (M4)

Collect candidate questions from Stack Overflow's public API (no key is
required for low-volume use). The collector saves raw API pages and excerpts
under Git-ignored `data/raw/questions/`, then writes a deterministic candidate
list:

```bash
uv run --project apps/api python evals/collect_questions.py --pages 2
```

GitHub Discussions is an optional source; it is skipped when `GH_TOKEN` is
absent. Collected rows are candidates, **not evaluation labels**. Review them
in `evals/labeling/batch-NN.md`: edit the proposed label JSON, check relevant
paths against the pinned docs, and tick `- [x] Confirmed` only after owner
review. The dataset builder ignores unticked rows:

```bash
uv run --project apps/api python scripts/build_real_dataset.py \
  evals/labeling/batch-01.md
uv run --project apps/api python evals/validate_real_datasets.py
```

The validator checks unique/non-overlapping IDs, source paths against the
ingestion report, provenance fields, query length, and PII. Unanswerable
questions are stored separately for the later abstention suite. Do not run
real baselines until owner-confirmed answerable labels exist. Then run AND and
OR separately and retain distinct `provenance:real` and
`provenance:synthetic` summaries:

```bash
uv run --project apps/api python evals/run_retrieval.py \
  --dataset evals/datasets/retrieval_real.jsonl --query-mode and \
  --output evals/reports/keyword-baseline-real-and.json
uv run --project apps/api python evals/run_retrieval.py \
  --dataset evals/datasets/retrieval_real.jsonl --query-mode or \
  --output evals/reports/keyword-baseline-real-or.json
```

See [ADR 002](../docs/adr/002-real-evaluation-paraphrases.md) for why the
committed records use paraphrases plus attribution links rather than raw post
text.
