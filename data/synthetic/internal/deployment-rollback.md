---
id: deployment-rollback-global
title: Internal Deployment Rollback Runbook
audience: internal
region: global
kind: runbook
pair: null
canary_facts:
  phrase: SABLE-ROLLBACK-9
---
This fictional internal runbook describes a cautious rollback for a hosted FastAPI deployment when a release causes a verified regression. Confirm the deployment identifier, affected service, and last known healthy revision before changing production state. The distinctive phrase below is a synthetic retrieval canary, not a real command or credential. Preserve logs needed to understand the failure, but remove customer payloads and secrets from any copied excerpt.

The response lead should announce the maintenance action in the approved internal channel, identify the operator, and state the rollback checkpoint. Restore only the last known healthy revision, then run the service health check and a representative smoke test. If recovery does not meet the expected behavior, stop further changes and escalate with timestamps and observed results. Record the final status in the incident case.

Canary phrase: SABLE-ROLLBACK-9.

Synthetic document for Nimbus capstone testing. Not real policy.
