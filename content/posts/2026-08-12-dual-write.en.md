---
title: "Dual Write in a Database: Helpful Bridge or Source of Inconsistency?"
date: 2026-08-11T00:01:00+02:00
slug: "dual-write-baza-danych"
description: "How to safely write to old and new models in parallel during a SQL Server schema migration."
category: "Relacyjny Renesans"
tags:
  - SQL Server
  - dual write
  - migracja danych
  - transakcje
  - spójność danych
draft: false
---

# Dual Write in a Database: Helpful Bridge or Source of Inconsistency?

Schema evolution often involves a period when old and new structures must coexist. Application V1 writes to the old table, while application V2 already expects the new model.

One solution is **Dual Write**: writing the same business operation to two places.

The pattern sounds simple:

1. Write data to the old model.
2. Write data to the new model.
3. Maintain both models until migration is complete.

The biggest problem is that two writes create two possible points of failure.

> Dual Write is not a problem when both writes are atomic. Problems begin when one can succeed and the other can fail.

## Address Migration Example

The old model stores the address in `Customers.AddressText`. The new model uses `CustomerAddresses`.

A temporary procedure can update both:

```sql
CREATE OR ALTER PROCEDURE dbo.usp_CustomerAddress_Save
    @CustomerId   int,
    @AddressLine1 nvarchar(200),
    @PostalCode   nvarchar(20),
    @City         nvarchar(100)
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    BEGIN TRANSACTION;

    UPDATE dbo.Customers
    SET AddressText = CONCAT(
        @AddressLine1,
        N', ',
        @PostalCode,
        N' ',
        @City
    )
    WHERE CustomerId = @CustomerId;

    MERGE dbo.CustomerAddresses AS target
    USING
    (
        SELECT
            @CustomerId AS CustomerId,
            @AddressLine1 AS AddressLine1,
            @PostalCode AS PostalCode,
            @City AS City
    ) AS source
        ON target.CustomerId = source.CustomerId
       AND target.IsPrimary = 1
    WHEN MATCHED THEN
        UPDATE SET
            AddressLine1 = source.AddressLine1,
            PostalCode = source.PostalCode,
            City = source.City
    WHEN NOT MATCHED THEN
        INSERT
        (
            CustomerId,
            AddressType,
            AddressLine1,
            PostalCode,
            City,
            IsPrimary
        )
        VALUES
        (
            source.CustomerId,
            'Other',
            source.AddressLine1,
            source.PostalCode,
            source.City,
            1
        );

    COMMIT;
END;
```

Both writes are part of one SQL Server transaction. If the second write fails, the first is rolled back as well.

In practice, many teams prefer explicit `UPDATE` and `INSERT` statements over `MERGE`, because concurrency and complex edge cases are easier to control.

## Worst Case: Two Independent Calls

Dangerous application logic can look reasonable:

```text
UPDATE starego modelu
COMMIT

INSERT do nowego modelu
COMMIT
```

If the first step succeeds and the second fails, the models diverge. Retrying the entire operation may execute the first write twice.

The situation becomes even harder when one write targets SQL Server and another targets an external service or message broker. There is no single local transaction covering both resources.

Better options may include:

- Transactional Outbox.
- A change queue.
- Change Data Capture.
- An asynchronous synchronization process.
- One authoritative source of truth.

## Which Model Is the Source of Truth?

Dual Write must have an explicit direction.

### The Old Model Is Authoritative

The new structure is updated secondarily. This can be safer early in migration when most traffic still uses V1.

### The New Model Is Authoritative

The old structure remains only to support legacy reports or V1 applications. This is a natural phase before removing the old model.

### Both Models Are Equally Authoritative

This is the riskiest case. If both can be edited independently, conflict-resolution rules are required. Instead of a controlled migration, you may inadvertently create two systems of record.

## Consistency Validation

During Dual Write, compare the models regularly:

```sql
SELECT
    c.CustomerId,
    LegacyAddress = c.AddressText,
    NewAddress = CONCAT(
        ca.AddressLine1,
        N', ',
        ca.PostalCode,
        N' ',
        ca.City
    )
FROM dbo.Customers AS c
JOIN dbo.CustomerAddresses AS ca
    ON ca.CustomerId = c.CustomerId
   AND ca.IsPrimary = 1
WHERE ISNULL(c.AddressText, N'')
   <> ISNULL(
        CONCAT(
            ca.AddressLine1,
            N', ',
            ca.PostalCode,
            N' ',
            ca.City
        ),
        N''
   );
```

This consistency report belongs in migration monitoring, not just in a one-time test.

Useful measurements include:

- Number of inconsistent records.
- Time since the last synchronization.
- Number of write failures for each model.
- Retry counts.
- Percentage of traffic using V1 versus V2.

## Idempotency

Migration operations must tolerate retries. Useful techniques include:

- Unique business keys.
- `IdempotencyKey`.
- Carefully controlled `UPSERT`.
- A processed-message table.
- Row-version tracking.
- Explicit operation identifiers.

Example operation table:

```sql
CREATE TABLE dbo.ProcessedRequests
(
    RequestId uniqueidentifier NOT NULL,
    ProcessedAt datetime2(0) NOT NULL,
    ResultCode varchar(30) NOT NULL,

    CONSTRAINT PK_ProcessedRequests
        PRIMARY KEY (RequestId)
);
```

Before writing, the application or procedure can check whether the request was already processed.

## How Long Should Dual Write Remain?

As briefly as possible.

Dual Write is transitional. The longer it stays, the greater the risk that it becomes permanent architecture. Every change must then accommodate two models, and the team loses confidence about which one is authoritative.

Define exit conditions before rollout:

- All application instances run V2.
- Historical data migration is complete.
- The consistency report shows zero differences for an agreed period.
- Legacy reports and integrations have been switched.
- Monitoring confirms that no consumers use the old model.

## When Should You Use It?

Dual Write can work well when:

- Both writes occur in the same database transaction.
- The coexistence period is short.
- A zero-downtime cutover is required.
- A comparison report checks both models.
- The source of truth is clearly defined.

## When Should You Avoid It?

Be particularly cautious when:

- Writes target different systems.
- Atomicity cannot be guaranteed.
- Both models can be independently edited.
- There is no retry and idempotency mechanism.
- Nobody has set a date to remove the temporary solution.

## Summary

Dual Write is a useful bridge during schema evolution. But it should not be treated as an innocent instruction to “write twice.”

Safe Dual Write requires:

- Atomicity.
- One source of truth.
- Idempotency.
- Inconsistency monitoring.
- A short lifespan.
- A clear retirement plan.

The most important question is not:

> Can we write to two places?

It is:

> What will we do when one of those writes fails?
