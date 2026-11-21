---
title: "Compatibility Level After Migration — Why You Should Not Change It Immediately"
date: 2026-10-27T08:00:00+01:00
slug: compatibility-level-after-migration
description: "How to safely approach SQL Server Compatibility Level changes after migration: Query Store, baselines, plan regressions, and a rollback strategy."
tags: [SQLServer, Migration, CompatibilityLevel, QueryStore, DBA]
categories: [SQL Server]
draft: false
---

Moving a database to SQL Server 2022 does not mean you have to set `COMPATIBILITY_LEVEL = 160` immediately.

These are two separate steps, and it is worth treating them that way.

## First, Check the Current Level

```sql
SELECT
    name,
    compatibility_level
FROM sys.databases
WHERE database_id > 4
ORDER BY name;
```

A database can run on SQL Server 2022 while still using Compatibility Level 130. This lets you separate the engine migration from changes to optimizer behavior.

## Why Does It Matter?

Changing the Compatibility Level can affect, among other things:

- Cardinality Estimator,
- scalar UDF inlining,
- table variable deferred compilation,
- batch mode on rowstore,
- memory grant feedback,
- Parameter Sensitive Plan optimization.

Not every change will cause a regression, but every change should be monitored.

## Query Store Before the Change

```sql
SELECT
    actual_state_desc,
    current_storage_size_mb,
    max_storage_size_mb,
    readonly_reason
FROM sys.database_query_store_options;
```

Before changing the level, capture a baseline: the most expensive queries, CPU, logical reads, execution times, waits, and the most important execution plans.

## Changing the Compatibility Level

```sql
ALTER DATABASE [TwojaBaza]
SET COMPATIBILITY_LEVEL = 160;
```

After the change, do not judge the system solely by whether the application starts. Observe its behavior under real workload.

## Rollback Plan

```sql
ALTER DATABASE [TwojaBaza]
SET COMPATIBILITY_LEVEL = 130;
```

The change is reversible, but rollback should not be the first reaction. First determine whether the issue concerns a specific query.

## Summary

Migration and Compatibility Level changes are two different stages.

A level-headed DBA migrates the system, stabilizes it, collects a baseline, and only then deliberately enables new optimizer behaviors.