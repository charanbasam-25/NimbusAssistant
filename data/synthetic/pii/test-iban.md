---
id: pii-test-iban
title: Synthetic IBAN Masking Fixture
audience: public
region: global
kind: pii
pair: null
canary_facts:
  pii_type: iban
---
Billing support can investigate a transfer or invoice using the workspace name, invoice reference, transaction date, and amount shown in the account dashboard. Staff should not request a full bank-account identifier in an ordinary support case. If a secure payment workflow needs banking information, the account owner should enter it only through the approved billing interface and confirm the destination before submitting.

Synthetic test IBAN: GB82 WEST 1234 5698 7654 32.

The value above is fictional test data and must not be used for a transfer, account lookup, or payment. Documents retained for search should not expose complete financial identifiers when the number is unnecessary to answer a service question. Use a masked representation in logs and training examples, and direct account owners to the protected billing form when sensitive details must be changed. This page is synthetic operational guidance, not a banking instruction.

Synthetic document for Nimbus capstone testing. Not real policy.
