---
id: data-residency-r1
title: Data Residency (R1)
audience: public
region: R1
kind: policy
pair: data-residency
canary_facts:
  residency_location: nc-us-1
---
Workspace owners choose a deployment region when creating a Nimbus Cloud service. The region shown in the dashboard identifies the location assigned to the workspace's primary service data. Before moving an application, review its storage settings and confirm that any separately configured backups or integrations meet the organization's own requirements. A region selection does not configure application-level encryption or determine where an external service stores information.

For a workspace assigned to region R1, the primary data location is the fictional facility identifier nc-us-1. The dashboard displays this location on the workspace details page and on deployment records. If an owner believes a service was created in the wrong region, they should contact support before migrating data or changing deployment settings.

For a residency question, include the workspace name and identify whether the question concerns the running service, logs, or backup copies. Do not attach customer records to a support case unless support has requested a specific sanitized sample. These fictional service details are not commitments from an actual cloud provider.

Synthetic document for Nimbus capstone testing. Not real policy.
