---
title: "CDC als Migrationswerkzeug: Backfill ist erst der Anfang"
date: 2026-10-07T00:01:00+02:00
slug: "cdc-jako-narzedzie-migracji"
description: "Change Data Capture zur Synchronisierung laufender Änderungen bei der Migration großer Tabellen und Datenmodelle."
category: "Relacyjny Renesans"
tags:
  - SQL Server
  - CDC
  - migracja danych
  - schema evolution
  - database DevOps
draft: false
---

# CDC als Migrationswerkzeug: Backfill ist erst der Anfang

Bei großen Tabellen lässt sich nicht immer ein einziges `INSERT ... SELECT` ausführen und die Anwendung stundenlang anhalten.

Wir benötigen zwei Komponenten:

1. Einen Backfill historischer Daten.
2. Die Synchronisierung der Änderungen während der Migration.

CDC kann beim zweiten Punkt helfen.

## Prozessablauf

```text
T0  uruchom CDC
T1  rozpocznij backfill
T2  aplikacja nadal zapisuje do starej tabeli
T3  odczytuj zmiany z CDC
T4  aplikuj deltę do nowego modelu
T5  wyrównaj opóźnienie
T6  przełącz odczyt i zapis
```

## CDC aktivieren

```sql
EXEC sys.sp_cdc_enable_db;
GO

EXEC sys.sp_cdc_enable_table
    @source_schema = N'dbo',
    @source_name   = N'Orders',
    @role_name     = NULL,
    @supports_net_changes = 1;
GO
```

## LSN statt Zeitstempel

Wenn die vollständige Reihenfolge der Änderungen wichtig ist, sollte die Synchronisierung nicht allein auf `ModifiedDate` beruhen.

CDC arbeitet mit Log Sequence Numbers (LSNs). Damit lässt sich ein Bereich festlegen:

```sql
DECLARE @from_lsn binary(10) = sys.fn_cdc_get_min_lsn(N'dbo_Orders');
DECLARE @to_lsn   binary(10) = sys.fn_cdc_get_max_lsn();
```

## Idempotenz

Die Synchronisierung muss eine erneute Verarbeitung desselben Bereichs tolerieren. Dafür eignet sich ein gespeicherter Checkpoint:

```sql
CREATE TABLE migration.CdcCheckpoint
(
    PipelineName sysname NOT NULL PRIMARY KEY,
    LastProcessedLsn binary(10) NOT NULL,
    UpdatedAt datetime2(0) NOT NULL
);
```

## Das Cleanup-Problem

CDC speichert Änderungen nicht unbegrenzt. Der Cleanup-Job entfernt alte Einträge.

Wenn die Migrationspipeline zu lange stillsteht, kann der benötigte Bereich verschwinden.

Überwache:

- Die älteste verfügbare LSN.
- Die zuletzt verarbeitete LSN.
- Den Rückstand der Pipeline.
- Die Anzahl der Fehler.
- Die Änderungsrate.

## Cutover

Vor dem Umschalten muss der verbleibende Rückstand auf ein akzeptables Maß reduziert sein.

Das kann bedeuten:

- Schreibvorgänge kurz anzuhalten.
- Die letzten CDC-Änderungen zu lesen.
- Die verbleibende Delta-Menge anzuwenden.
- Die Anwendung umzuschalten.

## CDC ist keine magische Replikation

CDC erfasst Änderungen. Für deren Interpretation und Anwendung auf das neue Modell bist du verantwortlich.

Wenn eine Operation des alten Modells zu drei Operationen im neuen Modell wird, muss die Migrationslogik diese Transformation verstehen.

## Zusammenfassung

Der Backfill liefert den historischen Datenbestand. CDC verfolgt Änderungen während der Migration.

Zusammen bilden sie eine Grundlage für Online-Migrationen, benötigen aber Checkpoints, Monitoring und einen eindeutig definierten Umschaltpunkt.
