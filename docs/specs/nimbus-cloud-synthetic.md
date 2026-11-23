# Nimbus Cloud synthetic corpus specification

**Status:** Implemented and ingested (M2); access-evaluated (M3). This describes fictional test data; it is not a
statement of real Nimbus Cloud or FastAPI policy.

## Purpose

Nimbus Cloud is a fictional hosting platform used to test retrieval and access
control. Public FastAPI docs have no matched R1/R2 policy variants, so paired
synthetic documents provide controlled canary facts: the answer changes by
region, and an access test can check that the other region's canary never leaks.

## Document format

Each Markdown document begins with front matter containing `id`, `title`,
`audience`, `region`, `kind`, `pair`, and `canary_facts`. The manifest records
the document ID, source path, shared evaluation question for a pair, and
expected canary metadata. Paired files are identical except for their
region-specific canary facts. Each file ends with the sentence:

> Synthetic document for Nimbus capstone testing. Not real policy.

The ingest pipeline must preserve these fields as document metadata and must
not treat front matter as answer text.

## Manifest JSON shape

The manifest is a JSON object with a schema version, corpus identifier, and a
`documents` array. Each entry identifies one Markdown file, repeats its access
labels for validation, and carries the evaluation question. The two entries in
a regional pair must use the exact same `question` string; only region-specific
metadata and expected canary facts differ.

```json
{
  "schema_version": 1,
  "corpus_id": "nimbus-cloud-synthetic",
  "documents": [
    {
      "id": "escalation-runbook-r1",
      "source_path": "internal/escalation-runbook-r1.md",
      "title": "Internal Escalation Runbook (R1)",
      "audience": "internal",
      "region": "R1",
      "kind": "runbook",
      "pair": "escalation-runbook",
      "question": "Which escalation identifier applies to the internal support team in this region?",
      "expected_canary_facts": { "identifier": "CEDAR-7" }
    },
    {
      "id": "escalation-runbook-r2",
      "source_path": "internal/escalation-runbook-r2.md",
      "title": "Internal Escalation Runbook (R2)",
      "audience": "internal",
      "region": "R2",
      "kind": "runbook",
      "pair": "escalation-runbook",
      "question": "Which escalation identifier applies to the internal support team in this region?",
      "expected_canary_facts": { "identifier": "LINDEN-4" }
    },
    {
      "id": "deployment-rollback-global",
      "source_path": "internal/deployment-rollback.md",
      "title": "Internal Deployment Rollback Runbook",
      "audience": "internal",
      "region": "global",
      "kind": "runbook",
      "pair": null,
      "question": "Which distinctive phrase starts the fictional deployment rollback checklist?",
      "expected_canary_facts": { "phrase": "SABLE-ROLLBACK-9" }
    }
  ]
}
```

Each entry has these required fields: `id`, `source_path`, `title`, `audience`,
`region`, `kind`, `pair`, `question`, and `expected_canary_facts`. `pair` is
`null` for a global-only runbook. `question` is used to build an evaluation
case; it is not indexed as document content. `expected_canary_facts` lets the
access evaluation check the right regional answer without relying only on
retrieved document IDs.

## Paired public documents

| Pair | R1 canary | R2 canary |
| --- | --- | --- |
| `refund-policy` | Refund within 14 days | Refund within 30 days |
| `support-hours` | 08:00-20:00 Eastern | 08:00-18:00 CET |
| `data-residency` | `nc-us-1` | `nc-eu-1` |
| `starter-plan-price` | $9/month | EUR 10/month, including VAT |
| `backup-retention` | 7 days | 35 days |
| `sla-credits` | 10% for availability below 99.9% | 25% for availability below 99.95% |
| `payment-methods` | ACH | SEPA |

## Internal documents

The brief calls for 10 internal runbook topics: three region-paired topics
(six files) and seven global-only topics (seven files), for 13 Markdown files
total. This interprets “10 runbooks” as 10 logical topics. Every topic has a
retrieval question; paired files share exactly the same question so the R1/R2
test changes only the authenticated persona and expected canary.

| Pair | R1 canary | R2 canary |
| --- | --- | --- |
| `escalation-runbook` | Cedar, `CEDAR-7` | Linden, `LINDEN-4` |
| `incident-comms` | Notify in 15 minutes | Notify in 30 minutes and provide 72-hour notice |
| `account-deletion` | Delete after 30 days | Delete after 14 days and retain a GDPR audit log |

The three shared questions are:

- `escalation-runbook`: “Which escalation identifier applies to the internal
  support team in this region?”
- `incident-comms`: “What incident-notification timing applies to the internal
  team in this region?”
- `account-deletion`: “What deletion and audit-retention rules apply in this
  region?”

The seven global-only runbooks must be clearly fictional, useful for
internal-only access tests, and have a unique phrase and question each:

| Runbook topic | Distinctive phrase | Evaluation question |
| --- | --- | --- |
| `deployment-rollback` | `SABLE-ROLLBACK-9` | Which distinctive phrase starts the fictional deployment rollback checklist? |
| `outage-triage` | `ORBIT-TRIAGE-4` | Which phrase identifies the internal outage-triage checklist? |
| `credential-rotation` | `COBALT-ROTATE-2` | Which phrase marks completion of the fictional credential-rotation procedure? |
| `queue-drain` | `MINT-DRAIN-6` | Which phrase should an engineer use to verify the internal queue-drain runbook? |
| `billing-adjustment` | `KITE-ADJUST-3` | Which phrase identifies the internal billing-adjustment procedure? |
| `backup-restore` | `EMBER-RESTORE-8` | Which phrase signals the fictional backup-restore checklist? |
| `service-retirement` | `LANTERN-RETIRE-5` | Which phrase identifies the internal service-retirement runbook? |

## Adversarial and privacy test fixtures

The corpus contains five poisoned documents, each containing one isolated test case: a hidden
"ignore instructions" comment, fake admin-mode instructions, a false 90-day
refund claim, a metadata-service URL, and a base64-encoded instruction. Plan
five separate PII/secret canary documents containing only synthetic values: a
test card number, fictional email, reserved/example phone, test IBAN, and
obviously fake API-key-shaped string. A glossary document must be indexed for
retrieval tests but marked so it is never cited as an authoritative answer.

These fixtures are synthetic and must not be used as live policy. M1
guardrails, PII masking, flagged-chunk filtering, and M3 access controls are
implemented; the M3 access evaluation reports 51 cases, 0 leaks, and 1.000
expected-document recall. Demo-user seeding and a live authenticated login
check remain pending a local `SEED_PASSWORD`.
