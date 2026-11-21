---
title: "NOT NULL Without Downtime: How to Safely Add a Required Column"
date: 2026-10-14T00:01:00+02:00
slug: add-not-null-column-without-downtime
description: "A safe pattern for adding a required column to a large table without relying on one risky deployment."
category: "Relational Renaissance"
tags:
  - SQL Server
  - schema evolution
  - NOT NULL
  - zero downtime
  - database DevOps
draft: false
---

# NOT NULL Without Downtime: How to Safely Add a Required Column

A seemingly simple change:

```sql
ALTER TABLE dbo.Orders
ADD SourceSystem varchar(20) NOT NULL;
```

may be anything but simple on a large table.

A safer approach is to break it into several stages.

## Stage 1 — Add a Nullable Column

```sql
ALTER TABLE dbo.Orders
ADD SourceSystem varchar(20) NULL;
```

The old code still works because it does not yet need to know about the new column.

## Stage 2 — Make the New Code Write a Value

From this point on, every new row should have a `SourceSystem` value.

You can monitor violations:

```sql
SELECT COUNT(*) AS MissingValueCount
FROM dbo.Orders
WHERE SourceSystem IS NULL;
```

## Stage 3 — Backfill

Populate historical rows in batches.

```sql
WHILE 1 = 1
BEGIN
    UPDATE TOP (10000) dbo.Orders
    SET SourceSystem = 'LEGACY'
    WHERE SourceSystem IS NULL;

    IF @@ROWCOUNT = 0 BREAK;

    WAITFOR DELAY '00:00:00.200';
END;
```

Choose the batch size based on observed log usage, blocking, and execution time.

## Stage 4 — Validate

```sql
SELECT COUNT(*)
FROM dbo.Orders
WHERE SourceSystem IS NULL;
```

Zero is only the beginning. You must also confirm that all active application versions write the value.

## Stage 5 — Enforce NOT NULL

```sql
ALTER TABLE dbo.Orders
ALTER COLUMN SourceSystem varchar(20) NOT NULL;
```

This should be a separate deployment step.

## What About DEFAULT?

A default can help with new rows:

```sql
ALTER TABLE dbo.Orders
ADD CONSTRAINT DF_Orders_SourceSystem
DEFAULT ('APP') FOR SourceSystem;
```

However, it should not hide an application defect unless that is a deliberate decision.

## The Most Important Rule

First make sure the constraint is **true in business terms and in the actual data**. Only then enforce it technically.

## Summary

Changing `NULL -> NOT NULL` does not have to be a single command.

Expand, write the new value, backfill, validate, and only then enforce the constraint — that is a much more controlled approach.