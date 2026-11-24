# ADR 002: Paraphrase real evaluation questions and retain source links

**Status:** Accepted for M4 data collection; labels remain owner-confirmed.

## Context

Nimbus needs realistic questions to evaluate retrieval over a pinned FastAPI
documentation snapshot. Stack Overflow is licensed under CC BY-SA 4.0, and its
posts may contain usernames, personal details, links, code, and long error
traces. Committing raw question bodies would add unnecessary third-party text
and privacy exposure to the repository.

## Decision

Keep raw API responses and candidate excerpts under ignored `data/raw/`. Review
questions are paraphrased into self-contained queries of at most 300
characters. Evaluation records retain the original source URL, license, and an
attribution note. Before export, the owner confirms each query's answerability
and relevant pinned-document paths. Queries containing PII are rejected by
validation. Only confirmed, paraphrased labels are written to the committed
JSONL evaluation datasets; raw post bodies are never indexed into Nimbus.

Short queries are labeled `real` only when the wording is genuinely present in
the source title. If an evaluator shortens a title, the item is marked
`synthetic` and its note identifies the source URL.

## Consequences

- Scores measure retrieval of realistic intents without reproducing complete
  third-party posts in the repository.
- Links and license fields retain attribution/provenance for review.
- Human review is a required data-quality gate; unconfirmed proposals cannot
  enter either evaluation dataset.
- Paraphrase decisions can alter query difficulty, so wording changes and
  provenance remain reviewable in the labeling batches.
