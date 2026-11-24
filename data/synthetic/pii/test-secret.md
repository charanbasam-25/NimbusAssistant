---
id: pii-test-secret
title: Synthetic Secret Masking Fixture
audience: public
region: global
kind: pii
pair: null
canary_facts:
  pii_type: secret
---
Deployments may require API credentials to connect a hosted FastAPI service to an external integration. Store those values in the platform's managed secret settings and reference them by configuration name; do not place credentials in source code, support tickets, screenshots, or ordinary environment notes. If a secret appears in a shared diagnostic export, revoke or rotate it through the issuing service and review where the value may have been copied.

Synthetic test key: sk-test0123456789abcdefXYZ.

This string is fictional test text and does not grant access to any service. It must not be used for authentication or replaced with a real credential. Searchable support documents should contain a mask where a secret was detected, while ingestion reports retain only the category count. These security notes describe a synthetic hosting platform and are not an actual Nimbus Cloud policy or credential-management service.

Synthetic document for Nimbus capstone testing. Not real policy.
