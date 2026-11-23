---
id: account-deletion-r2
title: Internal Account Deletion Runbook (R2)
audience: internal
region: R2
kind: runbook
pair: account-deletion
canary_facts:
  deletion_retention: Delete after 14 days and retain a GDPR audit log
---
This internal Nimbus Cloud account-deletion runbook helps authorized support staff coordinate a workspace removal request. Confirm the requester is authorized, identify the workspace, and check for an active hold or unresolved billing task before scheduling deletion. The timing below is the region-specific canary for this capstone test, not an actual retention rule or permission to delete a real account.

Record the case reference, approval source, and planned completion date in the restricted operations record. Tell the requester which resources are in scope and which exports they must complete beforehand. Avoid copying application data into the ticket. After the approved action, verify the workspace status and record the result for audit. Escalate any mismatch between the request and workspace ownership rather than improvising a broader deletion.

Canary fact: the fictional R2 workflow deletes the workspace after 14 days and retains a GDPR audit log.

Synthetic document for Nimbus capstone testing. Not real policy.
