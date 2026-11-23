---
title: "PIOSEE: Incident-Framework für DBAs mit kopierfertiger Vorlage"
date: "2025-10-04"
slug: "piosee-framework-fuer-dbas"
draft: false
description: "Eine praktische Vorlage zur Bearbeitung von Vorfällen (Problem–Information–Options–Select–Execute–Evaluate) mit Beispielen für SQL Server."
tags: ["DBA", "Incident Management", "Runbook", "PIOSEE", "Produktivität"]
author: "Marcin Pytlik | SQLManiak"
banner: "/images/piosee-framework-dla-dba.png"
---

Einleitung
----------
Wenn ein System in Flammen steht, brauchst du einen Ablaufplan, keine Poesie. PIOSEE besteht aus sechs Schritten, die helfen, einen kühlen Kopf zu bewahren und Daten zu schützen.

## Vorlage
**P – Problem**: Beschreibung des Symptoms und eine Kennzahl (z. B. `Backup FULL > 4h`).  
**I – Information**: Fakten, DMVs und Protokolle ohne Interpretation.  
**O – Options**: Liste möglicher Lösungen (noch ohne Bewertung).  
**S – Select**: Auswahl einer Option anhand von Zeit, Risiko und Auswirkungen.  
**E – Execute**: Umsetzungsplan und Kommunikation.  
**E – Evaluate**: Ergebnisse bewerten, Erkenntnisse festhalten und überwachen.

## Beispiel: Transaktionsprotokoll zu 95 % belegt
- **Problem**: `% Log Used` steigt in MyDb auf 95 %.  
- **Information**: Seit 18 Stunden kein `BACKUP LOG`; `vlf_active=1` am Dateiende.  
- **Options**: Protokollsicherung; Protokolldatei vorübergehend vergrößern; lang laufende Transaktion beenden.  
- **Select**: Protokollsicherung und Vergrößerung auf 64 GB; die Transaktion wird nicht beendet.  
- **Execute**: `BACKUP LOG`, `ALTER DATABASE ... MODIFY FILE`; Team benachrichtigen.  
- **Evaluate**: VLFs im normalen Bereich, `% Used < 30%`, Warnmeldung eingerichtet.

## Kopierfertige Vorlage (Markdown)
```
# PIOSEE – Incydent: <tytuł>

## P – Problem
<co nie działa>

## I – Information
<logi/DMV/screeny>

## O – Options
- [ ] Opcja A
- [ ] Opcja B

## S – Select
Wybrano: <opcja>, uzasadnienie.

## E – Execute
Kroki, właściciele, okno, rollback plan.

## E – Evaluate
Wynik, metryki po, wnioski, zadania follow‑up.
```
