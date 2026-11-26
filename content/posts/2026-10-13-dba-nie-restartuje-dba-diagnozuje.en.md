---
title: "A DBA Doesn't Restart First — A DBA Diagnoses"
date: 2026-10-13T20:00:00+02:00
slug: dba-nie-restartuje-dba-diagnozuje
description: "First minutes of a SQL Server incident: preserve evidence, inspect blocking, waits, resources, and recent changes."
tags: [SQLServer, Troubleshooting, IncidentResponse, DBA, Monitoring]
categories: [SQL Server]
draft: false
---

Restarting the service can be effective. The problem is that it also destroys much of the evidence needed to determine the root cause.

## First Principle

> Preserve diagnostic evidence first. Only then decide on corrective action.

## The First Five Minutes

Establish:

- What exactly is failing.
- When the issue started.
- Whether it affects one database or the entire instance.
- Whether anything changed.
- The business impact.

## Active Requests

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

Do not kill a session merely because it blocks others. First investigate the transaction and the potential cost of rollback.

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

## Memory

```sql
SELECT
    physical_memory_in_use_kb / 1024 AS SqlMemoryUsedMB,
    locked_page_allocations_kb / 1024 AS LockedPagesMB,
    memory_utilization_percentage,
    process_physical_memory_low,
    process_virtual_memory_low
FROM sys.dm_os_process_memory;
```

## Recent Changes

Review deployments, patching, failovers, configuration changes, new workloads, and data growth.

## When Is Restart Justified?

When it is part of an approved runbook, alternatives are riskier, and diagnostic data has already been collected.

Restarting is an operational action, not a diagnosis.

## Summary

A calm DBA does not begin by asking:

> Will a restart help?

Instead, ask:

> What diagnostic evidence will I lose, and do I understand the cause?
