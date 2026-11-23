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
**Planned (M2):** synthetic fixtures will provide separate `internal`, `R1`,
and `R2` material to test access isolation. Every fixture will be clearly
marked synthetic.

## Composition

- **Planned (M2):** pinned public FastAPI documentation, tagged
  `public` / `global`.
- **Planned (M2):** synthetic Nimbus Cloud documents with `public` or
  `internal` audience and `global`, `R1`, or `R2` region tags.
- **Planned (M4):** a separately labeled set of real support questions with
  source links and license/provenance notes. Questions are evaluation data and
  are not indexed as answer-bearing corpus documents.

## Synthetic layer

The synthetic Nimbus Cloud corpus models a fictional service for hosting
FastAPI applications. It is planned for M2. Open documentation corpora do not
provide matched regional variants with controlled differences. Paired canary
facts will make it possible to measure whether a user can retrieve the other
region's information. Synthetic pages will be labeled as fictional and not
real policy; they will never be presented as real FastAPI or Nimbus policy.

## Evaluation data

The current retrieval starter set contains synthetic questions and is not
indexed. Paraphrased questions remain evaluation examples only; they are not
added to the source corpus. **Planned (M4):** add approximately 100 real
FastAPI support questions with authoritative source links and recorded
provenance/licensing, and report their scores separately from synthetic data.

## Personal data handling

The current indexed source is public documentation; this project does not
collect private user-account data for the corpus. During ingestion, the
expanded document text is masked before chunking. The masker detects API-key
and long-hex secret patterns, non-example email addresses, checksum-valid
IBANs, Luhn-valid card numbers, and phone-number patterns. It preserves
`example.com`, `.org`, and `.net` addresses and rejects invalid IBAN/card
checksums. Titles are taken from the masked text. Mask counts are reported by
category; raw sensitive values are not included in that report. This is a
pattern-based defense, not a guarantee that all personal data is detected.
Suspicious prompt-injection or unsafe-URL passages are marked on chunks and
excluded from retrieval; the API rejects suspicious user inputs before search.
The current pinned FastAPI corpus must be re-ingested after this feature so the
masking and flagged state is reflected in stored rows.

## Known limitations

- Retrieval currently uses PostgreSQL full-text keyword search; embeddings,
  vector search, hybrid ranking, and generated answers are **Planned (M5-M7)**.
- Current evaluation questions are synthetic and too few to establish real
  support quality; the real-question set is **Planned (M4)**.
- Authentication and regional access enforcement are **Planned (M3)**; no
  regional synthetic content should be loaded or exposed before access controls
  and leak evaluations are verified.
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
