---
title: "Soft Delete in SQL Server and EF Core — Convenience That Can Create Problems"
date: 2026-09-22
slug: soft-delete-sql-server-ef-core-pitfalls
description: "Soft delete in SQL Server and EF Core: global query filters, filtered unique indexes, auditing, relationships and common pitfalls."
tags: [SQLServer, EFCore, SoftDelete, Indexes, DataModeling]
categories: [SQL Server]
draft: false
---

Soft delete means marking a record as deleted without physically removing it from the table.

Typically, we add `IsDeleted`, `DeletedAt` and `DeletedBy`.

However, this approach affects uniqueness, indexes, relationships, reporting and retention.

## Example Model

```sql
CREATE TABLE dbo.Customer
(
    CustomerId int IDENTITY(1,1) NOT NULL,
    Email nvarchar(320) NOT NULL,
    DisplayName nvarchar(200) NOT NULL,
    IsDeleted bit NOT NULL
        CONSTRAINT DF_Customer_IsDeleted DEFAULT (0),
    DeletedAt datetime2(0) NULL,
    DeletedBy nvarchar(200) NULL,
    CONSTRAINT PK_Customer PRIMARY KEY CLUSTERED (CustomerId)
);
```

## The Uniqueness Problem

A conventional `UNIQUE` constraint prevents an email address from being reused after soft deletion.

A filtered index solves this:

```sql
CREATE UNIQUE INDEX UX_Customer_Email_Active
ON dbo.Customer(Email)
WHERE IsDeleted = 0;
```

## Global Query Filter in EF Core

```csharp
public sealed class CustomerConfiguration
    : IEntityTypeConfiguration<Customer>
{
    public void Configure(EntityTypeBuilder<Customer> builder)
    {
        builder.HasQueryFilter(customer => !customer.IsDeleted);
    }
}
```

To bypass the filter:

```csharp
var allCustomers = await dbContext.Customers
    .IgnoreQueryFilters()
    .ToListAsync();
```

## Relationships and Cascades

What should happen to orders when their customer is soft-deleted?

Possible approaches:

- orders remain visible,
- orders become invisible,
- orders are also soft-deleted,
- deleting the customer is prohibited.

The rule must be designed explicitly.

## Auditing

Soft delete is not a complete audit trail. It does not show previous values or the reason for a change.

A complete history may require:

- temporal tables,
- an audit table,
- CDC,
- application logs.

## Summary

Soft delete is a business pattern, not just an extra column.

A careful designer asks:

> Why must the data remain, who may see it, and what does restoring it mean?
