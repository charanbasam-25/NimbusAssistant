# Corpus data card

## Dataset identity

- **Name:** FastAPI documentation corpus for Nimbus
- **Primary source:** `https://github.com/fastapi/fastapi`
- **Documentation site:** `https://fastapi.tiangolo.com/`
- **License:** MIT
- **Collection method:** shallow Git clone at a pinned commit; extract approved
  documentation files and associated metadata.

## Intended use

Support-question retrieval and cited-answer generation for this capstone only.

## Access labels

Official FastAPI documentation is initially tagged `public` and `global`.
Synthetic fixtures provide separate `internal`, `R1`, and `R2` material to
test access isolation. Every fixture is clearly marked synthetic.

## Composition

- Pinned public FastAPI documentation, tagged
  `public` / `global`.
- 38 synthetic Nimbus Cloud documents with `public` or `internal` audience
  and `global`, `R1`, or `R2` region tags: 14 public regional policy pages, 6
  paired internal regional runbooks, 7 internal global runbooks, 5 poisoned
  fixtures, 5 PII canaries, and 1 glossary.
- **Planned (M4):** a separately labeled set of real support questions with
  source links and license/provenance notes. Questions are evaluation data and
  are not indexed as answer-bearing corpus documents.

## Synthetic layer

The synthetic Nimbus Cloud corpus models a fictional service for hosting
FastAPI applications. Open documentation corpora do not provide matched
regional variants with controlled differences. Paired canary facts make it
possible to measure whether a user can retrieve the other region's information.
The 38 documents loaded to PostgreSQL created 151 chunks. Five poisoned pages
have flagged chunks and are excluded from normal retrieval. Synthetic pages
are labeled fictional and not real policy; they are never presented as real
FastAPI or Nimbus policy.

## Evaluation data

The current retrieval starter set contains synthetic questions and is not
indexed. Paraphrased questions remain evaluation examples only; they are not
added to the source corpus. **Planned (M4):** add approximately 100 real
FastAPI support questions with authoritative source links and recorded
provenance/licensing, and report their scores separately from synthetic data.
The current synthetic access evaluation has 17 distinct questions expanded to
51 persona cases. The observed result is 0 access leaks and 1.000
expected-document recall; this measures the synthetic fixture, not real-user
question quality.

## Personal data handling

The FastAPI and synthetic corpora contain no real personal data. During
ingestion, the expanded document text is masked before chunking. The masker detects API-key
and long-hex secret patterns, non-example email addresses, checksum-valid
IBANs, Luhn-valid card numbers, and phone-number patterns. It preserves
`example.com`, `.org`, and `.net` addresses and rejects invalid IBAN/card
checksums. The pinned corpus was re-ingested with this pipeline: 158
documents / 2,270 chunks, 0 flagged chunks, and 13 secret-pattern masks from
FastAPI security examples. Titles are taken from the masked text. Mask counts are reported by
category; raw sensitive values are not included in that report. This is a
pattern-based defense, not a guarantee that all personal data is detected.
Suspicious prompt-injection or unsafe-URL passages are marked on chunks and
excluded from retrieval; the API rejects suspicious user inputs before search.
The stored rows reflect these masking and flagged-state rules.

## Known limitations

- Retrieval currently uses PostgreSQL full-text keyword search; embeddings,
  vector search, hybrid ranking, and generated answers are **Planned (M5-M7)**.
- Current evaluation questions are synthetic and too few to establish real
  support quality; the real-question set is **Planned (M4)**.
- Authentication and regional access enforcement use verified EdDSA tokens
  and database query filters. The synthetic corpus was ingested after those
  controls and the zero-leak access evaluation were verified. Demo-user seeding
  and live authenticated login remain pending a locally configured
  `SEED_PASSWORD`.
- The current PII rules are pattern-based and may miss unusual formats or
  produce false positives; corpus-specific flagged/masking counts are checked
  during M1 re-ingestion.
- The source snapshot is pinned, so it does not automatically include newer
  FastAPI documentation.

## Exclusions

- Pull requests, issues, and discussions are not indexed.
- Paraphrased questions are evaluation data only, not indexed corpus content.
- User-account data
- Employer material, credentials, and proprietary documentation

## Reproducibility

The corpus manifest will record the upstream URL, selected commit SHA, fetch
date, file list, content hashes, tagging rules, and ingestion result.
