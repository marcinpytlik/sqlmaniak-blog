---
title: "Backfill in Batches: Migrating Millions of Rows Without One Huge Transaction"
date: 2026-08-25T00:01:00+02:00
slug: "backfill-in-batches-sql-server"
description: "A practical approach to populating new columns and migrating SQL Server data in batches."
category: "Relational Renaissance"
tags:
  - SQL Server
  - backfill
  - data migration
  - transaction log
  - locking
draft: false
---

# Backfill in Batches: Migrating Millions of Rows Without One Huge Transaction

Adding a new column is often only the beginning of a schema change. You still need to populate it for historical records.

The simplest solution is:

```sql
UPDATE dbo.Orders
SET OrderSource = 'Legacy'
WHERE OrderSource IS NULL;
```

This may work well for a table containing a few thousand rows. On a table with hundreds of millions of rows, however, it can cause:

- rapid transaction-log growth,
- long-held locks,
- lock escalation,
- replication or Availability Group lag,
- expensive rollback after interruption,
- disruption to backups and maintenance windows.

The **Backfill in Batches** pattern divides the work into small, repeatable transactions.

> The goal is not to finish the migration as quickly as possible. It is to proceed at a pace the production system can safely sustain.

## Example Schema

```sql
CREATE TABLE dbo.Orders
(
    OrderId     bigint IDENTITY(1,1) NOT NULL,
    CustomerId  int NOT NULL,
    CreatedAt   datetime2(0) NOT NULL,
    OrderSource varchar(30) NULL,

    CONSTRAINT PK_Orders
        PRIMARY KEY (OrderId)
);
```

The new `OrderSource` column allows `NULL` to avoid forcing an immediate rewrite of the entire table.

## The Simplest Loop

```sql
WHILE 1 = 1
BEGIN
    UPDATE TOP (5000) dbo.Orders
    SET OrderSource = 'Legacy'
    WHERE OrderSource IS NULL;

    IF @@ROWCOUNT = 0
        BREAK;
END;
```

This is already better than one enormous transaction, but it is not ideal. Each batch may scan a large portion of the table again.

## Key-Based Migration

A better approach tracks the last processed key:

```sql
DECLARE
    @BatchSize   int = 5000,
    @LastOrderId bigint = 0,
    @MaxOrderId  bigint;

SELECT @MaxOrderId = MAX(OrderId)
FROM dbo.Orders;

WHILE @LastOrderId < @MaxOrderId
BEGIN
    UPDATE dbo.Orders
    SET OrderSource = 'Legacy'
    WHERE OrderId > @LastOrderId
      AND OrderId <= @LastOrderId + @BatchSize
      AND OrderSource IS NULL;

    SET @LastOrderId += @BatchSize;
END;
```

This version is predictable but assumes relatively continuous keys. With large gaps, selecting actual batch identifiers works better.

```sql
DECLARE @BatchSize int = 5000;

WHILE 1 = 1
BEGIN
    CREATE TABLE #Batch
    (
        OrderId bigint NOT NULL PRIMARY KEY
    );

    INSERT INTO #Batch(OrderId)
    SELECT TOP (@BatchSize)
        o.OrderId
    FROM dbo.Orders AS o WITH (READPAST)
    WHERE o.OrderSource IS NULL
    ORDER BY o.OrderId;

    IF @@ROWCOUNT = 0
        BREAK;

    UPDATE o
    SET OrderSource = 'Legacy'
    FROM dbo.Orders AS o
    JOIN #Batch AS b
        ON b.OrderId = o.OrderId;

    DROP TABLE #Batch;
END;
```

**Practical caution:** This demonstration creates `#Batch` inside the loop and breaks before dropping it when no rows are found. In a real implementation, ensure the temporary table is cleaned up and that `READPAST` behavior is appropriate for the isolation level and concurrency model. A temporary filtered index may also be necessary to avoid repeated scans.

## Resumability

The process can be interrupted by a restart, deployment, or maintenance window. It should therefore be resumable.

A control table is useful:

```sql
CREATE TABLE dbo.DataMigrationState
(
    MigrationName   sysname NOT NULL,
    LastProcessedId bigint NOT NULL,
    RowsProcessed   bigint NOT NULL,
    LastBatchAt     datetime2(0) NULL,
    CompletedAt     datetime2(0) NULL,

    CONSTRAINT PK_DataMigrationState
        PRIMARY KEY (MigrationName)
);
```

Update the state after each batch. This lets you know:

- where the process stopped,
- how many rows were processed,
- when the most recent batch completed,
- whether migration has finished.

## Batch Size

There is no universally correct value. A batch of `100`, `5000`, or `50000` may be appropriate depending on:

- row width,
- index count,
- type of update,
- storage performance,
- system workload,
- log throughput,
- replication and high availability.

A good approach is to start small and observe:

- batch duration,
- logged bytes,
- locking,
- replica lag,
- CPU and I/O usage.

## Controlling the Pace

You can introduce a pause:

```sql
WAITFOR DELAY '00:00:00.250';
```

You can also stop the migration when the system is busy or replica lag exceeds a defined threshold. In practice, throttling should remain simple and predictable.

## Supporting Index

The predicate:

```sql
WHERE OrderSource IS NULL
```

may require a full scan. A temporary filtered index can greatly accelerate the migration:

```sql
CREATE INDEX IX_Orders_Backfill_OrderSource
ON dbo.Orders(OrderId)
WHERE OrderSource IS NULL;
```

After migration, remove it:

```sql
DROP INDEX IX_Orders_Backfill_OrderSource
ON dbo.Orders;
```

However, account for the cost of building the index and the additional write overhead while migrating.

## Concurrency with the Application

If the application inserts new rows, it should populate the new column immediately. Otherwise the backfill will constantly chase new `NULL` values.

Typical sequence:

1. Add the column as nullable.
2. Deploy application code that writes the new value.
3. Backfill historical rows.
4. Verify that no `NULL` values remain.
5. Apply `NOT NULL`.

## Validation

After migration, “the job succeeded” is not enough.

```sql
SELECT COUNT_BIG(*) AS MissingRows
FROM dbo.Orders
WHERE OrderSource IS NULL;
```

The result should be zero.

It is also worth comparing aggregates, checksums, or derived values from the old and new models.

## What About Rollback?

Each batch is a separate transaction, so rollback affects only the current batch. Completed batches are not automatically undone.

Before migrating, determine whether:

- the new value can be recalculated,
- a change-tracking table is needed,
- the migration is reversible,
- errors should be corrected by moving forward.

## When Should You Use It?

Batch backfill is appropriate when:

- the table is large,
- the system must stay available,
- the update affects the log and locking,
- migration may take hours or days,
- the process must resume after interruption.

## When Is One Transaction Better?

On a small table, a straightforward `UPDATE` can be clearer and safer. Do not complicate migration unnecessarily. First understand the data volume and operation cost.

## Summary

Backfill in Batches is an operational pattern. The `UPDATE` statement itself is not the hardest part. The challenge is controlling the impact on a running system.

A good batch migration is:

- resumable,
- idempotent,
- monitored,
- validated,
- adapted to workload,
- completed by removing temporary mechanisms.

Millions of rows do not have to mean one huge transaction. They can mean thousands of small, predictable steps.
