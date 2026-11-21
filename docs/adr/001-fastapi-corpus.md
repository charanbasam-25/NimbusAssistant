# ADR 001: Use FastAPI documentation as the Nimbus corpus

## Status

Accepted - 2026-11-21

## Decision

Nimbus will ingest documentation from the official
[`fastapi/fastapi`](https://github.com/fastapi/fastapi) repository only. The
ingestion process will clone a specific commit and record its SHA in a corpus
manifest.

## Context

The capstone needs a real, open-source documentation corpus that supports
reproducible retrieval experiments and allows a meaningful keyword baseline.
FastAPI has substantial public documentation and is released under the MIT
License.

## Consequences

- Evaluation questions must be answerable from FastAPI documentation.
- Region-specific and internal documents will be synthetic Nimbus fixtures,
  never represented as official FastAPI content.
- We must retain the source commit and license attribution in the data card.
