---
title: "Query Store After Migration — How to Detect Execution Plan Regressions"
date: 2026-11-03T08:00:00+01:00
slug: query-store-po-migracji
description: "Use SQL Server Query Store after migration to compare plans, identify regressions, and respond safely to performance problems."
tags: [SQLServer, QueryStore, Performance, Migration, DBA]
categories: [SQL Server]
draft: false
---

The worst performance issues do not always show up immediately after a migration.

Often, an application appears to work correctly, but individual queries start using worse execution plans. Query Store lets you observe the change rather than guess what happened.

## Is Query Store running?

```sql
SELECT
    actual_state_desc,
    desired_state_desc,
    current_storage_size_mb,
    max_storage_size_mb,
    readonly_reason
FROM sys.database_query_store_options;
```

If Query Store has switched to `READ_ONLY`, find out why before proceeding.

## One query_id, multiple plans

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

If a new plan appeared after migration, compare its statistics with those of the previous plan.

## What should you compare?

- Duration.
- CPU time.
- Logical reads.
- Execution count.
- Wait statistics.
- Parameter distribution.

A plan change is not, by itself, a regression. A regression means that query behavior has deteriorated under a representative workload.

## Force a plan — with caution

```sql
EXEC sys.sp_query_store_force_plan
    @query_id = 123,
    @plan_id = 456;
```

Forcing a plan can quickly mitigate a regression, but it does not replace root-cause analysis.

## Takeaway

Query Store is especially valuable when a system is changing.

A composed DBA does not ask only, “Is it slow?” They ask, “What changed in the behavior of this particular query?”
