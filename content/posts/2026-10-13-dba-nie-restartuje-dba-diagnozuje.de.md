---
title: "Ein DBA startet nicht einfach neu — ein DBA diagnostiziert"
date: 2026-10-13T20:00:00+02:00
slug: dba-nie-restartuje-dba-diagnozuje
description: "Die ersten Minuten eines SQL-Server-Vorfalls: Diagnosedaten sichern, Blocking, Waits, Ressourcen und Änderungen prüfen."
tags: [SQLServer, Troubleshooting, IncidentResponse, DBA, Monitoring]
categories: [SQL Server]
draft: false
---

Ein Neustart des Dienstes kann helfen. Das Problem ist, dass er viele Spuren beseitigt, die zur Ursachenanalyse benötigt werden.

## Erste Regel

> Zuerst Diagnosedaten sichern. Danach über Gegenmaßnahmen entscheiden.

## Die ersten fünf Minuten

Kläre:

- Was genau nicht funktioniert.
- Seit wann das Problem besteht.
- Ob eine Datenbank oder die gesamte Instanz betroffen ist.
- Ob Änderungen stattgefunden haben.
- Welche geschäftlichen Auswirkungen bestehen.

## Aktive Requests

```sql
SELECT
    r.session_id,
    r.status,
    r.command,
    DB_NAME(r.database_id) AS DatabaseName,
    r.blocking_session_id,
    r.wait_type,
    r.wait_time,
    r.cpu_time,
    r.logical_reads,
    r.writes,
    r.total_elapsed_time,
    t.text
FROM sys.dm_exec_requests AS r
CROSS APPLY sys.dm_exec_sql_text(r.sql_handle) AS t
WHERE r.session_id <> @@SPID
ORDER BY r.total_elapsed_time DESC;
```

## Blocking

```sql
SELECT
    r.session_id,
    r.blocking_session_id,
    r.wait_type,
    r.wait_time,
    r.wait_resource,
    t.text
FROM sys.dm_exec_requests AS r
CROSS APPLY sys.dm_exec_sql_text(r.sql_handle) AS t
WHERE r.blocking_session_id <> 0
ORDER BY r.wait_time DESC;
```

Beende eine Session nicht nur deshalb, weil sie andere blockiert. Untersuche zuerst die Transaktion und die möglichen Rollback-Kosten.

## CPU

```sql
SELECT
    scheduler_id,
    current_tasks_count,
    runnable_tasks_count,
    active_workers_count,
    load_factor
FROM sys.dm_os_schedulers
WHERE status = N'VISIBLE ONLINE';
```

## Arbeitsspeicher

```sql
SELECT
    physical_memory_in_use_kb / 1024 AS SqlMemoryUsedMB,
    locked_page_allocations_kb / 1024 AS LockedPagesMB,
    memory_utilization_percentage,
    process_physical_memory_low,
    process_virtual_memory_low
FROM sys.dm_os_process_memory;
```

## Letzte Änderungen

Prüfe Deployments, Patching, Failover, Konfigurationsänderungen, neue Workloads und Datenwachstum.

## Wann ist ein Neustart gerechtfertigt?

Wenn er Teil eines freigegebenen Runbooks ist, Alternativen riskanter sind und Diagnosedaten bereits gesichert wurden.

Ein Neustart ist eine operative Maßnahme, keine Diagnose.

## Zusammenfassung

Ein besonnener DBA fragt nicht zuerst:

> Hilft ein Neustart?

Sondern:

> Welche Diagnosedaten verliere ich, und verstehe ich die Ursache?
