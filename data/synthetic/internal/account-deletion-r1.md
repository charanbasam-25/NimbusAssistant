---
id: account-deletion-r1
title: Internal Account Deletion Runbook (R1)
audience: internal
region: R1
kind: runbook
pair: account-deletion
canary_facts:
  deletion_retention: Delete after 30 days
---
Use this runbook when an authorized Nimbus Cloud customer asks support to close a workspace. Verify the requester against the account record, confirm the workspace identifier, and check for a legal hold, open incident, or unresolved invoice before scheduling the request. Explain which deployments and stored settings are included so the owner can export anything they need before the closure date.

For an R1 workspace, the deletion workflow completes 30 days after the approved request. Record the approval, request date, and target completion date in the restricted operations case. On the scheduled date, a second support operator confirms the workspace and scope before deletion. Afterward, verify that the workspace is no longer available and update the case with the completion timestamp.

Do not copy application content, credentials, or unnecessary personal information into the case. If ownership is unclear or an account is subject to a hold, pause the request and contact the designated reviewer rather than extending the deletion scope. This internal procedure is fictional training material and does not authorize action on a real service.

Synthetic document for Nimbus capstone testing. Not real policy.
