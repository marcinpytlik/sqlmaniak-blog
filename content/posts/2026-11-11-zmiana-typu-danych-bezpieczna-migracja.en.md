---
title: "Changing a Data Type Without a Major Blocking Operation: Add a Column Instead of ALTER COLUMN"
date: 2026-11-11T08:00:00+01:00
slug: safe-data-type-migration-new-column
description: "How to change a data type in a large table in stages instead of running a risky ALTER COLUMN against a live system."
category: "Relational Renaissance"
tags:
  - SQL Server
  - schema evolution
  - data type
  - zero downtime
  - database DevOps
draft: false
---

# Changing a Data Type Without a Major Blocking Operation: Add a Column Instead of ALTER COLUMN

`ALTER COLUMN` looks harmless until the table contains hundreds of millions of rows.

Changing a data type may require rebuilding data, indexes, and dependencies.

## Example

We want to move from:

```text
OrderNumber varchar(20)
```

to:

```text
OrderNumber bigint
```

## Step 1 — Add a New Column

```sql
ALTER TABLE dbo.Orders
ADD OrderNumberBigint bigint NULL;
```

## Step 2 — Validate the Conversion

```sql
SELECT OrderNumber
FROM dbo.Orders
WHERE TRY_CONVERT(bigint, OrderNumber) IS NULL
  AND OrderNumber IS NOT NULL;
```

First, identify the rows that cannot be migrated.

## Step 3 — Backfill in Batches

```sql
UPDATE TOP (10000) dbo.Orders
SET OrderNumberBigint = TRY_CONVERT(bigint, OrderNumber)
WHERE OrderNumberBigint IS NULL
  AND OrderNumber IS NOT NULL;
```

## Step 4 — Dual Write

The new application version writes both representations or writes one and synchronizes the other.

## Step 5 — Switch Reads

After validation, the new column becomes the source for reads.

## Indexes

Remember that indexes depending on the old column must be planned separately.

You can prepare the new index before switching:

```sql
CREATE INDEX IX_Orders_OrderNumberBigint
ON dbo.Orders(OrderNumberBigint);
```

## Contract

Remove the old column only when:

- all reads use the new column,
- all writes use the new column,
- integrations have been switched,
- the data has been validated,
- rollback no longer requires the old representation.

## Summary

Changing a data type does not have to be a single DDL operation.

A new column, backfill, validation, and cutover give you much greater control over risk.