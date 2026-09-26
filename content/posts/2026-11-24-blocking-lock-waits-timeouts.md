---
title: "Blokowanie, lock waits i timeouty — jak czytać je razem"
date: 2026-11-24T20:00:00+01:00
slug: blocking-lock-waits-timeouts
description: "Jak korelować blocking, lock waits i lock timeouty w SQL Server, żeby odróżnić normalne blokowanie od problemu wymagającego interwencji."
tags: [SQLServer, Blocking, Locks, Performance, DBA]
categories: [SQL Server]
draft: false
---

Blokowanie jest normalną częścią działania SQL Server.

Problemem nie jest sam fakt, że jedna sesja czeka na drugą. Problem zaczyna się wtedy, gdy czas oczekiwania i wpływ na system przekraczają akceptowalny poziom.

## Aktywne blokowanie

```sql
SELECT
    r.session_id,
    r.blocking_session_id,
    DB_NAME(r.database_id) AS DatabaseName,
    r.wait_type,
    r.wait_time,
    r.wait_resource
FROM sys.dm_exec_requests AS r
WHERE r.blocking_session_id <> 0
ORDER BY r.wait_time DESC;
```

To pokazuje sytuację teraz. Nie mówi jeszcze, jak często problem występuje.

## Lock waits

```sql
SELECT
    wait_type,
    waiting_tasks_count,
    wait_time_ms
FROM sys.dm_os_wait_stats
WHERE wait_type LIKE N'LCK_M_%'
ORDER BY wait_time_ms DESC;
```

Największą wartość ma delta z określonego przedziału czasu.

## Lock timeout

```sql
SET LOCK_TIMEOUT 5000;
```

Żądanie zakończy się błędem po 5 sekundach oczekiwania na lock. Sam monitoring aktywnych blokad może więc nie pokazać pełnego wpływu na aplikację.

## Koreluj trzy rzeczy

- czas i liczbę aktywnych blokad,
- przyrost waitów `LCK_M_*`,
- liczbę timeoutów po stronie aplikacji lub Extended Events.

## Nie zabijaj sesji automatycznie

`KILL` może usunąć objaw i rozpocząć kosztowny rollback. Najpierw sprawdź transakcję i wpływ biznesowy.

## Podsumowanie

Spokojny DBA nie alertuje na każdą blokadę.

Alertuje na blokowanie, które ma mierzalny wpływ na system i użytkowników.