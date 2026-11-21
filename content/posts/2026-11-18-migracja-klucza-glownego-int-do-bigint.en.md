---
title: "INT to BIGINT: Migrating a Primary Key Without One Massive ALTER"
date: 2026-11-18T08:00:00+01:00
slug: migrating-primary-key-int-to-bigint
description: "How to plan a primary-key migration from int to bigint in a large system while accounting for foreign keys, indexes, and the application."
category: "Relational Renaissance"
tags:
  - SQL Server
  - schema evolution
  - BIGINT
  - primary key
  - data migration
draft: false
---

# INT to BIGINT: Migrating a Primary Key Without One Massive ALTER

Changing a primary key from `int` to `bigint` sounds like a data type change.

In practice, it changes an entire graph of dependencies.

## First, Measure How Much Headroom You Have

```sql
SELECT
    MAX(Id) AS MaxId,
    CAST(MAX(Id) AS decimal(19,0)) * 100.0 / 2147483647 AS IntUsagePercent
FROM dbo.Orders;
```

Do not wait until you run out of values.

## Why Is a Simple ALTER Risky?

A primary key may be:

- referenced by many foreign keys,
- part of indexes,
- used in history tables,
- passed through APIs,
- mapped as `int` in an ORM.

## Add the New Key Alongside the Old One

```sql
ALTER TABLE dbo.Orders
ADD OrderIdBigint bigint NULL;
```

Next, backfill the data and build the new index.

## Foreign Keys

Every dependent table also needs a new column:

```sql
ALTER TABLE dbo.OrderLines
ADD OrderIdBigint bigint NULL;
```

An unambiguous `OldId -> NewId` mapping is useful during migration, especially when the new identifier is not a straightforward type conversion.

## The Application

During the transition, the application model must understand both keys.

This is a good opportunity to introduce:

- a new API contract,
- shadow reads,
- comparative telemetry,
- gradual cutover of individual modules.

## Contract Only at the End

The old `int` key can be removed only after all references have been migrated.

## Summary

A primary-key migration is not just an `ALTER COLUMN`. It is a project to change the contract between tables and applications.