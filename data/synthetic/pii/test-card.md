---
id: pii-test-card
title: Synthetic Card Masking Fixture
audience: public
region: global
kind: pii
pair: null
canary_facts:
  pii_type: card
---
This fictional privacy fixture is used to check whether Nimbus masks a payment-card-shaped value before creating searchable chunks. It contains one synthetic test number and no real person's account information. The value appears in a sentence so the ingestion pipeline can verify that detection works across ordinary prose, and any stored passage should contain only a masked representation.

Synthetic test card value: 4111 1111 1111 1111.

The card belongs to a widely used payment-testing range and is not valid payment information for a real transaction. Do not use the example to make a purchase or associate it with an account. The purpose of this page is limited to a deterministic capstone privacy check. Its title and tags identify it as synthetic test content rather than a policy document.

Synthetic document for Nimbus capstone testing. Not real policy.
