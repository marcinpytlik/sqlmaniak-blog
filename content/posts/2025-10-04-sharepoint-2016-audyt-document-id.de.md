---
title: "SharePoint 2016: Überwachung und Document ID in der Praxis (On-Premises)"
date: "2025-10-04"
slug: "sharepoint-2016-ueberwachung-document-id"
draft: false
description: "Schritt für Schritt: Überwachung für eine Websitesammlung aktivieren, Document ID konfigurieren, PowerShell für Massenaktionen nutzen und das Ergebnis prüfen."
tags: ["SQL Server","Query Store","PSP","Performance","Tuning"]
author: "Marcin Pytlik | SQLManiak"
banner: "/images/sharepoint-2016-audyt-document-id.png"
---

Lead
----
SharePoint 2016 On-Premises kann eigenwillig sein, funktioniert aber. Hier ist die Reihenfolge: Überwachung → Document ID → Prüfung, dazu einige sofort nutzbare PowerShell-Beispiele.

## Überwachung
Central Admin → General Settings → Configure Audit Settings.  
In der Websitesammlung: *Audit Log Reports* öffnen und `Opening/Downloading`, `Editing`, `Moving/Copying` sowie weitere relevante Aktionen auswählen.

## Document ID
Site Collection Features → **Document ID Service** (Enable).  
Unter **Document ID settings** ein Präfix festlegen (z. B. `SQLM-`).

### Neuindizierung und Vergabe von IDs für vorhandene Dokumente
- Die Option „reassign IDs for existing“ kann Zeit benötigen — lass den Auftrag abschließen.  
- Den Fortschritt kannst du in den `ULS`-Protokollen über `DocumentId` prüfen.

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

## Überprüfung
- Die Spalte **Document ID** ist in Dokumentbibliotheken sichtbar.  
- Überwachungsberichte zeigen Benutzeraktionen.  
- In klassischen Ansichten lässt sich die Spalte zur Listenansicht hinzufügen.

> Denke an die Aufbewahrung der ULS-Protokolle und die Einstellung `Log File Location` — sonst kann der Speicherplatz knapp werden.
