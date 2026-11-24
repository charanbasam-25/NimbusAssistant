# Nimbus evaluation process

Evaluation is a **loop**, not a one-way checklist. Try the simplest end-to-end
system first, inspect its failures, then build only the labels and synthetic
cases needed to measure those failures. Every fixed failure should return as a
regression row in the golden or synthetic set. Repeat error coding after each
meaningful variant and feed the findings into later monitoring.

```text
1 Try v0 -> 2 Golden dataset -> 3 Calibrate judge -> 4 Expand synthetic
     |                                                  |
     +-> 6 Error coding <-------------------------------+
              |                           5 Benchmark <-+
              +-- regression rows ---------------------> 2 / 4
              +-- failure categories ------------------> 3 / 4
7 Monitor -> sampled traces -> owner review -> 6 -> regression rows -> 2 / 4
```

Error coding runs once immediately after v0 as well as after later runs. At
that first pass, v0's mistakes decide which judge criteria and synthetic
dimensions are worth building. No evaluation metric is treated as trustworthy
until its labels and judge are validated.

## 1. Try v0

**Purpose:** Establish a minimal end-to-end answer baseline before investing in
more retrieval or evaluation machinery. Use PostgreSQL keyword search in OR
mode, retrieve up to 20 candidate chunks, collapse to the top 5 pages and use
their chunks as context. Add a basic grounded prompt and make one chat call via
the OpenAI-compatible settings `LLM_BASE_URL`, `LLM_MODEL`, and `LLM_API_KEY`
(Ollama on the Mac is the initial runtime). Run as `guest` only and use about
30–50 owner-confirmed answerable M4 questions.

**Artifacts:** Minimal reusable `llm.py` adapter with a timeout and `FakeLLM`
for tests; a versioned prompt; `evals/run_v0.py`; one JSONL trace per question
under `evals/traces/<run_id>.jsonl`, containing question ID, retrieved chunk
IDs and scores, prompt version, model, answer, and latency. Trace files are
local and Git-ignored. Protect trace text as sensitive; do not put raw
question/answer content in logs or metrics.

**Exit criterion:** The owner has read every v0 answer and step 6 error coding
has been completed once on those answers. Runtime is proved by Ollama returning
an answer on the Mac.

## 2. Golden dataset

**Purpose:** Create trusted, human-reviewed examples for answerable retrieval,
abstention, short-query behavior, and answer facts.

**Artifacts:** The M4 files `evals/datasets/retrieval_real.jsonl` (at least 100
confirmed answerable questions), `unanswerable_real.jsonl` (at least 15
confirmed unanswerable questions), and approximately 25 short queries. Add
`expected_key_facts` to about 40 answerable rows: one to three concise facts
that an answer must state, confirmed by the owner. Keep real and synthetic
records separate; preserve source URLs, license, paraphrase notes, and label
status.

**Exit criterion:** Dataset validation passes, every relevant source path is in
the pinned corpus, labels are owner-confirmed, and real and synthetic datasets
are not mixed. Keep short-query provenance honest: exact user wording can be
real; a shortened title written by us is synthetic and cites its source.

## 3. Calibrate the judge

**Purpose:** Measure whether an automated judge agrees with human judgments
before using judge scores as evidence.

**Artifacts:** Start with one binary pass/fail judge for faithfulness: every
answer claim must be supported by a cited retrieved chunk. The owner labels
about 50 v0 or later-variant answers in
`evals/datasets/judge_labels.jsonl` with `trace_id`, `question_id`, `criterion`,
`human_label` (`pass` or `fail`), and notes. Include at least 15 fails; if v0
fails too rarely, add answers from a deliberately weak top-1-context variant.
Split development/test 50/50 by a stable hash of `question_id`; use few-shot
examples only from development. Use a judge model different from the answer
model (for example, a Groq 70B judge with an Ollama answerer). Report test-set
TPR and TNR plus bias-corrected pass rate:
`(observed + TNR - 1) / (TPR + TNR - 1)`.

**Exit criterion:** Test TPR and TNR are each at least 0.85 and recorded in
`PROJECT_LOG.md`. Do not report faithfulness numbers as validated before this
gate. If the target is missed, improve the rubric/data and recalibrate.

## 4. Expand synthetic data

**Purpose:** Target the failure categories observed in step 6 with controlled
and reproducible cases, rather than generating arbitrary question volume.

**Artifacts:** `evals/synthetic/dimensions.yaml` defines persona (`guest`,
`R1`, `R2`), intent (`how_to`, `troubleshooting`, `concept`, `comparison`,
`account_action`, `off_topic`), phrasing (`short`, `natural`, `typo`,
`multi_part`, `non_native`), and answerability (`answerable`, `unanswerable`,
`adversarial`). Select at least 40 tuples first, weighted toward observed
failure categories. For answerable tuples, select and read the source page
first, then ask an LLM to draft the question. Store relevant source paths,
generator model, and prompt version. The owner keeps or drops every row.
Synthetic records use `provenance: synthetic` and are reported separately.

**Exit criterion:** At least 40 reviewed rows cover the selected tuples; each
answerable row has a source-first verified relevance label, generation
metadata, and owner keep/drop decision. The grid reflects actual coded failures
and is not mistaken for real-user quality evidence.

## 5. Benchmark

**Purpose:** Compare successive retrieval and answer variants on identical
datasets and pinned versions so improvements and regressions are attributable.

**Artifacts:** Benchmark `v0-keyword`, vector retrieval (M5), hybrid RRF
(M6), then reranking and sibling-chunk variants. Write
`evals/reports/benchmark-<variant>.json` with a config block containing
`CHUNKER_VERSION`, PII/guardrail versions, embedding spec, RRF weights,
reranker, LLM and judge models, prompt version, and dataset SHA-256. Report
Recall@5, MRR, nDCG@5 over distinct pages, calibrated judge-faithfulness,
key-fact hit rate, abstention on unanswerable questions, access leaks, and
p50/p95 latency. Put the comparison table in `docs/EVAL_RESULTS.md`, with real
question columns first and synthetic results separate.

**Exit criterion:** Each compared variant uses the same labeled dataset and
records its complete reproducibility config. V2 additionally includes one
error-coding sheet for the hybrid variant. Interpret faithfulness only after
step 3's calibration gate.

## 6. Error coding

**Purpose:** Find the first actionable cause of failures, prioritize fixes,
and turn each resolved failure into a regression case. Run this after v0 and
after each later benchmark where enough traces exist.

**Artifacts:** Sample 30–50 traces per run, including every judge fail plus
random passes. First write one free-text note on the first thing that went
wrong (open coding). Then group notes into categories, count them, and fix the
largest category first (axial coding). Store rows in
`evals/error_analysis/<run_id>.csv` using `TEMPLATE.csv`: trace ID, question ID,
variant, pass/fail, open note, category, stage, and fix idea. Stage is one of
`retrieval`, `generation`, `safety`, `access`, or `other`. Maintain
`evals/error_analysis/codes.md` with category definitions, an example trace ID,
and per-run counts. Starter categories are `wrong_page`,
`right_page_wrong_chunk`, `split_code_example`, `ignores_context`,
`over_abstains`, `under_abstains`, `bad_citation`, and `region_confusion`; revise
them to fit observed traces. Every fixed failure becomes a golden or synthetic
regression row.

**Exit criterion:** The run has a reviewed sample, coded counts by category,
one prioritized top-category fix, and regression rows for resolved failures.
For the first v0 pass, this is also a prerequisite to leaving step 1.

## 7. Monitor (M11)

**Purpose:** Detect quality and safety drift after the system is in use, and
route observed failures back into the same error-coding and regression loop.

**Artifacts:** Extend existing panels/alerts with a weekly stratified sample of
20 live traces: all thumbs-down, abstained, low-retrieval-score, plus random
examples. A calibrated judge scores the sample, then the owner reviews it and
adds observed categories to step 6. Add Grafana panels for sample judge pass
rate and weekly failure-category counts. Raw question/answer text must remain
absent from normal logs and metrics. Reviewed text goes only to a separate,
PII-masked, admin-only `trace_review` table and is deleted after 14 days.

**Exit criterion:** The weekly sampling, calibrated judging, owner review,
retention/deletion, and two Grafana panels have been verified. New failures
flow back to step 6 and become regression rows after fixes.

## Harness

This harness design uses the task/trial/grader/transcript/outcome/suite
vocabulary and outcome-first grading approach described in Anthropic's
[“Demystifying evals for AI agents”](https://www.anthropic.com/research/demystifying-evals-for-ai-agents).
Implementation is planned for M4b and later milestones; this section defines
the contract, not working harness code.

### B1. Terms

- **Task:** one test case with inputs, a reference, and graders.
- **Trial:** one execution of a task.
- **Grader:** one check applied to a transcript or outcome.
- **Transcript:** the saved trace of the interaction.
- **Outcome:** the final state being evaluated, such as the ticket draft in
  Redis.
- **Suite:** a group of related tasks.
- **Harness:** the runner that executes suites consistently and reports the
  results.

### B2. Layout

Build this layout in M4b by adapting `run_retrieval.py` and `run_access.py` into
suites. No files under `evals/harness/` are implemented by this docs-only
specification.

```text
evals/harness/
  task.py
  runner.py
  graders/
  metrics.py
  user_sim.py
  report.py
evals/suites/*.yaml
evals/transcripts/   # local-only; Git-ignored
```

### B3. Regression and capability suites

**Regression** is the CI gate and should remain near 100%:

- `access`: zero leaks.
- `guardrails`, `PII`, and `red-team` safety cases.
- `retrieval_synthetic`: current saturated fixture, recall 1.000.
- `ticket_safety`: never submits, region stays locked, at most two follow-up
  questions.

**Capability** suites measure the quality hill still to climb:

- `retrieval_real`, `answers` (faithfulness and key facts), `abstention`,
  `router`, and `ticket_agent` (topic choice and pre-fill).

When a capability task passes reliably across repeated runs, promote it to the
regression suite. Keep the failure-prone capability cases visible rather than
making the capability suite artificially easy.

### B4. Trials

Use one trial per task during development. In the final M12 run, use three
trials for LLM/agent suites and report both pass@1 and pass^3 (the fraction of
tasks that pass all three trials). Retrieval remains at one trial because it
is deterministic under pinned inputs.

### B5. Graders

Prefer code-based graders where the outcome is objectively checkable. Grade
the final state rather than requiring one exact sequence of tool calls. Tool
constraints are reserved for safety invariants, such as forbidding submission
from the agent. Combine **must-pass** safety graders with weighted graders for
partial credit (for example, one point per correctly filled field). An LLM
rubric grader checks one dimension at a time and may return `unknown`; calibrate
it against human labels using step 3 before treating its score as evidence.

### B6. Grader self-test

Every suite includes a known-good reference solution that must pass and a
known-bad solution that must fail. These catch broken graders before task
scores are trusted. For example, an access evaluator that compares documents
by database ID rather than `source_path` can report zero leaks while never
matching the forbidden-document ground truth; its bad fixture must make that
bug visible.

### B7. Balanced should/shouldn't cases

For each behavior, include both cases where the agent should act and cases
where it should not: abstain, block on guardrails, hand off to a ticket, and
ask a follow-up question. This checks false positives as well as missed
actions; a suite containing only positive examples cannot distinguish a
careful agent from one that always takes the action.

### B8. Simulated user for `ticket_agent`

Use a second LLM as the simulated user, with a task opening message and hidden
facts. It answers only what the agent asks for; when it does not know a value,
it says **“I don't know.”** Limit the simulated conversation to eight turns.
Hidden facts are available to the simulator, not directly to the ticket agent;
this makes invented pre-fill values detectable.

### B9. Trial isolation

Each trial gets a fresh Redis namespace (use `fakeredis` in CI), a rolled-back
database transaction for ticket writes, and no carried-over conversation
state. The corpus is read-only. Isolation prevents a previous task's draft,
ticket, or conversation from making a later task pass accidentally.

### B10. Report fields

Every report records the model, temperature, prompt version, corpus/chunker/
PII/guardrail versions, dataset SHA-256, pass@1, pass^k, weighted/partial-credit
mean, p50/p95 latency, token usage, and estimated (“would-be”) cost. For
deterministic suites with one trial, pass@1 and pass^1 reflect that single run.
Include suite/task counts and grader configuration so the values can be
reproduced and interpreted.

### B11. Example task template

```yaml
id: ticket-deploy-502-r1
suite: ticket_agent
kind: capability
trials: 1
persona: R1
user_sim:
  opening: "My deploy keeps failing with 502 since this morning, I restarted twice"
  hidden_facts:
    app_name: orders-api
    environment: production
reference:
  topic_id: app_error
  queue: platform
  fields:
    app_name: orders-api
    environment: production
graders:
  - type: state_check
    expect:
      topic_id: app_error
      status: draft
      region: R1
      queue: platform
    must_pass: true
  - type: no_invented_values
    must_pass: true
  - type: tool_constraints
    never_called: [submit_ticket]
    max_calls:
      ask_missing_field: 2
    must_pass: true
  - type: fields_match
    weight: 0.7
  - type: llm_rubric
    dimension: clear_and_polite
    weight: 0.3
```
