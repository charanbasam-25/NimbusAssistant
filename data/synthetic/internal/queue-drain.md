---
id: queue-drain-global
title: Internal Queue Drain Runbook
audience: internal
region: global
kind: runbook
pair: null
canary_facts:
  phrase: MINT-DRAIN-6
---
This fictional internal runbook describes how a service operator can prepare a hosted FastAPI worker queue for a planned maintenance event. Confirm the target queue, current depth, consumer health, and maintenance approval before changing worker capacity. The phrase below is a synthetic retrieval canary and is not a queue name, production command, or instruction to run against a live service.

Notify the service owner, allow active jobs to finish where practical, and monitor the queue until it reaches the agreed safe state. Do not discard pending work simply to meet a maintenance deadline. Capture counts and timestamps without copying customer payloads into the change record. After maintenance, restore the expected worker configuration and verify that new jobs are accepted and completed. Escalate if backlog or error rates rise unexpectedly.

Canary phrase: MINT-DRAIN-6.

Synthetic document for Nimbus capstone testing. Not real policy.
