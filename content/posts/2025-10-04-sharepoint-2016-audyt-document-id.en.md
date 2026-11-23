---
title: "SharePoint 2016: Auditing and Document ID in Practice (On-Premises)"
date: "2025-10-04"
slug: "sharepoint-2016-auditing-document-id"
draft: false
description: "Step by step: enable auditing for a site collection, configure Document ID, use PowerShell for bulk operations, and verify the results."
tags: ["SQL Server","Query Store","PSP","Performance","Tuning"]
author: "Marcin Pytlik | SQLManiak"
banner: "/images/sharepoint-2016-audyt-document-id.png"
---

Lead
----
SharePoint 2016 on-premises can be temperamental, but it works. Here is the sequence: Auditing → Document ID → verification, plus a few ready-to-use PowerShell snippets.

## Auditing
Central Admin → General Settings → Configure Audit Settings.  
For the site collection: open *Audit Log Reports* and select `Opening/Downloading`, `Editing`, `Moving/Copying`, and other relevant actions.

## Document ID
Site Collection Features → **Document ID Service** (Enable).  
Set a prefix in **Document ID settings** (for example, `SQLM-`).

### Reindexing and assigning IDs to existing documents
- The “reassign IDs for existing” option can take time — allow the job to finish.  
- Search `ULS` logs for `DocumentId` to check progress.

## PowerShell
```powershell
$siteUrl="https://sp2016/sites/Docs"
$site=Get-SPSite $siteUrl
$site.Audit.AuditFlags="All"
$site.Audit.Update()
Enable-SPFeature -Identity "DocumentId" -Url $siteUrl -Force
$svc = Get-SPDocumentIdServiceApplication
Set-SPDocumentId -Site $siteUrl -Prefix "SQLM-"
```

## Verification
- The **Document ID** column is visible in document libraries.  
- Audit reports show user operations.  
- In classic views, you can add the column to the list view.

> Remember ULS log retention and the `Log File Location` setting — otherwise you may run out of disk space.
