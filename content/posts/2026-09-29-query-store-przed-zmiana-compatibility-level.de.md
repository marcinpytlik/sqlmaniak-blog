---
title: "Query Store vor einer Änderung des Compatibility Levels — sichere Migration vorbereiten"
date: 2026-09-29
slug: query-store-vor-compatibility-level-aenderung
description: "Mit Query Store vor der Änderung des Compatibility Levels eine Baseline aufbauen und Planregressionen nach einer SQL-Server-Migration erkennen."
tags: [SQLServer, QueryStore, CompatibilityLevel, Migration, Performance]
categories: [SQL Server]
draft: false
---

Eine Änderung des Datenbank-Compatibility-Levels kann die Abfrageoptimierung beeinflussen.

Mit Query Store lässt sich das Abfrageverhalten vor und nach der Änderung vergleichen.

## Query Store aktivieren

```sql
ALTER DATABASE [TwojaBaza]
SET QUERY_STORE = ON;
GO

ALTER DATABASE [TwojaBaza]
SET QUERY_STORE
(
    OPERATION_MODE = READ_WRITE,
    QUERY_CAPTURE_MODE = AUTO,
    MAX_STORAGE_SIZE_MB = 2048,
    INTERVAL_LENGTH_MINUTES = 15,
    CLEANUP_POLICY =
    (
        STALE_QUERY_THRESHOLD_DAYS = 30
    )
);
GO
```

## Status prüfen

```sql
SELECT
    actual_state_desc,
    desired_state_desc,
    current_storage_size_mb,
    max_storage_size_mb,
    readonly_reason,
    query_capture_mode_desc
FROM sys.database_query_store_options;
```

## Wie lange sollte die Baseline gesammelt werden?

Die Baseline sollte Folgendes abdecken:

- normale Arbeitstage,
- Spitzenlastzeiten,
- nächtliche Prozesse,
- Monatsabschluss,
- ETL,
- periodische Berichte.

## Compatibility Level ändern

```sql
ALTER DATABASE [TwojaBaza]
SET COMPATIBILITY_LEVEL = 160;
```

Führe diese Änderung als eigenständigen Schritt durch — nach Tests und mit vorbereitetem Rollback-Plan.

## Einen früheren Plan erzwingen

```sql
EXEC sys.sp_query_store_force_plan
    @query_id = 123,
    @plan_id = 456;
```

Plan Forcing kann die Performance stabilisieren, muss aber überwacht und dokumentiert werden.

## Migrationsplan

1. Query Store aktivieren.
2. Konfiguration prüfen.
3. Repräsentative Baseline sammeln.
4. Kritische Abfragen dokumentieren.
5. Test durchführen.
6. Compatibility Level ändern.
7. Regressionen überwachen.
8. Kritische Abfragen stabilisieren.
9. Plan Forcing dokumentieren.
10. Dauerhafte Korrekturen umsetzen.

## Zusammenfassung

Query Store beseitigt Risiken nicht, ersetzt aber Vermutungen durch datenbasierte Analyse.

Ein sorgfältiger DBA ändert den Compatibility Level nicht ohne Vergleichsbasis.

Zuerst erstellt er eine Baseline.
