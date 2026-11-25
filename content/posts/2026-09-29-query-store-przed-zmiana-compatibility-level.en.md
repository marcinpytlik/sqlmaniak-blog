---
title: "Query Store Before Changing Compatibility Level — Preparing a Safe Migration"
date: 2026-09-29
slug: query-store-before-compatibility-level-change
description: "Use Query Store to establish a baseline before changing compatibility level and detect execution plan regressions after a SQL Server migration."
tags: [SQLServer, QueryStore, CompatibilityLevel, Migration, Performance]
categories: [SQL Server]
draft: false
---

Changing the database compatibility level can alter how queries are optimized.

Query Store lets you compare query behavior before and after the change.

## Enable Query Store

```sql
ALTER DATABASE [TwojaBaza]
SET QUERY_STORE = ON;
GO

ALTER DATABASE [TwojaBaza]
SET QUERY_STORE
(
    OPERATION_MODE = READ_WRITE,
    QUERY_CAPTURE_MODE = AUTO,
    MAX_STORAGE_SIZE_MB = 2048,
    INTERVAL_LENGTH_MINUTES = 15,
    CLEANUP_POLICY =
    (
        STALE_QUERY_THRESHOLD_DAYS = 30
    )
);
GO
```

## Check Its State

```sql
SELECT
    actual_state_desc,
    desired_state_desc,
    current_storage_size_mb,
    max_storage_size_mb,
    readonly_reason,
    query_capture_mode_desc
FROM sys.database_query_store_options;
```

## How Long Should You Collect a Baseline?

The baseline should include:

- ordinary business days,
- peak periods,
- overnight processes,
- month-end closing,
- ETL,
- periodic reports.

## Change the Compatibility Level

```sql
ALTER DATABASE [TwojaBaza]
SET COMPATIBILITY_LEVEL = 160;
```

Perform this change as a separate stage, after testing and with a rollback plan ready.

## Force a Previous Plan

```sql
EXEC sys.sp_query_store_force_plan
    @query_id = 123,
    @plan_id = 456;
```

Plan forcing can stabilize performance, but it should be monitored and documented.

## Migration Plan

1. Enable Query Store.
2. Verify its configuration.
3. Collect a representative baseline.
4. Record the critical queries.
5. Run a test.
6. Change the compatibility level.
7. Monitor regressions.
8. Stabilize critical queries.
9. Document plan forcing.
10. Implement lasting fixes.

## Summary

Query Store does not eliminate risk, but it replaces guesswork with data-driven analysis.

A careful DBA does not change the compatibility level without a reference point.

First, establish the baseline.
