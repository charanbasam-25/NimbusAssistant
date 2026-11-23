---
id: pii-test-email
title: Synthetic Email Masking Fixture
audience: public
region: global
kind: pii
pair: null
canary_facts:
  pii_type: email
---
This fictional privacy fixture checks whether Nimbus masks an email address that does not use one of the preserved example domains. It is written as a short hosting-platform support note so that the value is processed in normal document context rather than as an isolated regex sample.

Synthetic contact address: alex.rivera@mail.nimbus.test.

The address is reserved for this capstone and is not a real mailbox or a way to contact a person. A real support request should use the authenticated account dashboard and should not place personal contact details in public documentation. During ingestion, the expected stored content replaces the address with the standard email marker. This file exists solely to verify that privacy behavior and to provide a reproducible test case.

Synthetic document for Nimbus capstone testing. Not real policy.
