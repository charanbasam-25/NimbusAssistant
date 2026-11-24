---
id: backup-retention-r2
title: Backup Retention (R2)
audience: public
region: R2
kind: policy
pair: backup-retention
canary_facts:
  retention_days: 35
---
Nimbus Cloud creates routine backups to help workspace owners recover from an accidental change or a service interruption. The retention period begins when a backup is created, and older copies are removed as they pass the published window. Owners can review the latest backup status in the dashboard and should maintain separate application exports when their own recovery plan requires them.

For workspaces in region R2, routine platform backups are retained for 35 days. This window applies to standard workspace backups and does not guarantee that every individual object can be restored to an exact point in time. Before relying on a backup, confirm that the service has completed a recent successful backup and that the application can read restored data.

If a restore is needed, open a support case with the workspace name, approximate backup time, and affected service. Do not attach customer records or secrets to the request. A support agent will confirm which recovery options are available for the workspace. These fictional operating terms are not a substitute for an organization's own backup and disaster-recovery plan.

Synthetic document for Nimbus capstone testing. Not real policy.
