---
title: "Compatibility View: Changing the Data Model Without Breaking Legacy Reports"
date: 2026-09-02T00:01:00+02:00
slug: "compatibility-view-legacy-reports"
description: "A compatibility view as a transitional layer between the old data contract and a new SQL Server model."
category: "Relational Renaissance"
tags: [SQL Server, views, compatibility, reporting, schema migration]
draft: false
---

# Compatibility View: Changing the Data Model Without Breaking Legacy Reports

Changing a data model does not end with the application. Tables are also consumed by:

- reports,
- ETL processes,
- integrations,
- user spreadsheets,
- ad hoc queries,
- systems the database team may not even know exist.

The **Compatibility View** pattern creates a view that exposes the new model in the format expected by legacy consumers.

> A compatibility view separates the physical data structure from a temporary contract that must still be supported.

## Scenario

The old customer table contained:

```sql
dbo.Customers
(
    CustomerId,
    CustomerName,
    AddressText
)
```

After normalization, addresses live in `CustomerAddresses`.

The old report still executes:

```sql
SELECT
    CustomerId,
    CustomerName,
    AddressText
FROM dbo.Customers;
```

Removing the column immediately would break the report.

## Compatibility View

We can create a view that reconstructs the legacy format:

```sql
CREATE OR ALTER VIEW dbo.vw_Customers_Legacy
AS
    SELECT
        c.CustomerId,
        c.CustomerName,
        AddressText =
            CONCAT(
                ca.AddressLine1,
                CASE
                    WHEN ca.PostalCode IS NOT NULL
                      OR ca.City IS NOT NULL
                    THEN N', '
                    ELSE N''
                END,
                COALESCE(ca.PostalCode + N' ', N''),
                COALESCE(ca.City, N'')
            )
    FROM dbo.Customers AS c
    OUTER APPLY
    (
        SELECT TOP (1)
            a.AddressLine1,
            a.PostalCode,
            a.City
        FROM dbo.CustomerAddresses AS a
        WHERE a.CustomerId = c.CustomerId
        ORDER BY
            a.IsPrimary DESC,
            a.CustomerAddressId
    ) AS ca;
```

The report can switch from the table to the view without needing to understand the new model.

## Preserving the Old Object Name

Sometimes a more aggressive approach is used:

1. Rename the old table.
2. Create a view under the old name.
3. Keep the new model in other tables.

Conceptual example:

```sql
EXEC sys.sp_rename
    N'dbo.Customers',
    N'Customers_Internal';

CREATE VIEW dbo.Customers
AS
SELECT ...
```

This may reduce changes required by consumers, but it demands thorough testing. Applications may expect a table, perform writes, use hints, or rely on specific metadata.

Renaming an object with `sp_rename` does not automatically update every textual reference.

## Read-Only or Writable View?

The safest compatibility view is read-only.

Simple views can sometimes be updated automatically. For complex mappings, an `INSTEAD OF TRIGGER` can be used, but it introduces hidden complexity.

```sql
CREATE OR ALTER TRIGGER dbo.tr_CustomersLegacy_Update
ON dbo.vw_Customers_Legacy
INSTEAD OF UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    -- Jawne przepisanie starego kontraktu
    -- na operacje w nowym modelu.
END;
```

The trigger must handle multirow operations, errors, transactions, and concurrency correctly. It should therefore be a temporary mechanism, not a permanent database API.

## A Stable Contract

The compatibility view must faithfully preserve:

- column names,
- data types,
- value semantics,
- `NULL` handling,
- row counts,
- data-selection rules.

If the new model stores several addresses while the old contract exposes one, decide which address to return. Usually it is the primary address, but the rule must be explicit.

Without that rule, the view may return duplicate customers and change report results.

## Performance

A regular view does not store data. Each query executes its definition.

If a report previously read one table but now joins several large tables through a view, performance may deteriorate.

Check:

- execution plans,
- indexes on join keys,
- filter selectivity,
- post-join row counts,
- functions and type conversions,
- report parameter behavior.

Example index:

```sql
CREATE INDEX IX_CustomerAddresses_Customer_Primary
ON dbo.CustomerAddresses
(
    CustomerId,
    IsPrimary
)
INCLUDE
(
    AddressLine1,
    PostalCode,
    City
);
```

## Versioning Views

Instead of a single “legacy” object, contracts can be explicitly versioned:

```text
reporting.vw_Customers_v1
reporting.vw_Customers_v2
```

This improves transparency. Consumers know which version they use, and the team can plan retirement of V1.

Record:

- each consumer's owner,
- planned migration date,
- retirement date for the old view,
- how usage will be monitored.

## How Do We Know Whether the View Is Still Used?

SQL Server does not keep a complete history of every consumer. Useful sources include:

- Query Store,
- Extended Events,
- plan cache analysis,
- reporting logs,
- source-code repositories,
- query auditing,
- error monitoring after a controlled disablement in a test environment.

A compatibility view without an owner and retirement date is likely to remain indefinitely.

## When Should You Use It?

Compatibility View works well when:

- the physical model changes but the legacy read format is still needed,
- reports migrate more slowly than the application,
- a controlled transition period is required,
- the mapping between the old and new contract is unambiguous.

## When Should You Avoid It?

A view may be unsuitable when:

- heavy write activity is required,
- mapping loses data meaning,
- queries become very expensive,
- a consumer depends on table-specific behavior,
- the compatibility layer has no defined lifetime.

## Summary

Compatibility View is an effective transitional layer. It lets the data model evolve without switching all reports and integrations at once.

But it must not hide the problem forever.

A good compatibility view has a clearly defined contract, result tests, an acceptable execution plan, an owner, usage monitoring, and a retirement date.

Its purpose is to buy time for migration, not to stop schema evolution.
