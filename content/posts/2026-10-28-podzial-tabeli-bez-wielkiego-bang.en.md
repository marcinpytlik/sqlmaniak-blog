---
title: "Splitting a Table Without a Big Bang: From One Data Model to Two"
date: 2026-10-28T08:00:00+01:00
slug: "split-table-without-big-bang"
description: "How to safely split a wide table into two structures without rewriting the entire application and migrating all data in a single cutover."
category: "Relational Renaissance"
tags:
  - SQL Server
  - schema evolution
  - normalization
  - data migration
  - database DevOps
draft: false
---

# Splitting a Table Without a Big Bang: From One Data Model to Two

Imagine that, over the years, a `Customer` table has grown to contain dozens of columns.

We want to move some of the address information into a separate table.

## The New Table

```sql
CREATE TABLE dbo.CustomerAddress
(
    CustomerId int NOT NULL,
    AddressType varchar(20) NOT NULL,
    AddressLine1 nvarchar(200) NOT NULL,
    City nvarchar(100) NOT NULL,
    PostalCode nvarchar(20) NULL,
    CONSTRAINT PK_CustomerAddress
        PRIMARY KEY (CustomerId, AddressType)
);
```

## Step 1 — Introduce the New Structure Without Removing the Old One

The existing columns remain in place. The new table extends the data model.

## Step 2 — Backfill the Data

```sql
INSERT dbo.CustomerAddress
(
    CustomerId, AddressType, AddressLine1, City, PostalCode
)
SELECT
    CustomerId, 'PRIMARY', AddressLine1, City, PostalCode
FROM dbo.Customer
WHERE AddressLine1 IS NOT NULL;
```

For large tables, perform the backfill in batches and persist checkpoints.

## Step 3 — Keep the Two Models in Sync

During the transition period, an address change must be reflected in both models, or one model must act as the source of truth and synchronize the other.

## Step 4 — Switch the Read Path

Start with a small portion of the traffic, then gradually increase it.

Shadow reads let you compare results from the old and new representations.

## Step 5 — Remove the Old Columns

This is the final stage, not part of the initial deployment.

Before the contract phase, check:

- reports,
- integrations,
- ETL processes,
- stored procedures,
- dynamic SQL,
- exports,
- BI tools.

## Semantic Risks

Splitting a table often changes not only the physical schema but also the meaning of the data.

One address may become multiple addresses. In that case, rolling back to the old model can lose information.

## Summary

Splitting a table is safest when we first introduce the new representation, then move the traffic, and only remove the old one at the end.
