---
title: "Feature Flags for Schema Changes: Controlled Migration to a New Data Model"
date: 2026-09-23T00:01:00+02:00
slug: feature-flag-schema-change
description: "How to use feature flags during schema migrations and gradually switch reads and writes."
category: "Relational Renaissance"
tags: [SQL Server, feature flags, schema evolution, deployment, data migration]
draft: false
---

# Feature Flags for Schema Changes: Controlled Migration to a New Data Model

A schema change and a feature release do not need to happen at the same time.

We can add a table, deploy code, and only later enable the new model for a subset of traffic. **Feature flags** make this possible.

A flag can control:

- reads from the old or new model,
- writes to one or two structures,
- activation for selected users,
- gradual increases in traffic,
- rapid deactivation without redeploying code.

> A feature flag separates code deployment from activation of new behavior.

## Example Scenario

An application migrates from `Customers.AddressText` to `CustomerAddresses`.

We can define three flags:

```text
UseNewAddressRead
UseNewAddressWrite
EnableAddressV2
```

Each controls a different stage.

## Separate Decisions, Not One Flag

A single `NewAddressModel` flag may be too broad. Reads and writes have different risks.

A better sequence:

1. perform new writes in the background,
2. continue reading from the old model,
3. compare results from both read paths,
4. switch a small group of users,
5. increase the share,
6. disable old writes,
7. remove flags after migration.

## Where Should Flags Be Stored?

Options include:

- a feature-management system,
- application configuration,
- a database table,
- environment variables.

A simple table:

```sql
CREATE TABLE config.FeatureFlags
(
    FeatureName  sysname NOT NULL,
    IsEnabled    bit NOT NULL,
    Percentage   tinyint NULL,
    UpdatedAt    datetime2(0) NOT NULL,
    UpdatedBy    sysname NOT NULL,

    CONSTRAINT PK_FeatureFlags
        PRIMARY KEY (FeatureName),

    CONSTRAINT CK_FeatureFlags_Percentage
        CHECK (Percentage BETWEEN 0 AND 100)
);
```

The application should not query this table before every operation without caching. Propagation delay must also be considered.

## Read Flag

The code can select the data source:

```text
if UseNewAddressRead:
    read CustomerAddresses
else:
    read Customers.AddressText
```

During testing, **shadow reads** are often better:

1. return the old-model result to the user,
2. read the new model as well,
3. compare both results,
4. record differences in telemetry.

Users see no change while the team gathers evidence of compatibility.

## Write Flag

Possible modes:

```text
LegacyOnly
DualWrite
NewOnly
```

These are clearer than several independent booleans that could form invalid combinations.

The database can store the mode:

```sql
CREATE TABLE config.AddressWriteMode
(
    Mode varchar(20) NOT NULL,

    CONSTRAINT CK_AddressWriteMode
        CHECK (Mode IN ('LegacyOnly', 'DualWrite', 'NewOnly'))
);
```

The critical point is to ensure the mode does not change halfway through a transaction and all application instances interpret it consistently.

## Gradual Rollout

Enable the new model for:

- employees,
- test tenants,
- a specific region,
- selected customers,
- a defined percentage of traffic.

Assignment must be stable. The same customer should not randomly switch between V1 and V2 on every request.

A hash of the identifier can be used:

```text
hash(CustomerId) % 100 < Percentage
```

This keeps the selected group stable for a given percentage.

## The Database Must Still Be Compatible

A feature flag does not replace sound schema design.

If turning the flag off must restore the old path, the old model must still hold all data needed to function. Once V2-only information has been stored, reverting the flag may no longer be possible.

The flag can disable code; it does not automatically undo data changes.

## Monitoring

Every activation should be tied to metrics:

- V1 and V2 operation counts,
- errors in each path,
- shadow-read differences,
- response time,
- inconsistent records,
- deadlocks and blocking,
- pending migration queue,
- use of the old model.

Example discrepancy table:

```sql
CREATE TABLE audit.AddressReadDifferences
(
    DifferenceId bigint IDENTITY(1,1) NOT NULL,
    CustomerId   int NOT NULL,
    LegacyValue  nvarchar(500) NULL,
    NewValue     nvarchar(500) NULL,
    DetectedAt   datetime2(0) NOT NULL,

    CONSTRAINT PK_AddressReadDifferences
        PRIMARY KEY (DifferenceId)
);
```

## Emergency Deactivation

A flag should quickly disable the new path. But deactivation must have a precise meaning:

- only reads return to V1,
- writes still go to V2,
- both directions stop,
- the queue must be drained,
- V2 data must be synchronized backward.

Without this definition, a kill switch can create greater inconsistency.

## Feature Flag Technical Debt

Temporary flags should be removed.

Every flag left behind:

- increases the number of code paths,
- complicates tests,
- makes troubleshooting harder,
- can produce combinations nobody anticipated.

For each flag, document:

- owner,
- purpose,
- creation date,
- removal condition,
- maximum lifetime.

## When to Use Them

Feature flags work well when:

- traffic should increase gradually,
- new code can be deployed inactive,
- rapid deactivation is needed,
- shadow reads are useful,
- migration spans multiple application instances.

## When to Be Careful

- the old model cannot represent new data,
- writes span distributed systems,
- flags are propagated inconsistently,
- comparative monitoring is missing,
- the team does not remove flags after migration.

## Summary

Feature flags control the pace of migration to a new schema. They do not change the fundamentals:

- the schema must remain compatible,
- data must be migrated,
- writes must remain consistent,
- results must be compared,
- the old model must eventually be retired.

A flag is not a migration plan. It is a tool for executing that plan gradually without redeploying the application.
