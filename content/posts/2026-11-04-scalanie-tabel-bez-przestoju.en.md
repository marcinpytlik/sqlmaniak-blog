---
title: "Merging Tables Without Downtime: When Two Data Models Become One"
date: 2026-11-04T08:00:00+01:00
slug: "merging-tables-without-downtime"
description: "How to safely merge data from several tables into a new unified model without switching the entire application over in a single step."
category: "Relational Renaissance"
tags:
  - SQL Server
  - schema evolution
  - data migration
  - zero downtime
  - database DevOps
draft: false
---

Splitting a table is one direction of schema evolution. Sometimes, after years of development, we need to do the opposite: combine several structures into a single model.

## Example

We have:

```text
RetailCustomer
BusinessCustomer
```

And we want to move to:

```text
Customer
```

## The New Model

```sql
CREATE TABLE dbo.CustomerV2
(
    CustomerId bigint NOT NULL PRIMARY KEY,
    CustomerType varchar(20) NOT NULL,
    DisplayName nvarchar(200) NOT NULL,
    TaxId nvarchar(30) NULL
);
```

## Map the Semantics First

Merging tables is not simply a matter of running `UNION ALL`.

We need to establish:

- how keys are mapped,
- which columns have the same meaning,
- how to handle identifier collisions,
- how to represent fields that exist in only one of the original models.

## A Stable Key

If the original tables can contain the same `CustomerId`, a mapping layer is needed.

```sql
CREATE TABLE migration.CustomerKeyMap
(
    SourceType varchar(20) NOT NULL,
    SourceId bigint NOT NULL,
    TargetId bigint NOT NULL,
    CONSTRAINT PK_CustomerKeyMap
        PRIMARY KEY (SourceType, SourceId)
);
```

## Backfill and Delta Changes

First, migrate the historical state. Then synchronize changes arriving while the migration is in progress.

Change Data Capture (CDC), an event queue, or dual writes can serve this purpose.

## Switching Consumers

Not every application has to switch at the same time.

We can migrate these consumers first:

- new APIs,
- reports,
- a selected application module,
- batch processes.

## The Biggest Pitfall

Do not remove the old tables merely because the new one has been populated successfully.

First, demonstrate that nothing still depends on the old contract.

## Summary

Merging tables means migrating data, keys, and semantics at the same time.

Without key mapping and telemetry, it is easy to create a new model that cannot be safely validated.

**Related reading:** [Splitting a Table Without a Big Bang](/en/posts/split-table-without-big-bang/) explores the reverse migration.
