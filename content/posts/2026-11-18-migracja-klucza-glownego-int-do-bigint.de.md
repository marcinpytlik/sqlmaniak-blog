---
title: "Von INT zu BIGINT: Einen Primärschlüssel ohne ein einziges großes ALTER migrieren"
date: 2026-11-18T08:00:00+01:00
slug: primaerschluessel-von-int-zu-bigint-migrieren
description: "Wie man die Migration eines Primärschlüssels von int auf bigint in einem großen System plant und dabei Fremdschlüssel, Indizes und Anwendungen berücksichtigt."
category: "Relationale Renaissance"
tags:
  - SQL Server
  - Schema-Evolution
  - BIGINT
  - Primärschlüssel
  - Datenmigration
draft: false
---

# Von INT zu BIGINT: Einen Primärschlüssel ohne ein einziges großes ALTER migrieren

Die Umstellung eines Primärschlüssels von `int` auf `bigint` klingt nach einer Änderung des Datentyps.

In der Praxis verändert sie einen ganzen Abhängigkeitsgraphen.

## Zuerst den verbleibenden Wertebereich prüfen

```sql
SELECT
    MAX(Id) AS MaxId,
    CAST(MAX(Id) AS decimal(19,0)) * 100.0 / 2147483647 AS IntUsagePercent
FROM dbo.Orders;
```

Warte nicht, bis der Wertebereich erschöpft ist.

## Warum ist ein einfaches ALTER riskant?

Ein Primärschlüssel kann:

- von zahlreichen Fremdschlüsseln referenziert werden,
- Bestandteil von Indizes sein,
- in Historientabellen verwendet werden,
- über APIs übertragen werden,
- in einem ORM als `int` abgebildet sein.

## Den neuen Schlüssel neben dem alten anlegen

```sql
ALTER TABLE dbo.Orders
ADD OrderIdBigint bigint NULL;
```

Anschließend werden die Daten schrittweise übernommen und der neue Index erstellt.

## Fremdschlüssel

Auch jede abhängige Tabelle benötigt eine neue Spalte:

```sql
ALTER TABLE dbo.OrderLines
ADD OrderIdBigint bigint NULL;
```

Eine eindeutige Zuordnung `OldId -> NewId` ist bei der Migration hilfreich – besonders dann, wenn die neue Kennung nicht durch eine einfache Typumwandlung entsteht.

## Die Anwendung

Während der Übergangszeit muss das Anwendungsmodell beide Schlüssel verstehen.

Das ist ein guter Zeitpunkt für:

- einen neuen API-Vertrag,
- Shadow Reads,
- vergleichende Telemetrie,
- die schrittweise Umstellung einzelner Module.

## Contract erst ganz zum Schluss

Der alte `int`-Schlüssel darf erst entfernt werden, wenn alle Referenzen migriert wurden.

## Fazit

Die Migration eines Primärschlüssels ist nicht einfach ein `ALTER COLUMN`. Sie ist ein Projekt zur Änderung des Vertrags zwischen Tabellen und Anwendungen.