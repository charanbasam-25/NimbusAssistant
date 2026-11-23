---
id: incident-comms-r1
title: Internal Incident Communications Runbook (R1)
audience: internal
region: R1
kind: runbook
pair: incident-comms
canary_facts:
  notification_timing: Notify in 15 minutes
---
This internal Nimbus Cloud incident-communications runbook helps the response lead coordinate updates for an affected hosted FastAPI workspace. Verify the incident scope and customer impact before sending a status message. Use the approved incident channel, identify what is known, and separate confirmed facts from estimates. The timing below is the region-specific canary used by this capstone test; it is not a real service commitment or an instruction for a live incident.

The first update should explain the affected service, current mitigation, and when the next update is expected. Do not include secrets, private payloads, or unverified root-cause claims. Record the message timestamp and link to the incident record so another responder can continue communications. If facts change, publish a correction that preserves the prior update for auditability.

Canary fact: the fictional R1 response team sends its initial incident notification within 15 minutes.

Synthetic document for Nimbus capstone testing. Not real policy.
