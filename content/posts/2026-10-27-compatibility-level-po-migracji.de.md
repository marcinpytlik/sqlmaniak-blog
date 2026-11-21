---
title: "Compatibility Level nach der Migration — warum eine sofortige Umstellung keine gute Idee ist"
date: 2026-10-27T08:00:00+01:00
slug: compatibility-level-nach-migration
description: "Wie man den Compatibility Level nach einer SQL-Server-Migration sicher ändert: Query Store, Baseline, Planregressionen und Rollback-Strategie."
tags: [SQLServer, Migration, CompatibilityLevel, QueryStore, DBA]
categories: [SQL Server]
draft: false
---

Eine Datenbank auf SQL Server 2022 zu migrieren bedeutet nicht, dass man sofort `COMPATIBILITY_LEVEL = 160` einstellen muss.

Das sind zwei getrennte Schritte, und genau so sollte man sie behandeln.

## Zuerst den aktuellen Level prüfen

```sql
SELECT
    name,
    compatibility_level
FROM sys.databases
WHERE database_id > 4
ORDER BY name;
```

Eine Datenbank kann unter SQL Server 2022 laufen und weiterhin Compatibility Level 130 verwenden. So lässt sich die Migration der Datenbank-Engine von Änderungen am Optimizer-Verhalten trennen.

## Warum ist das wichtig?

Eine Änderung des Compatibility Levels kann unter anderem Folgendes beeinflussen:

- Cardinality Estimator,
- Scalar UDF Inlining,
- Table Variable Deferred Compilation,
- Batch Mode on Rowstore,
- Memory Grant Feedback,
- Parameter Sensitive Plan Optimization.

Nicht jede Änderung führt zu einer Regression. Trotzdem sollte jede Änderung überwacht werden.

## Query Store vor der Umstellung

```sql
SELECT
    actual_state_desc,
    current_storage_size_mb,
    max_storage_size_mb,
    readonly_reason
FROM sys.database_query_store_options;
```

Vor der Umstellung erfassen wir eine Baseline: die aufwendigsten Abfragen, CPU, Logical Reads, Ausführungszeiten, Waits und die wichtigsten Ausführungspläne.

## Compatibility Level ändern

```sql
ALTER DATABASE [TwojaBaza]
SET COMPATIBILITY_LEVEL = 160;
```

Nach der Umstellung reicht es nicht, zu prüfen, ob die Anwendung startet. Entscheidend ist ihr Verhalten unter realer Last.

## Rollback-Plan

```sql
ALTER DATABASE [TwojaBaza]
SET COMPATIBILITY_LEVEL = 130;
```

Die Änderung lässt sich rückgängig machen. Ein Rollback sollte aber nicht die erste Reaktion sein. Zuerst ist zu prüfen, ob das Problem nur eine bestimmte Abfrage betrifft.

## Fazit

Migration und Compatibility Level sind zwei unterschiedliche Etappen.

Ein besonnener DBA migriert zunächst das System, stabilisiert es, erfasst eine Baseline und aktiviert erst danach bewusst neue Verhaltensweisen des Optimizers.