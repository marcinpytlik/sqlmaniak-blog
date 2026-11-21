---
title: "Eine Spalte umbenennen, ohne die Anwendung zu beschädigen"
date: 2026-10-21T08:00:00+02:00
slug: spalte-umbenennen-ohne-anwendung-zu-beschaedigen
description: "Wie man eine SQL-Server-Spalte umbenennt, ohne die Kompatibilität zu älteren Anwendungsversionen sofort zu verlieren."
category: "Relationale Renaissance"
tags:
  - SQL Server
  - Schema-Evolution
  - Kompatibilität
  - Deployment
  - Database DevOps
draft: false
---

# Eine Spalte umbenennen, ohne die Anwendung zu beschädigen

`sp_rename` ist schnell.

Das Problem: Nicht alle Abhängigkeiten werden automatisch mit dem neuen Namen kompatibel.

## Die riskante Variante

```sql
EXEC sys.sp_rename
    N'dbo.Customer.Name',
    N'DisplayName',
    N'COLUMN';
```

Greift eine ältere Anwendung weiterhin auf `Name` zu, funktioniert sie sofort nicht mehr.

## Die kompatible Variante

Statt die Spalte direkt umzubenennen:

1. eine neue Spalte hinzufügen,
2. beide Werte konsistent halten,
3. den Anwendungscode umstellen,
4. die alte Spalte erst später entfernen.

```sql
ALTER TABLE dbo.Customer
ADD DisplayName nvarchar(200) NULL;
```

## Backfill

```sql
UPDATE dbo.Customer
SET DisplayName = Name
WHERE DisplayName IS NULL;
```

Bei großen Tabellen erfolgt dies in Batches.

## Die Übergangsphase

In dieser Phase sind folgende Lösungen möglich:

- Dual Writes in der Anwendung,
- ein Trigger als Übergangslösung,
- eine Stored Procedure, die beide Felder aktualisiert,
- eine Kompatibilitäts-View.

Ein Trigger kann praktisch sein, führt aber zu versteckter Logik und sollte ein klar festgelegtes Ablaufdatum haben.

## Wie findet man Abhängigkeiten?

```sql
SELECT
    OBJECT_SCHEMA_NAME(referencing_id) AS SchemaName,
    OBJECT_NAME(referencing_id) AS ObjectName
FROM sys.sql_expression_dependencies
WHERE referenced_id = OBJECT_ID(N'dbo.Customer');
```

Diese Abfrage findet nicht alles, etwa dynamisches SQL außerhalb der Datenbank.

Zusätzlich braucht man Telemetrie und eine Analyse der Anwendungen.

## Endgültiges Entfernen

Die alte Spalte darf erst entfernt werden, wenn:

- auf keiner Instanz mehr der alte Code läuft,
- keine Berichte oder Integrationen den alten Namen verwenden,
- das Monitoring keine Zugriffe mehr darauf zeigt,
- ein Rollback den alten Vertrag nicht mehr benötigt.

## Fazit

Eine Umbenennung ist eine technische Operation. Die Migration eines Namens ist eine Vertragsänderung.

In der Relationalen Renaissance ändern wir Verträge schrittweise.