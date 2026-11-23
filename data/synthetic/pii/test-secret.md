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
This fictional security fixture verifies that an API-key-shaped string is masked before it can enter the searchable Nimbus corpus. A developer reviewing a hosted FastAPI deployment should store credentials in a managed secret facility and rotate them if they are accidentally exposed.

Synthetic test key: sk-test0123456789abcdefXYZ.

The value is intentionally fake and does not grant access to any service. Do not attempt to authenticate with it, place a real key in this file, or use a production credential in the test suite. The expected ingestion result replaces the string with the secret marker and records only the category count. This page is a privacy canary, not a user guide or a real Nimbus Cloud security policy.

Synthetic document for Nimbus capstone testing. Not real policy.
