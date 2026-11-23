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
Use the Nimbus Cloud backup-retention policy when planning recovery for a hosted FastAPI workspace. This page describes the standard retention window for the listed topic and helps an account owner understand how long a routine service backup remains available. Confirm the workspace region before relying on the canary below; the value is a fictional region-specific fact for the capstone retrieval exercise.

Backups support recovery from ordinary platform incidents, but they do not replace application exports or a tested restore plan. Before a maintenance change, identify which data matters and how the application will validate a recovered copy. The account dashboard displays the workspace's current backup status. For a support request, provide the workspace identifier, approximate backup time, and the affected service without attaching customer records.

Canary fact: standard Nimbus Cloud backups in R2 are retained for 35 days.

Synthetic document for Nimbus capstone testing. Not real policy.
