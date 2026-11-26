---
title: "CDC as a Migration Tool: Backfill Is Only the Beginning"
date: 2026-10-07T00:01:00+02:00
slug: "cdc-jako-narzedzie-migracji"
description: "Using Change Data Capture to synchronize changes during large-table and schema migrations."
category: "Relacyjny Renesans"
tags:
  - SQL Server
  - CDC
  - migracja danych
  - schema evolution
  - database DevOps
draft: false
---

# CDC as a Migration Tool: Backfill Is Only the Beginning

For a large table, a single `INSERT ... SELECT` followed by hours of application downtime is not always practical.

We need two components:

1. A historical data backfill.
2. Synchronization of changes occurring during the migration.

CDC can help with the second component.

## Process Outline

```text
T0  uruchom CDC
T1  rozpocznij backfill
T2  aplikacja nadal zapisuje do starej tabeli
T3  odczytuj zmiany z CDC
T4  aplikuj deltę do nowego modelu
T5  wyrównaj opóźnienie
T6  przełącz odczyt i zapis
```

## Enabling CDC

```sql
EXEC sys.sp_cdc_enable_db;
GO

EXEC sys.sp_cdc_enable_table
    @source_schema = N'dbo',
    @source_name   = N'Orders',
    @role_name     = NULL,
    @supports_net_changes = 1;
GO
```

## LSN Rather Than Time

Do not base synchronization on `ModifiedDate` if you need the complete order of changes.

CDC operates on log sequence numbers (LSNs), allowing you to identify a range:

```sql
DECLARE @from_lsn binary(10) = sys.fn_cdc_get_min_lsn(N'dbo_Orders');
DECLARE @to_lsn   binary(10) = sys.fn_cdc_get_max_lsn();
```

## Idempotency

The synchronization process should tolerate reprocessing a range. A reliable approach is to store a checkpoint:

```sql
CREATE TABLE migration.CdcCheckpoint
(
    PipelineName sysname NOT NULL PRIMARY KEY,
    LastProcessedLsn binary(10) NOT NULL,
    UpdatedAt datetime2(0) NOT NULL
);
```

## The Cleanup Problem

CDC does not retain changes indefinitely. The cleanup job removes older entries.

If the migration pipeline stops for too long, the required range may disappear.

Monitor:

- The oldest available LSN.
- The last processed LSN.
- Pipeline lag.
- Error count.
- Rate of incoming changes.

## Cutover

Before switching, verify that the remaining delta has been reduced to an acceptable level.

This may require:

- Briefly pausing writes.
- Reading the final CDC changes.
- Applying the remaining delta.
- Switching the application.

## CDC Is Not Magical Replication

CDC records changes. You are responsible for interpreting and applying them to the new model.

If one operation in the old model becomes three operations in the new model, the migration logic must handle that transformation.

## Summary

Backfill supplies the historical state. CDC tracks changes made during migration.

Together they form a foundation for online migration, but they require checkpoints, monitoring, and an explicit cutover point.
