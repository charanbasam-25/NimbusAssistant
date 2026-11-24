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
Use this runbook before planned maintenance on a Nimbus Cloud worker service. Confirm the target queue, current depth, consumer health, and change approval with the service owner. Schedule the work when incoming traffic is manageable and make sure the on-call engineer can observe the queue throughout the maintenance window. The internal checklist reference is MINT-DRAIN-6; it is documentation metadata, not a queue name or production command.

Notify affected operators, allow active jobs to finish where practical, and monitor the queue until it reaches the approved safe state. Do not discard pending work solely to meet the schedule. Record counts and timestamps in the change case without copying customer payloads. Once maintenance is complete, restore the expected worker capacity and confirm that new jobs are accepted and completed.

If backlog or error rates rise unexpectedly, pause the maintenance and contact the service owner. Capture the observed state and the action taken so the next operator can continue safely. This fictional operational guide is included for documentation testing and is not authorization to change a live queue.

Synthetic document for Nimbus capstone testing. Not real policy.
