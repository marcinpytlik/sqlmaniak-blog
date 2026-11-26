---
title: "Foreign Keys Without Surprises: Safely Adding a Relationship to Existing Data"
date: 2026-11-25T08:00:00+01:00
slug: "foreign-key-bezpieczne-wdrozenie"
description: "Adding a foreign key to an existing data model: identify orphan rows first, then enforce referential integrity."
category: "Relacyjny Renesans"
tags:
  - SQL Server
  - foreign key
  - schema evolution
  - data quality
  - database DevOps
draft: false
---

# Foreign Keys Without Surprises: Safely Adding a Relationship to Existing Data

Adding a foreign key to an empty table is straightforward.

In an existing system, first check whether the data already satisfies the new rule.

## Find Orphan Rows

```sql
SELECT c.CustomerId
FROM dbo.Orders AS c
LEFT JOIN dbo.Customers AS p
    ON p.CustomerId = c.CustomerId
WHERE p.CustomerId IS NULL;
```

If this query returns rows, the constraint will not repair the data for us.

## Fix the Data First

Determine what the orphaned records mean:

- Historical data errors.
- Deleted parent records.
- Missing backfill.
- A legitimate business exception.

## Add the Constraint

```sql
ALTER TABLE dbo.Orders WITH CHECK
ADD CONSTRAINT FK_Orders_Customers
FOREIGN KEY (CustomerId)
REFERENCES dbo.Customers(CustomerId);
```

`WITH CHECK` validates existing data.

## Untrusted Constraints

A constraint created using `WITH NOCHECK` may exist without being trusted by the engine.

Check:

```sql
SELECT
    name,
    is_disabled,
    is_not_trusted
FROM sys.foreign_keys
WHERE parent_object_id = OBJECT_ID(N'dbo.Orders');
```

## Validate Later

If the migration requires a transitional phase, clean up the data first and then run:

```sql
ALTER TABLE dbo.Orders WITH CHECK
CHECK CONSTRAINT FK_Orders_Customers;
```

## Performance

The child-side column generally benefits from an appropriate index, especially for frequent joins and deletion of parent records.

## Summary

A foreign key is not merely a model declaration. It is evidence that existing data satisfies the relationship.

Data quality first; enforcement second.
