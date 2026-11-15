---
title: "Query Store nach einer Migration — Regressionen von Ausführungsplänen erkennen"
date: 2026-11-03T08:00:00+01:00
slug: query-store-po-migracji
description: "Mit SQL Server Query Store nach einer Migration Ausführungspläne vergleichen, Regressionen erkennen und sicher auf Leistungsprobleme reagieren."
tags: [SQLServer, QueryStore, Performance, Migration, DBA]
categories: [SQL Server]
draft: false
---

Die schwerwiegendsten Performanceprobleme treten nach einer Migration nicht immer sofort auf.

Oft scheint die Anwendung einwandfrei zu funktionieren, doch einzelne Abfragen verwenden plötzlich ungünstigere Ausführungspläne. Mit Query Store lässt sich diese Veränderung nachvollziehen, statt über ihre Ursache zu spekulieren.

## Ist Query Store aktiv?

```sql
SELECT
    actual_state_desc,
    desired_state_desc,
    current_storage_size_mb,
    max_storage_size_mb,
    readonly_reason
FROM sys.database_query_store_options;
```

Wenn Query Store in den Zustand `READ_ONLY` gewechselt ist, klären Sie zunächst die Ursache.

## Eine query_id, mehrere Ausführungspläne

```sql
SELECT
    p.query_id,
    p.plan_id,
    p.is_forced_plan,
    p.last_execution_time
FROM sys.query_store_plan AS p
WHERE p.query_id = 123
ORDER BY p.last_execution_time DESC;
```

Falls nach der Migration ein neuer Plan entstanden ist, vergleichen Sie dessen Statistiken mit denen des vorherigen Plans.

## Welche Kennzahlen sind relevant?

- Ausführungsdauer.
- CPU-Zeit.
- Logische Lesezugriffe.
- Anzahl der Ausführungen.
- Wartestatistiken (Waits).
- Verteilung der Parameterwerte.

Eine Planänderung allein ist noch keine Regression. Von einer Regression sprechen wir, wenn sich das Verhalten einer Abfrage unter einer repräsentativen Last verschlechtert.

## Einen Plan erzwingen — mit Vorsicht

```sql
EXEC sys.sp_query_store_force_plan
    @query_id = 123,
    @plan_id = 456;
```

Das Erzwingen eines Plans kann die Auswirkungen einer Regression schnell begrenzen, ersetzt aber keine Ursachenanalyse.

## Fazit

Query Store ist besonders wertvoll, wenn sich ein System verändert.

Ein besonnener DBA fragt nicht nur: „Ist die Abfrage langsam?“, sondern: „Was hat sich am Verhalten genau dieser Abfrage geändert?“
