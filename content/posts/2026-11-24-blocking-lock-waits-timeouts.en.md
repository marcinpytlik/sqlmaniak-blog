---
title: "Blocking, Lock Waits, and Timeouts — How to Read Them Together"
date: 2026-11-24T08:00:00+01:00
slug: blocking-lock-waits-timeouts
description: "Correlating blocking, lock waits, and lock timeouts in SQL Server to distinguish normal contention from actionable incidents."
tags: [SQLServer, Blocking, Locks, Performance, DBA]
categories: [SQL Server]
draft: false
---

Blocking is a normal part of SQL Server operation.

The problem is not that one session waits for another. It begins when wait duration and system impact exceed acceptable limits.

## Active Blocking

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

This shows what is happening now. It does not tell us how often the problem occurs.

## Lock Waits

```sql
SELECT
    wait_type,
    waiting_tasks_count,
    wait_time_ms
FROM sys.dm_os_wait_stats
WHERE wait_type LIKE N'LCK_M_%'
ORDER BY wait_time_ms DESC;
```

The most useful measurement is the change (delta) over a defined time interval.

## Lock Timeout

```sql
SET LOCK_TIMEOUT 5000;
```

The request will fail after waiting five seconds for a lock. Monitoring active blocking alone may therefore miss the full impact on the application.

## Correlate Three Signals

- Duration and number of active blocking sessions.
- Growth in `LCK_M_*` waits.
- Number of timeouts observed by the application or Extended Events.

## Do Not Automatically Kill Sessions

`KILL` can remove a symptom while triggering an expensive rollback. First inspect the transaction and business impact.

## Summary

A calm DBA does not alert on every blocked session.

Alert on blocking that measurably affects the system and its users.
