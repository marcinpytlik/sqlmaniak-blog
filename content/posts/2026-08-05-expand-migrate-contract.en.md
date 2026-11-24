---
title: "Expand–Migrate–Contract: Changing a Schema Without Stopping the Application"
date: 2026-08-05T00:01:00+02:00
slug: "expand-migrate-contract-ewolucja-schematu"
description: "A practical pattern for safe SQL Server schema evolution: expand the model, migrate data, maintain compatibility, validate, and remove the old structure."
category: "Relacyjny Renesans"
tags:
  - SQL Server
  - projektowanie baz danych
  - ewolucja schematu
  - deployment
  - migracja danych
draft: false
---

# Expand–Migrate–Contract: Changing a Schema Without Stopping the Application

Designing a new table is relatively easy. Changing a table already used by applications, reports, ETL processes, and users is much harder.

In a lab, we can run `ALTER TABLE`, fix the code, and restart everything. In production, however, two application versions may run side by side for some time. A report might still expect the old column, while an integration job runs only once per day and exposes a problem hours after deployment.

The **Expand–Migrate–Contract** pattern divides a change into controlled stages:

1. **Expand** — add the new structure without removing the old one.
2. **Migrate** — move data and application traffic.
3. **Validate** — verify completeness and actual use of the old model.
4. **Contract** — only then remove the old structure.

The key principle:

> A schema change is a deployment process, not a single DDL statement.

## Example Problem

Suppose the first version of a system stores the customer address in one column:

```sql
CREATE TABLE dbo.Customers
(
    CustomerId   int IDENTITY(1,1) NOT NULL,
    CustomerName nvarchar(200) NOT NULL,
    AddressText  nvarchar(500) NULL,

    CONSTRAINT PK_Customers
        PRIMARY KEY (CustomerId)
);
```

Over time, the business needs to:

- store several addresses,
- distinguish billing and shipping addresses,
- filter customers by city,
- integrate with a courier company.

A separate address table is a natural target model. Immediately dropping `AddressText`, however, would be risky.

## Stage 1: Expand

First, add the new table:

```sql
CREATE TABLE dbo.CustomerAddresses
(
    CustomerAddressId bigint IDENTITY(1,1) NOT NULL,
    CustomerId        int NOT NULL,
    AddressType       varchar(20) NOT NULL,
    AddressLine1      nvarchar(200) NOT NULL,
    PostalCode        nvarchar(20) NULL,
    City              nvarchar(100) NULL,
    CountryCode       char(2) NOT NULL,
    IsPrimary         bit NOT NULL,

    CONSTRAINT PK_CustomerAddresses
        PRIMARY KEY (CustomerAddressId),

    CONSTRAINT FK_CustomerAddresses_Customers
        FOREIGN KEY (CustomerId)
        REFERENCES dbo.Customers(CustomerId)
);
```

The old column remains. Application V1 can continue working unchanged while application V2 is prepared to use the new model.

An additive change is usually easier to deploy than a destructive one. Adding a table does not break the existing contract; dropping a column does.

## Stage 2: Migrate

Data must be moved into the new model. For a small table, one `INSERT ... SELECT` is enough. For a large table, use batches.

```sql
WHILE 1 = 1
BEGIN
    ;WITH Batch AS
    (
        SELECT TOP (1000)
            c.CustomerId,
            c.AddressText
        FROM dbo.Customers AS c
        WHERE c.AddressText IS NOT NULL
          AND NOT EXISTS
          (
              SELECT 1
              FROM dbo.CustomerAddresses AS ca
              WHERE ca.CustomerId = c.CustomerId
          )
        ORDER BY c.CustomerId
    )
    INSERT INTO dbo.CustomerAddresses
    (
        CustomerId,
        AddressType,
        AddressLine1,
        CountryCode,
        IsPrimary
    )
    SELECT
        CustomerId,
        'Other',
        AddressText,
        'PL',
        1
    FROM Batch;

    IF @@ROWCOUNT = 0
        BREAK;
END;
```

Batch migration reduces:

- individual transaction duration,
- transaction-log growth,
- lock duration,
- risk of lengthy rollback,
- impact on normal system operation.

The process should be idempotent or at least resumable. Restarting it must not create duplicates.

## Compatibility Period

Old and new application versions may run concurrently for a while. You must decide how to maintain consistency.

Possible solutions include:

- temporary dual writes,
- one stored procedure writing both models,
- a compatibility view,
- disabling V1 writes once all application instances have switched.

Dual writes can be useful but add complexity. If one write succeeds and the other fails, the models diverge. Both writes should therefore be part of one local transaction.

## Validation Before Removing the Old Model

Do not drop a column just because the new application has been deployed. You need evidence.

A basic completeness check:

```sql
SELECT
    c.CustomerId,
    c.CustomerName,
    c.AddressText
FROM dbo.Customers AS c
WHERE c.AddressText IS NOT NULL
  AND NOT EXISTS
  (
      SELECT 1
      FROM dbo.CustomerAddresses AS ca
      WHERE ca.CustomerId = c.CustomerId
  );
```

The query should return zero rows.

Also inspect module dependencies:

```sql
SELECT
    ReferencingSchema = OBJECT_SCHEMA_NAME(d.referencing_id),
    ReferencingObject = OBJECT_NAME(d.referencing_id),
    d.referenced_entity_name
FROM sys.sql_expression_dependencies AS d
WHERE d.referenced_id = OBJECT_ID(N'dbo.Customers');
```

That still does not guarantee full coverage. Dynamic SQL, application code, and external reports may not appear in the metadata. In practice, also use Query Store, Extended Events, application error monitoring, and code repository analysis.

## Stage 3: Contract

Only after migration is complete and application V1 has been retired should you remove the old structure:

```sql
ALTER TABLE dbo.Customers
    DROP COLUMN AddressText;
```

Before doing so, remove or update:

- stored procedures referencing the column,
- compatibility views,
- triggers,
- indexes,
- reports,
- ETL processes,
- ORM mappings.

The `Contract` stage should be a separate deployment. Keeping it apart from `Expand` gives you time to observe the system and safely roll back application code.

## Rollback or Roll Forward?

Rolling back code does not always mean that a database migration can be reversed. If the new application has written data that the old model cannot represent, going back may lose information.

Decide in advance:

- up to which point rollback is possible,
- when to switch to a roll-forward strategy,
- how to recover data after an incomplete migration,
- which metrics trigger a deployment stop.

## When Should You Use This Pattern?

Expand–Migrate–Contract is especially useful when:

- deployments cannot require lengthy downtime,
- the application runs on multiple instances,
- reports and integrations share the schema,
- data migration takes a long time,
- a controlled cutover is required.

## Costs

The pattern is not free. For a while, you maintain two models, extra compatibility code, and more deployment steps. You also need monitoring and a cleanup procedure.

That is the cost of controlled change. The alternative is a big-bang deployment where any hidden consumer of the old structure may stop the system.

## Summary

Mature schema evolution does not start with the question:

> Will the `ALTER TABLE` statement execute?

It starts with:

- Will the system remain operational during the change?
- Will both application versions remain compatible?
- Can the migration be resumed?
- How will we verify data completeness?
- When is it safe to remove the old model?

Expand–Migrate–Contract turns a risky change into a sequence of small, observable, and reversible steps. That is why it is a fundamental pattern for evolving relational databases.
