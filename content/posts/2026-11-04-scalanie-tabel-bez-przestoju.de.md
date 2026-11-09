---
title: "Tabellen ohne Ausfallzeit zusammenführen: Wenn aus zwei Datenmodellen eines wird"
date: 2026-11-04T08:00:00+01:00
slug: "tabellen-zusammenfuehren-ohne-ausfallzeit"
description: "Wie man Daten aus mehreren Tabellen sicher in einem neuen Modell zusammenführt, ohne die gesamte Anwendung auf einmal umzustellen."
category: "Relationale Renaissance"
tags:
  - SQL Server
  - Schema-Evolution
  - Datenmigration
  - Zero Downtime
  - Database DevOps
draft: false
---

Eine Tabelle aufzuteilen ist eine Richtung der Schema-Evolution. Manchmal möchten wir nach Jahren den umgekehrten Weg gehen: mehrere Strukturen in einem gemeinsamen Modell zusammenführen.

## Beispiel

Wir haben:

```text
RetailCustomer
BusinessCustomer
```

Und möchten zu folgendem Modell wechseln:

```text
Customer
```

## Das neue Modell

```sql
CREATE TABLE dbo.CustomerV2
(
    CustomerId bigint NOT NULL PRIMARY KEY,
    CustomerType varchar(20) NOT NULL,
    DisplayName nvarchar(200) NOT NULL,
    TaxId nvarchar(30) NULL
);
```

## Zuerst die Semantik zuordnen

Eine Zusammenführung ist nicht einfach nur ein `UNION ALL`.

Wir müssen klären:

- wie die Schlüssel zugeordnet werden,
- welche Spalten dieselbe Bedeutung haben,
- wie Kollisionen von Identifikatoren behandelt werden,
- wie Felder dargestellt werden, die nur in einem der bisherigen Modelle existieren.

## Ein stabiler Schlüssel

Wenn in den alten Tabellen dieselbe `CustomerId` vorkommen kann, benötigen wir eine Zuordnungsschicht.

```sql
CREATE TABLE migration.CustomerKeyMap
(
    SourceType varchar(20) NOT NULL,
    SourceId bigint NOT NULL,
    TargetId bigint NOT NULL,
    CONSTRAINT PK_CustomerKeyMap
        PRIMARY KEY (SourceType, SourceId)
);
```

## Backfill und laufende Änderungen

Zuerst übernehmen wir den historischen Datenbestand. Anschließend synchronisieren wir die Änderungen, die während der Migration eintreffen.

Change Data Capture (CDC), eine Ereigniswarteschlange oder Dual Writes können diese Aufgabe übernehmen.

## Schrittweise Umstellung der Datenkonsumenten

Nicht alle Anwendungen müssen gleichzeitig umgestellt werden.

Wir können zunächst folgende Komponenten umstellen:

- neue APIs,
- Berichte,
- ein ausgewähltes Anwendungsmodul,
- Batch-Prozesse.

## Die größte Falle

Entfernen Sie die alten Tabellen nicht allein deshalb, weil die neue Tabelle erfolgreich befüllt wurde.

Weisen Sie zuerst nach, dass niemand mehr auf den alten Vertrag angewiesen ist.

## Fazit

Bei der Zusammenführung von Tabellen migrieren wir Daten, Schlüssel und Semantik gleichzeitig.

Ohne Schlüsselzuordnung und Telemetrie entsteht leicht ein neues Modell, das sich nicht zuverlässig überprüfen lässt.

**Weiterführender Artikel:** [Eine Tabelle ohne Big Bang aufteilen](/de/posts/tabelle-aufteilen-ohne-big-bang/) beschreibt die umgekehrte Migration.
