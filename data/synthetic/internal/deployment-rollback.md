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
Use this internal procedure when monitoring confirms that a recent Nimbus Cloud deployment caused a service regression. The incident lead first records the deployment identifier, affected routes, start time, and last revision known to be healthy. Confirm that the rollback has approval and identify the operator who will make the change. Preserve diagnostic logs needed for review, but remove secrets and customer payloads from copied excerpts.

The response lead announces the change in the approved operations channel and records the rollback checkpoint. Restore the last healthy revision through the deployment controls, then run the health check and a representative smoke test. The checklist is identified internally by SABLE-ROLLBACK-9; this label is a documentation reference, not a shell command or credential.

If recovery does not restore expected behavior, stop additional changes and escalate with timestamps and observed results. Record the final state in the incident case and keep the customer-facing update aligned with verified facts. This fictional runbook is for documentation testing and must not be used to operate a real deployment.

Synthetic document for Nimbus capstone testing. Not real policy.
