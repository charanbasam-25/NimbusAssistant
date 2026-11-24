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
Use this internal runbook when a service owner requests retirement of an unused Nimbus Cloud deployment. Verify ownership, downstream dependencies, open incidents, and the approved retirement date before scheduling a change. Notify affected teams and identify a migration path for any workspace that still depends on the service. LANTERN-RETIRE-5 is the index reference for this fictional checklist, not a service identifier or deletion authorization.

Disable incoming traffic through the approved control plane and monitor the service during the observation window for unexpected requests or errors. Preserve the operational records required by the retention schedule. Remove the remaining resources only after the owner confirms that dependency checks are complete and the rollback contact is available.

Record the final state, operator, and completion time in the restricted change case. Do not retain credentials or customer payloads in the runbook. If new traffic or an unresolved incident appears, pause retirement and contact the service owner. This fictional procedure is for documentation tests and must not be used to retire a real deployment.

Synthetic document for Nimbus capstone testing. Not real policy.
