---
title: "Wait Statistics — Where to Really Start Diagnosing SQL Server Performance"
date: 2026-11-17T08:00:00+01:00
slug: wait-statistics-sql-server
description: "How to interpret SQL Server Wait Statistics, which conclusions to avoid, and why wait deltas are more useful than a single counter accumulated since instance startup."
tags: [SQLServer, WaitStats, Performance, Troubleshooting, DBA]
categories: [SQL Server]
draft: false
---

Wait Statistics do not answer the question, “What is broken?”

They are better at answering, “What has SQL Server been waiting for?”

## Current Instance Wait Statistics

```sql
SELECT TOP (30)
    wait_type,
    waiting_tasks_count,
    wait_time_ms,
    signal_wait_time_ms
FROM sys.dm_os_wait_stats
ORDER BY wait_time_ms DESC;
```

These results cover the period since the SQL Server instance started or its wait statistics were cleared. Without context, it is easy to draw the wrong conclusions.

## Calculate the Delta

A better approach during an incident:

1. capture snapshot A,
2. wait for a defined interval,
3. capture snapshot B,
4. calculate the difference.

What matters is what happened while the problem was occurring.

## Waits and Active Requests

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

Only then does a wait type start to have a specific meaning.

## Possible Directions for Investigation

- `PAGEIOLATCH_*` — storage, large scans, memory,
- `LCK_M_*` — blocking and transactions,
- `RESOURCE_SEMAPHORE` — memory grants,
- `ASYNC_NETWORK_IO` — how the client consumes result sets.

These are diagnostic leads, not ready-made diagnoses.

## Summary

Wait Statistics are a map, not an answer.

A level-headed DBA uses them to narrow the search.