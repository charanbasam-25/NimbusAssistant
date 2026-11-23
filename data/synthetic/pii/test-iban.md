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
This fictional privacy fixture checks that a checksum-valid IBAN-shaped value is removed before a synthetic document becomes searchable. It presents the value in a billing-support context because financial identifiers can otherwise be copied into tickets or indexed alongside unrelated instructions.

Synthetic test IBAN: GB82 WEST 1234 5698 7654 32.

The sample is included for automated validation only and must not be used for a payment, bank transfer, or customer lookup. Support staff should request an invoice reference rather than a complete account identifier. After ingestion, the chunk should contain the standard IBAN marker, while the raw value should be absent from searchable content. This fixture makes that behavior repeatable without using a real person's financial information.

Synthetic document for Nimbus capstone testing. Not real policy.
