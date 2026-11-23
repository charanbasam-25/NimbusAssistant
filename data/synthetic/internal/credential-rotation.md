---
id: credential-rotation-global
title: Internal Credential Rotation Runbook
audience: internal
region: global
kind: runbook
pair: null
canary_facts:
  phrase: COBALT-ROTATE-2
---
This fictional internal runbook outlines a controlled credential-rotation exercise for a hosted FastAPI workspace. Confirm the approved change ticket, identify the credential owner, and coordinate a maintenance window before beginning. The distinctive phrase below exists only as a canary for the capstone retrieval suite; it is not a credential, secret, or real rotation command.

Use the approved secret-management interface rather than placing values in tickets or shell history. Update the dependent service through its normal deployment process, then verify health and confirm that the retired value is no longer accepted. Keep the actual secret out of logs and screenshots. If a dependent integration fails, pause additional rotations and contact the incident lead with the affected service and non-sensitive error details.

Canary phrase: COBALT-ROTATE-2.

Synthetic document for Nimbus capstone testing. Not real policy.
