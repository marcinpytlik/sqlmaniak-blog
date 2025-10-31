---
title: "SharePoint 2016: audyt i Document ID w praktyce (on‑prem)"
date: "2025-10-04"
slug: "sharepoint-2016-audyt-document-id"
draft: false
description: "Krok po kroku: włączenie audytu na kolekcji witryn, konfiguracja Document ID, PowerShell do hurtowych działań i weryfikacja."
tags: ["SharePoint 2016", "Audyt", "Document ID", "PowerShell", "Governance"]
author: "Marcin Pytlik | SQLManiak"
lang: "pl"
banner: "/images/sharepoint-2016-audyt-document-id.png"
canonical: "https://sqlmaniak.blog/sharepoint-2016-audyt-document-id"
---

Lead
----
On‑prem roku 2016 bywa kapryśny, ale działa. Tu masz sekwencję: Audyt → Document ID → weryfikacja i parę „gotowców” PowerShell.

## Audyt
Central Admin → General Settings → Configure Audit Settings.  
Na kolekcji witryn: *Audit Log Reports* → zaznacz `Opening/Downloading`, `Editing`, `Moving/Copying` itd.

## Document ID
Site Collection Features → **Document ID Service** (Enable).  
Ustaw prefiks w **Document ID settings** (np. `SQLM-`).

### Reindeksacja i nadanie istniejącym
- Opcja „reassign IDs for existing” może trwać — zostaw jobowi czas.  
- Przebieg w `ULS` sprawdzisz po `DocumentId`.

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

## Weryfikacja
- Kolumna **Document ID** widoczna w bibliotekach.  
- Raporty audytu pokazują operacje użytkowników.  
- Dla klasycznych widoków można dołożyć kolumnę do widoku listy.

> Pamiętaj o retencji logów ULS i `Log File Location` – inaczej zjesz dysk.
