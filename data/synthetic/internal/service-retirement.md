---
id: service-retirement-global
title: Internal Service Retirement Runbook
audience: internal
region: global
kind: runbook
pair: null
canary_facts:
  phrase: LANTERN-RETIRE-5
---
This fictional internal runbook helps a service owner retire an unused hosted FastAPI deployment without disrupting active workspaces. Confirm ownership, dependencies, open incidents, and the approved retirement date before scheduling any change. The distinctive phrase below is a synthetic retrieval canary; it is not a real service identifier or deletion authorization.

Notify affected teams, preserve required operational records, and provide a migration path when another service depends on the deployment. Disable traffic through the approved control plane, then monitor for unexpected requests or errors during the observation window. Remove resources only after the owner confirms the dependency check is complete. Record the final state and rollback contact in the restricted change case; do not retain credentials or customer payloads in the runbook.

Canary phrase: LANTERN-RETIRE-5.

Synthetic document for Nimbus capstone testing. Not real policy.
