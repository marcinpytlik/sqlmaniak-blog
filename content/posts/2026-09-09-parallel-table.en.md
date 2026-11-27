---
title: "Parallel Table: Migrating to a New Table Without Rebuilding the Old One"
date: 2026-09-09T00:01:00+02:00
slug: "parallel-table-migration"
description: "Build a new table alongside the old one, migrate data, and switch the application over in a controlled manner."
category: "Relational Renaissance"
tags: [SQL Server, parallel table, table migration, schema evolution, zero downtime]
draft: false
---

# Parallel Table: Migrating to a New Table Without Rebuilding the Old One

Sometimes a model change is too extensive for a few `ALTER TABLE` statements. We may be changing:

- the primary key,
- partitioning,
- compression,
- data types,
- index layout,
- history storage,
- the meaning of certain columns.

In that situation, we can build **a new table alongside the old one**.

The Parallel Table pattern works as follows:

1. Create a V2 table.
2. Copy historical data.
3. Synchronize ongoing changes.
4. Compare both models.
5. Switch reads and writes.
6. Retain the old table for a safety period.
7. Remove it once correctness has been confirmed.

> Rather than rebuilding the foundations beneath an occupied building, we construct new foundations alongside it and redirect traffic.

## Example

The old table:

```sql
CREATE TABLE dbo.Orders
(
    OrderId    int IDENTITY(1,1) NOT NULL,
    CustomerId int NOT NULL,
    Amount     money NOT NULL,
    CreatedAt  datetime NOT NULL,

    CONSTRAINT PK_Orders
        PRIMARY KEY (OrderId)
);
```

The new model uses:

- `bigint` identifiers,
- `decimal` instead of `money`,
- `datetime2`,
- an explicit status,
- a different index layout.

```sql
CREATE TABLE dbo.OrdersV2
(
    OrderId     bigint NOT NULL,
    CustomerId  int NOT NULL,
    Amount      decimal(19,4) NOT NULL,
    OrderStatus varchar(20) NOT NULL,
    CreatedAt   datetime2(0) NOT NULL,

    CONSTRAINT PK_OrdersV2
        PRIMARY KEY CLUSTERED (OrderId),

    CONSTRAINT CK_OrdersV2_Status
        CHECK (OrderStatus IN ('New', 'Paid', 'Cancelled'))
);
```

## Copying Historical Data

```sql
INSERT INTO dbo.OrdersV2
(
    OrderId,
    CustomerId,
    Amount,
    OrderStatus,
    CreatedAt
)
SELECT
    CONVERT(bigint, OrderId),
    CustomerId,
    CONVERT(decimal(19,4), Amount),
    'Paid',
    CONVERT(datetime2(0), CreatedAt)
FROM dbo.Orders;
```

On a large table, use batched migration and record progress.

## Synchronizing Changes

The hardest question is what happens to rows modified while copying.

Possible strategies include:

### Short Read-Only Window

The simplest solution. Stop writes, copy the final delta, and switch tables. This works when a brief maintenance window is acceptable.

### Dual Write

The application writes to both tables. This requires atomicity and consistency monitoring.

### Change Data Capture

Copy the baseline data set, then replay changes from CDC.

### Synchronization Trigger

A trigger writes changes to V2. Conceptually simple, but it increases the cost of each operation and hides logic.

### Change Queue

Operations go into a queue table, and a separate process applies them to the new model.

The choice depends on downtime requirements, scale, and tolerance for temporary inconsistency.

## Validation

Comparing row counts is necessary but insufficient.

```sql
SELECT
    OldCount = (SELECT COUNT_BIG(*) FROM dbo.Orders),
    NewCount = (SELECT COUNT_BIG(*) FROM dbo.OrdersV2);
```

Also compare:

```sql
SELECT
    OldAmount = SUM(CONVERT(decimal(38,4), Amount))
FROM dbo.Orders;

SELECT
    NewAmount = SUM(CONVERT(decimal(38,4), Amount))
FROM dbo.OrdersV2;
```

Additionally verify:

- missing keys,
- duplicates,
- converted values,
- status distribution,
- date ranges,
- random row samples,
- results of critical business queries.

## Cutover

The switch may occur through:

- application configuration,
- stored procedures,
- a synonym,
- a view,
- renaming tables.

Example using a synonym:

```sql
CREATE SYNONYM app.Orders
FOR dbo.OrdersV2;
```

A synonym makes it easier to change the target object, but does not support every scenario and requires care with schema dependencies. The `app` schema must exist first.

Renaming tables is attractive but risky: it does not update every reference and may introduce errors between operations.

## Identity and New Rows

If both tables generate identifiers, collisions are easy to create. Better options include:

- generate the key in one place,
- pass the identifier to both tables,
- use a sequence,
- reserve ranges,
- switch the key generator before writing to V2.

Example sequence:

```sql
CREATE SEQUENCE dbo.OrderIdSequence
    AS bigint
    START WITH 1000000
    INCREMENT BY 1;
```

## Returning to the Old Table

Do not immediately delete V1 after cutover. It can remain a reference point and emergency option.

However, decide:

- whether V1 still receives writes,
- how long it will be retained,
- whether rollback is possible after writing values supported only by V2,
- when the table becomes a read-only archive.

## When Should You Use It?

Parallel Table is a good choice when:

- the structural change is large,
- new indexes or partitioning are needed,
- an in-place conversion is risky,
- V1 and V2 need to be compared,
- there is enough storage for parallel data.

## Costs

The greatest costs are disk space and synchronization. For a time, two full data sets are stored. You must also address:

- ongoing changes,
- keys,
- constraints,
- stored procedures,
- permissions,
- statistics and indexes,
- backup and high availability.

## Summary

Parallel Table is powerful because it establishes a clear boundary between the old and new models. We can build V2, test it on real data, and redirect traffic only when ready.

But this is more than `INSERT ... SELECT`. Success depends on delta synchronization, business validation, controlled cutover, a rollback or roll-forward plan, and ending the parallel period.

A new table alongside the old one may be safer than rebuilding in place — provided we plan precisely when the two versions stop running in parallel.
