---
title: "Autogrowth Is Enabled, but the Database File Still Won't Grow. Why?"
date: 2026-08-04
slug: autogrowth-wlaczony-plik-bazy-nie-rozszerza-sql-server
description: "Why SQL Server autogrowth can fail despite being enabled: file limits, disk space, storage restrictions, diagnostic queries, and DBA best practices."
tags: [SQLServer, Autogrowth, MDF, NDF, LDF, DBA, Troubleshooting]
categories: [SQL Server]
draft: false
---

One common misconception in SQL Server administration is that enabling **autogrowth** solves every database-space problem.

In reality, autogrowth may be enabled and configured, yet the database reports insufficient space, the application returns errors, and the file still cannot grow.

This usually does not mean the SQL Server autogrowth mechanism is broken. It means that SQL Server cannot overcome an external or configured limit.

This article explains what autogrowth does, why it can fail, how to check data and log files, and how to configure safer production defaults.

## What Is Autogrowth?

Autogrowth is SQL Server's mechanism for automatically expanding a database file when it needs more space. For example, a data file may be configured to grow by:

```text
1024 MB
```

When it runs out of internal free space, SQL Server attempts to allocate another 1 GB.

But this requires available disk space, appropriate permissions, the ability to extend the file, a suitable `MAXSIZE` setting, and a functioning storage subsystem.

> Autogrowth does not create disk space. It uses space that already exists.

## Free Space Inside a File vs. Free Space on Disk

These are different things.

A 100 GB MDF or NDF file might contain only 80 GB of allocated data pages. SQL Server can use the remaining 20 GB without increasing the physical file size.

If the file is nearly full, however, it must grow. If the disk is full, growth fails even if autogrowth is enabled.

The disk might report:

```text
Free space: 0 MB
```

## Checking Database File Sizes

Use `sys.database_files`:

```sql
SELECT
    name AS LogicalFileName,
    type_desc AS FileType,
    physical_name AS PhysicalFileName,
    size / 128.0 AS FileSizeMB,
    max_size,
    growth,
    is_percent_growth
FROM sys.database_files;
```

The query reports logical and physical names, file types, current sizes, `max_size`, `growth`, and `is_percent_growth`.

Pay particular attention to:

```text
max_size
growth
is_percent_growth
```

## Interpreting Autogrowth Configuration

If:

```text
is_percent_growth = 0
```

then `growth` is stored in 8 KB pages. Convert it to MB:

```sql
SELECT
    name,
    growth / 128.0 AS GrowthMB
FROM sys.database_files
WHERE is_percent_growth = 0;
```

If:

```text
is_percent_growth = 1
```

then `growth` is a percentage. For example:

```text
growth = 10
```

means 10% growth. Fixed-size increments are generally more predictable in production, such as:

```text
512 MB
1024 MB
4096 MB
```

Ten percent of a 10 GB file is about 1 GB; ten percent of a 1 TB file is about 100 GB.

## Checking Data File Utilization

For data files, use `FILEPROPERTY`:

```sql
SELECT
    df.name AS LogicalFileName,
    df.type_desc AS FileType,
    df.physical_name,
    df.size / 128.0 AS FileSizeMB,
    FILEPROPERTY(df.name, 'SpaceUsed') / 128.0 AS UsedSpaceMB,
    (
        df.size -
        FILEPROPERTY(df.name, 'SpaceUsed')
    ) / 128.0 AS FreeSpaceMB,
    CAST(
        100.0 * FILEPROPERTY(df.name, 'SpaceUsed') / NULLIF(df.size, 0)
        AS decimal(10,2)
    ) AS UsedPercent
FROM sys.database_files AS df
WHERE df.type = 0;
```

This reports file size, used space, free space, and utilization percentage. Low `FreeSpaceMB` means the file will soon need to grow, but does not prove that the volume has enough capacity.

## Checking Free Space on Volumes

Use `sys.dm_os_volume_stats`:

```sql
SELECT DISTINCT
    vs.volume_mount_point,
    vs.logical_volume_name,
    vs.total_bytes / 1024.0 / 1024 / 1024 AS TotalSizeGB,
    vs.available_bytes / 1024.0 / 1024 / 1024 AS FreeSpaceGB,
    CAST(
        100.0 * vs.available_bytes / NULLIF(vs.total_bytes, 0)
        AS decimal(10,2)
    ) AS FreeSpacePercent
FROM sys.master_files AS mf
CROSS APPLY sys.dm_os_volume_stats(mf.database_id, mf.file_id) AS vs
ORDER BY vs.volume_mount_point;
```

This is one of the most useful checks when autogrowth fails. If the volume has almost no free space, the file cannot grow.

## Seven Common Reasons File Growth Fails

### 1. Insufficient Disk Space

The file may allow autogrowth, but the disk is full. SQL Server may report:

```text
Could not allocate space for object
because the filegroup is full.
```

or:

```text
Autogrow of file failed because
there is insufficient disk space.
```

Possible responses: free space, expand the volume, move a file using a supported procedure, add a file to the same filegroup, or remove unnecessary non-database files.

Never manually delete MDF, NDF, or LDF files through the operating system.

### 2. Maximum File Size Reached

A file can have autogrowth enabled and still be restricted by `MAXSIZE`:

```sql
ALTER DATABASE [TwojaBaza]
MODIFY FILE
(
    NAME = N'TwojaBaza_Data',
    MAXSIZE = 100GB
);
```

At 100 GB, this file stops growing. Inspect its limit:

```sql
SELECT
    name,
    size / 128.0 AS CurrentSizeMB,
    CASE
        WHEN max_size = -1 THEN 'UNLIMITED'
        ELSE CAST(max_size / 128.0 AS varchar(30))
    END AS MaxSizeMB
FROM sys.database_files;
```

The value:

```text
max_size = -1
```

means no SQL Server file-level limit; it does not mean unlimited disk capacity.

### 3. The Filegroup Is Full

A database can have several filegroups. A table or index belongs to a specific filegroup; free space in a different filegroup is not automatically available to that object.

Inspect the filegroup and file mapping:

```sql
SELECT
    fg.name AS FilegroupName,
    df.name AS LogicalFileName,
    df.physical_name,
    df.size / 128.0 AS FileSizeMB,
    CASE
        WHEN df.max_size = -1 THEN 'UNLIMITED'
        ELSE CAST(df.max_size / 128.0 AS varchar(30))
    END AS MaxSizeMB
FROM sys.filegroups AS fg
INNER JOIN sys.database_files AS df
    ON fg.data_space_id = df.data_space_id
ORDER BY
    fg.name,
    df.name;
```

Possible actions: extend an existing file, add a file to the same filegroup, move the object, or archive data.

### 4. Autogrowth Increment Exceeds Available Space

Suppose the disk has 800 MB free but the file is configured to grow by:

```text
1024 MB
```

The requested 1 GB increment cannot be allocated. Reducing the increment may help temporarily, but it is not a substitute for capacity planning.

### 5. The Problem Is the Transaction Log

Data files and log files behave differently. A full log may need log truncation or removal of a log-reuse blocker rather than more disk space.

Check:

```sql
SELECT
    name,
    recovery_model_desc,
    log_reuse_wait_desc
FROM sys.databases
WHERE name = DB_NAME();
```

The `log_reuse_wait_desc` column may show:

```text
LOG_BACKUP
ACTIVE_TRANSACTION
AVAILABILITY_REPLICA
REPLICATION
CHECKPOINT
```

With `FULL` recovery, verify that transaction log backups run regularly. Simply enlarging the log may only delay the next incident.

### 6. SQL Server Service Account Permissions

SQL Server runs under a service account, domain account, or gMSA. It needs appropriate file-system permissions. After moving a file or changing NTFS ACLs, growth may fail.

Check the service identity, NTFS permissions, SQL Server Error Log, and Windows Event Log.

### 7. Additional File-System or Storage Limits

A Windows volume can report free space even when the underlying hypervisor datastore, thin-provisioned storage, network share, quota, or LUN has reached its limit.

Diagnosing these cases may require cooperation with storage, virtualization, and operating-system administrators.

## Finding Autogrowth Errors

Start with SQL Server Error Log:

```sql
EXEC sys.xp_readerrorlog
    0,
    1,
    N'Autogrow';
```

Also search for allocation errors:

```sql
EXEC sys.xp_readerrorlog
    0,
    1,
    N'Could not allocate space';
```

and:

```sql
EXEC sys.xp_readerrorlog
    0,
    1,
    N'insufficient disk space';
```

Extended Events can help monitor file growth events and their duration.

## Is Autogrowth a Capacity-Management Strategy?

No. Treat autogrowth as a safety net, not as your primary sizing strategy.

Pre-size files, monitor growth trends, configure alerts, maintain reserve capacity, and grow files proactively before predictable demand.

If a database grows automatically every day, its capacity planning probably needs improvement.

## Why Is Frequent Autogrowth a Problem?

Each file-growth event can introduce latency.

For data files, Instant File Initialization (IFI) can significantly reduce the cost when supported and enabled. Transaction log growth generally requires initialization, although newer SQL Server versions support limited instant log initialization for certain small growth events. Verify behavior for your specific build.

Very small log-growth increments can create excessive VLFs and operational overhead. Very large increments can cause noticeable delays. Choose values appropriate to the workload and storage.

## Example Autogrowth Configuration

Data file:

```sql
ALTER DATABASE [TwojaBaza]
MODIFY FILE
(
    NAME = N'TwojaBaza_Data',
    FILEGROWTH = 1024MB
);
```

Log file:

```sql
ALTER DATABASE [TwojaBaza]
MODIFY FILE
(
    NAME = N'TwojaBaza_Log',
    FILEGROWTH = 512MB
);
```

There is no universal value. Consider database size, growth rate, workload, acceptable growth duration, storage performance, recovery model, and log backup frequency.

## Consolidated Diagnostic Query

Use this query to inspect the current database's files:

```sql
SELECT
    DB_NAME() AS DatabaseName,
    df.file_id AS FileId,
    df.name AS LogicalFileName,
    df.type_desc AS FileType,
    df.physical_name AS PhysicalFileName,
    df.size / 128.0 AS FileSizeMB,
    CASE
        WHEN df.type = 0
        THEN FILEPROPERTY(df.name, 'SpaceUsed') / 128.0
        ELSE NULL
    END AS UsedSpaceMB,
    CASE
        WHEN df.type = 0
        THEN
            (
                df.size -
                FILEPROPERTY(df.name, 'SpaceUsed')
            ) / 128.0
        ELSE NULL
    END AS FreeSpaceMB,
    CASE
        WHEN df.max_size = -1
        THEN 'UNLIMITED'
        ELSE CAST(df.max_size / 128.0 AS varchar(30))
    END AS MaxSizeMB,
    CASE
        WHEN df.is_percent_growth = 1
        THEN CAST(df.growth AS varchar(20)) + '%'
        ELSE CAST(df.growth / 128.0 AS varchar(20)) + ' MB'
    END AS Autogrowth
FROM sys.database_files AS df
ORDER BY df.file_id;
```

Combine it with volume-capacity information:

```sql
SELECT DISTINCT
    DB_NAME(mf.database_id) AS DatabaseName,
    mf.name AS LogicalFileName,
    mf.physical_name,
    vs.volume_mount_point,
    vs.total_bytes / 1024.0 / 1024 / 1024 AS TotalSizeGB,
    vs.available_bytes / 1024.0 / 1024 / 1024 AS FreeSpaceGB,
    CAST(
        100.0 * vs.available_bytes /
        NULLIF(vs.total_bytes, 0)
        AS decimal(10,2)
    ) AS FreeSpacePercent
FROM sys.master_files AS mf
CROSS APPLY sys.dm_os_volume_stats
(
    mf.database_id,
    mf.file_id
) AS vs
WHERE mf.database_id = DB_ID()
ORDER BY mf.file_id;
```

## What If a File Has 0 MB Free?

1. Identify whether it is an MDF, NDF, or LDF file.
2. Check internal free space using `FILEPROPERTY` for data files.
3. Check disk capacity using `sys.dm_os_volume_stats`.
4. Inspect `MAXSIZE`.
5. Compare the growth increment with available disk space.
6. Read SQL Server Error Log.
7. For a log file, inspect `log_reuse_wait_desc`.
8. Review the growth trend and recent operations such as imports, index rebuilds, ETL, or large transactions.

## What Not to Do

Do not delete database files from the operating system, shrink without understanding the cause, configure extremely small increments, use percentage growth without analysis, expand a log without checking reuse waits, assume `UNLIMITED` means infinite capacity, or ignore recurring growth events.

Shrink is appropriate for selected exceptional cases, not routine space management.

## Preventing Incidents

Monitor volume free space (both percentage and GB), internal file free space, autogrowth counts and duration, database growth trends, log size and reuse waits, and file-size limits.

Example alert thresholds:

```text
poniżej 20% wolnego miejsca – ostrzeżenie,
poniżej 10% – alert krytyczny,
poniżej 5% – natychmiastowa reakcja.
```

Thresholds must account for absolute volume size: 10% of 100 GB is only 10 GB, whereas 10% of 10 TB is 1 TB.

## Summary

Autogrowth does not guarantee that a file can expand. Growth may fail because of full disks, `MAXSIZE`, full filegroups, increments exceeding available capacity, permissions, storage limits, or log reuse blockers.

Always distinguish:

1. Physical file size.
2. Free space inside the file.
3. Free space on the disk.

Autogrowth is a protective mechanism, not a replacement for monitoring, capacity planning, and deliberate file sizing.

A calm DBA monitors trends, configures alerts, and expands capacity before a space shortage becomes a production incident.
