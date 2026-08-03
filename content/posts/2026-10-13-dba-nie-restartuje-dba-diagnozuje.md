---
title: "DBA nie restartuje — DBA diagnozuje"
date: 2026-10-13T20:00:00+02:00
slug: dba-nie-restartuje-dba-diagnozuje
description: "Procedura pierwszych minut incydentu SQL Server: zabezpieczenie danych diagnostycznych, analiza blokowania, waitów, zasobów i ostatnich zmian."
tags: [SQLServer, Troubleshooting, IncidentResponse, DBA, Monitoring]
categories: [SQL Server]
draft: false
---

Restart usługi bywa skuteczny.

Problem polega na tym, że usuwa wiele śladów potrzebnych do ustalenia przyczyny.

## Pierwsza zasada

> Najpierw zabezpiecz dane diagnostyczne. Potem podejmuj działania naprawcze.

## Pierwsze pięć minut

Ustal:

- co dokładnie nie działa,
- od kiedy,
- czy problem dotyczy jednej bazy czy całej instancji,
- czy wystąpiła zmiana,
- jaki jest wpływ biznesowy.

## Aktywne żądania

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

## Blokowanie

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

Nie zabijaj sesji tylko dlatego, że blokuje inne. Najpierw sprawdź transakcję i koszt rollbacku.

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

## Pamięć

```sql
SELECT
    physical_memory_in_use_kb / 1024 AS SqlMemoryUsedMB,
    locked_page_allocations_kb / 1024 AS LockedPagesMB,
    memory_utilization_percentage,
    process_physical_memory_low,
    process_virtual_memory_low
FROM sys.dm_os_process_memory;
```

## Ostatnie zmiany

Sprawdź wdrożenia, patching, failover, zmianę konfiguracji, nowe obciążenie i wzrost danych.

## Kiedy restart jest uzasadniony?

Gdy jest częścią zatwierdzonego runbooka, alternatywy są bardziej ryzykowne, a dane diagnostyczne zostały zebrane.

Restart jest działaniem operacyjnym, nie diagnozą.

## Podsumowanie

Spokojny DBA nie pyta najpierw:

> Czy restart pomoże?

Pyta:

> Co stracę diagnostycznie i czy rozumiem przyczynę problemu?
