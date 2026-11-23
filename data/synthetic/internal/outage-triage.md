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
This fictional internal runbook helps an on-call engineer triage a reported outage affecting a hosted FastAPI service. Start by confirming the workspace, the first observed failure, and whether the health endpoint or a customer-facing route is affected. The phrase below is a synthetic canary for retrieval evaluation and must not be treated as an operational system identifier.

Compare the report with current service status and recent deployment history. Record symptoms, timestamps, impact, and checks already completed. Avoid speculative root-cause statements and do not request passwords, tokens, or unnecessary customer data. If the issue is isolated to one workspace, route it to the owning support queue; if several services show the same symptom, notify the incident lead. Reassess impact after each mitigation and keep the internal case updated.

Canary phrase: ORBIT-TRIAGE-4.

Synthetic document for Nimbus capstone testing. Not real policy.
