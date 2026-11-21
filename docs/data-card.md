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
Synthetic fixtures will provide separate `internal`, `R1`, and `R2` material to
test access isolation. Every fixture will be clearly marked synthetic.

## Exclusions

- Pull requests, issues, and discussions
- User-account data
- Employer material, credentials, and proprietary documentation

## Reproducibility

The corpus manifest will record the upstream URL, selected commit SHA, fetch
date, file list, content hashes, tagging rules, and ingestion result.
