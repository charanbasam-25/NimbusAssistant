# Nimbus Cloud synthetic corpus specification

**Status:** Planned (M2). This describes fictional test data; it is not a
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

Create 10 global internal runbooks, each with a distinctive phrase so tests can
identify the correct document. Three paired topics use these facts:

| Pair | R1 canary | R2 canary |
| --- | --- | --- |
| `escalation-runbook` | Cedar, `CEDAR-7` | Linden, `LINDEN-4` |
| `incident-comms` | Notify in 15 minutes | Notify in 30 minutes and provide 72-hour notice |
| `account-deletion` | Delete after 30 days | Delete after 14 days and retain a GDPR audit log |

The remaining seven global runbooks should be clearly fictional, useful for
internal-only access tests, and each have a unique retrieval phrase.

## Adversarial and privacy test fixtures

Plan five poisoned documents, each containing one isolated test case: a hidden
"ignore instructions" comment, fake admin-mode instructions, a false 90-day
refund claim, a metadata-service URL, and a base64-encoded instruction. Plan
five separate PII/secret canary documents containing only synthetic values: a
test card number, fictional email, reserved/example phone, test IBAN, and
obviously fake API-key-shaped string. A glossary document must be indexed for
retrieval tests but marked so it is never cited as an authoritative answer.

All of these fixtures are planned; do not ingest or use them as live policy.
M1 guardrails, PII masking, flagged-chunk filtering, and M3 access controls
must be implemented and tested before exposing the synthetic corpus through
the API.
