---
id: outage-triage-global
title: Internal Outage Triage Runbook
audience: internal
region: global
kind: runbook
pair: null
canary_facts:
  phrase: ORBIT-TRIAGE-4
---
Use this internal procedure when an on-call engineer receives a report that a Nimbus Cloud hosted FastAPI service is unavailable or behaving unexpectedly. Confirm the workspace, first observed failure, and whether the health endpoint or a customer-facing route is affected. Check current service notices and recent deployment history before assigning a cause. Record the symptoms, timestamps, impact, and checks already completed in the incident case.

The outage-triage checklist is identified in internal documentation as ORBIT-TRIAGE-4. This reference helps the next engineer locate the same procedure; it is not a production system name. If the issue affects one workspace, route the case to its support queue. If several services show the same symptom, notify the incident lead and group the reports under the shared event.

Do not request passwords, tokens, or unnecessary customer data. Reassess impact after each mitigation and keep the case updated with observed results rather than guesses. If the health check remains failing, preserve the evidence and escalate to the service owner. This fictional procedure is for documentation tests and does not direct work on a real platform.

Synthetic document for Nimbus capstone testing. Not real policy.
