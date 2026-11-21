---
title: "Wait Statistics — Wo beginnt die Performanceanalyse von SQL Server wirklich?"
date: 2026-11-17T08:00:00+01:00
slug: wait-statistics-sql-server
description: "Wie man Wait Statistics in SQL Server interpretiert, welche voreiligen Schlüsse man vermeiden sollte und warum die Differenz zwischen zwei Messungen aussagekräftiger ist als ein Zähler seit dem Instanzstart."
tags: [SQLServer, WaitStats, Performance, Fehleranalyse, DBA]
categories: [SQL Server]
draft: false
---

Wait Statistics beantworten nicht die Frage: „Was ist defekt?“

Sie beantworten vielmehr: „Worauf hat SQL Server gewartet?“

## Aktuelle Wait Statistics der Instanz

```sql
SELECT TOP (30)
    wait_type,
    waiting_tasks_count,
    wait_time_ms,
    signal_wait_time_ms
FROM sys.dm_os_wait_stats
ORDER BY wait_time_ms DESC;
```

Diese Werte umfassen den Zeitraum seit dem Start der SQL-Server-Instanz oder seit dem Zurücksetzen der Wait Statistics. Ohne Kontext zieht man daraus leicht falsche Schlüsse.

## Die Differenz berechnen

Bei einem Vorfall ist ein besseres Vorgehen:

1. Messstand A erfassen,
2. ein festgelegtes Zeitintervall abwarten,
3. Messstand B erfassen,
4. die Differenz berechnen.

Entscheidend ist, was während des Problems passiert ist.

## Waits und aktive Anfragen

```sql
SELECT
    r.session_id,
    DB_NAME(r.database_id) AS DatabaseName,
    r.wait_type,
    r.wait_time,
    r.wait_resource,
    r.blocking_session_id,
    r.cpu_time,
    r.logical_reads
FROM sys.dm_exec_requests AS r
WHERE r.session_id <> @@SPID
ORDER BY r.wait_time DESC;
```

Erst dann erhält ein Wait-Typ eine konkrete Bedeutung.

## Mögliche Ansatzpunkte für die Analyse

- `PAGEIOLATCH_*` — Storage, große Scans, Arbeitsspeicher,
- `LCK_M_*` — Blocking und Transaktionen,
- `RESOURCE_SEMAPHORE` — Memory Grants,
- `ASYNC_NETWORK_IO` — wie der Client die Ergebnisse abruft.

Das sind Hinweise für die Diagnose, keine fertigen Diagnosen.

## Fazit

Wait Statistics sind eine Landkarte, keine Antwort.

Ein besonnener DBA nutzt sie, um den Suchbereich einzugrenzen.