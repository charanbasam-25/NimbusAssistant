# Nimbus implementation plan

Nimbus is a four-week capstone effort, planned at about 8-10 hours per week.
Milestones are complete only after their acceptance checks have actually run.
Track verified outcomes in `PROJECT_LOG.md`; work in progress and the current
session belong in `HANDOFF.md`.

## Milestones

| Milestone | Build | Done when |
| --- | --- | --- |
| M0 | GitHub Actions CI: Ruff, unit tests, integration tests against PostgreSQL/pgvector, and `alembic upgrade head` | CI is green; the transfer brief's Step 3 checks are complete |
| M1 | PII masking, input guardrails, and `chunks.flagged` filtering | 69 tests pass and no FastAPI chunks are flagged |
| M2 | Synthetic Nimbus Cloud corpus, manifest, and ingestion of front-matter access tags | Synthetic sources are ingested with the expected audience/region tags |
| M3 | Login, signed JWTs, access-scoped API, and access evaluation | V1 has zero leaks across 60 cases; 91 tests pass |
| M4 | About 100 real FastAPI questions with provenance and source/license notes | Real evaluation set is committed and reported separately |
| M5-M6 | Embeddings, access-filtered vector search, RRF fusion, cross-encoder reranking, sibling chunks, and no-answer threshold | V2 compares hybrid retrieval with the strongest keyword baseline |
| M7 | LLM adapter, grounded prompt, structured output, citation checks, and abstention | Answers are grounded and cited; retrieved chunk access tags are rechecked |
| M8-M10 | Streaming chat, feedback, rate limits, readiness/metrics endpoints, ticket handoff workflow, and Next.js UI | V3 browser flow works for guest, R1, and R2 personas |
| M11-M13 | Prometheus metrics, Product Insights and Engineering Grafana dashboards, alerts, remaining evaluations, docs, and demo | V4 evaluations and dashboards are complete |

## Implementation strategy

Keep retrieval, policy, and answer logic in a small **pure core**: functions
should take explicit inputs and return explicit outputs, without opening network
connections or reading process-global state themselves. Put database, model,
Redis, and HTTP behavior in **thin adapters** around that core. This makes
policy and ranking logic easy to test without starting services.

Use small fakes for unit tests: `FakeConnection`, `FakeLLM`, `FakeEmbedder`,
and `fakeredis` for Redis-backed behavior. Add a pytest `integration` marker
for tests that require real PostgreSQL/pgvector or other services; CI should
run those against disposable service containers. Unit tests should remain fast
and deterministic.

## Guardrails for project work

- Never commit until the project owner explicitly asks.
- Do not use employer code, data, prompts, names, or secrets.
- Label synthetic content and synthetic evaluation questions honestly.
- Record only verified outcomes in `PROJECT_LOG.md`; record in-progress work
  and blockers in `HANDOFF.md`.
- Include the exact test/check command and its observed result in completion
  notes. A proposed test is not a passing test.
