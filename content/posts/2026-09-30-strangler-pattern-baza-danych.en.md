---
title: "The Strangler Pattern for Databases: Retiring the Old Model Without a Big Cutover"
date: 2026-09-30T00:01:00+02:00
slug: strangler-pattern-database
description: "Gradually replace an old data model without one risky migration cutover."
category: "Relational Renaissance"
tags: [SQL Server, schema evolution, strangler pattern, data migration, database DevOps]
draft: false
---

# The Strangler Pattern for Databases: Retiring the Old Model Without a Big Cutover

After feature flags, the natural next question is: **how do we retire the old model without one major cutover?**

One approach is the Strangler Pattern. A new part of the system gradually assumes responsibility for operations until the old structure is no longer needed.

> Do not migrate everything at once. Transfer responsibility piece by piece.

## Example

Old model:

```sql
CREATE TABLE dbo.Customer
(
    CustomerId int NOT NULL PRIMARY KEY,
    Name nvarchar(200) NOT NULL,
    AddressText nvarchar(500) NULL
);
```

New model:

```sql
CREATE TABLE dbo.CustomerAddress
(
    CustomerAddressId bigint IDENTITY(1,1) NOT NULL PRIMARY KEY,
    CustomerId int NOT NULL,
    AddressLine1 nvarchar(200) NOT NULL,
    City nvarchar(100) NOT NULL,
    PostalCode nvarchar(20) NULL
);
```

## Stage 1 — New Writes

First, route new operations to the new model while keeping the old one compatible.

For a period, we may use:

- dual writes,
- writes to the new model with backward synchronization,
- an event queue that updates the legacy structure.

## Stage 2 — New Reads

Next, selected reads move to the new table. A feature flag limits the rollout.

Start with shadow reads and compare results without affecting users.

## Stage 3 — Isolate the Old Model

Applications should no longer access the old table directly.

Useful mechanisms include:

- compatibility views,
- stored procedures as an access layer,
- a dedicated `legacy` schema,
- monitoring queries that still reach the old object.

## Stage 4 — Retirement

Remove the old model only when there is evidence that:

- no active reads remain,
- no active writes remain,
- backfill completed successfully,
- integrations have been switched,
- rollback no longer depends on the old structure.

## Biggest Risk

The Strangler Pattern fails when the old and new models remain competing sources of truth for too long.

Clearly define which model is authoritative at every migration stage.

## Summary

The Strangler Pattern replaces one large migration with a series of small, controlled transfers of responsibility.

The Relational Renaissance is not about revolution. It is about making the old model unnecessary in a controlled way.
