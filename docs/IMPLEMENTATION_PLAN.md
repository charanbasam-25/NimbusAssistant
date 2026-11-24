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
| M4 | About 100 owner-confirmed answerable real FastAPI questions, 15+ unanswerable questions, and ~25 short queries; provenance/source/license notes; expected key facts on ~40 answerable rows | Validator passes; real and synthetic sets stay separate; labels and key facts are owner-confirmed |
| M4b | v0 + first error coding (~3 h), plus harness core (~3 h): minimal reusable `llm.py` makes one chat call with a timeout and has `FakeLLM`; `evals/run_v0.py` writes traces; implement harness task/runner, grader self-tests, isolation, and report config | Ollama answers on the Mac; v0 traces are reviewed; reference/bad grader tests pass; one error-coding pass is complete |
| M5-M6 | Embeddings, access-filtered vector search, RRF fusion, cross-encoder reranking, sibling chunks, and no-answer threshold | V2 uses the step-5 benchmark report/config and includes one hybrid-variant error-coding sheet |
| M7 | Reuse `llm.py` for grounded prompt, structured output, citation checks, abstention, calibrated judge (~2 h), and the harness `answers` suite | Judge test TPR/TNR are each >= 0.85 before reporting faithfulness; answers are grounded/cited and access tags rechecked |
| M8 | Streaming chat, feedback, rate limits, readiness/metrics endpoints | V3 service behaviors have tests and metrics |
| M9 | Ticket Agent per [spec](specs/ticket-agent.md) (~1 h): six catalog topics, validated tools/rules, token-locked ownership/access, Redis draft, confirm-only submission; add migration for `topic_id`, `queue`, and `fields JSONB NOT NULL DEFAULT '{}'` | Ticket writes validate ownership/region and route from catalog; submit is possible only through explicit confirm endpoint |
| M10 | Ticket UI (~1 h): topic chips, “None of these”, text/textarea/select form, ✨ pre-filled and 🔒 locked markers, edit and Confirm | Guest/login behavior and complete draft-confirm flow work in browser |
| M11 | Weekly trace sample, separate privacy-controlled `trace_review` storage, and two Grafana panels (+1 h) | Weekly sample is owner-reviewed, PII-masked, admin-only, and deleted after 14 days; panels show judge pass rate and failure categories |
| M12 | Calibrated judges (M7) + dimension-grid synthetic set (step 4) (+2 h); ticket-agent suite with simulated user (~30 balanced tasks, +3 h); benchmark every variant and complete final error coding | Final run uses three trials for agent tasks and reports pass@1/pass^3; final evaluation set, calibrated judge, all variant reports, and final error-coding sheet are verified |
| M13 | Documentation, capstone demo, and final project wrap-up | V4 handoff, demo, and report are complete |

## Implementation strategy

The evaluation method is the loop in [`EVAL_PROCESS.md`](EVAL_PROCESS.md):
try v0, code its failures immediately, build a human-reviewed golden set,
calibrate judges, expand synthetic coverage from observed failures, benchmark
variants, then monitor and feed new failures back into regression data. Do not
report judge-based faithfulness before the calibration gate.

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

## Schedule and scope

The calendar is a working sequence, not a one-way evaluation process. Week 2
now covers M4, M4b, and M5–M7: finish the human-reviewed M4 set, prove the
minimal Ollama v0 and error-code its failures, then proceed through embeddings,
hybrid retrieval, and judge calibration. Later benchmark and monitoring work
continues to feed errors back into the golden and synthetic sets.

The existing Core estimate for the planned implementation is **40–48 h**.
The evaluation, agent, and harness additions contribute about **16 h** total:
the evaluation process adds ~8 h, and the Ticket Agent/harness adds ~8 h (M4b
harness +3, M9 +1, M10 +1, M12 +3). That makes the corrected estimate
**56–64 Core hours**—about **16–24 h above** the original **32–40 h** four-week
budget. Keep v0, first error coding, judge calibration, and ticket safety
constraints in Core because they define the method and protect user data. If
schedule is tight, move synthetic expansion beyond the first 40 tuples and
automation of weekly sampling to **Should have**; do not remove the initial 40
failure-weighted tuples or the first human-reviewed weekly sample.

**Should have:** run the complete regression suites as a CI gate after the
harness is implemented. Capability suites remain an iterative quality hill;
reliably passing tasks graduate into regression. **Better to have:** date
fields, conditional forms, uploads, region-specific help text, and a Langfuse
trace viewer. These are outside the initial Ticket Agent scope.

## Guardrails for project work

- Never commit until the project owner explicitly asks.
- Do not use employer code, data, prompts, names, or secrets.
- Label synthetic content and synthetic evaluation questions honestly.
- Record only verified outcomes in `PROJECT_LOG.md`; record in-progress work
  and blockers in `HANDOFF.md`.
- Include the exact test/check command and its observed result in completion
  notes. A proposed test is not a passing test.
