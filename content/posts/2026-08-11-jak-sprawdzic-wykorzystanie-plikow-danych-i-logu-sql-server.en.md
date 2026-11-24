---
title: "How to Check Actual Data File and Transaction Log Usage"
date: 2026-08-11
slug: jak-sprawdzic-wykorzystanie-plikow-danych-i-logu-sql-server
description: "Practical T-SQL queries showing size, usage, and free space in SQL Server data files and transaction logs."
tags: [SQLServer, MDF, NDF, LDF, TransactionLog, DBA, Monitoring]
categories: [SQL Server]
draft: false
---

A database file's size does not tell you how much data it actually contains.

An MDF file may be 500 GB but hold only 350 GB of data. A log file may be 100 GB even though its active portion occupies only a few gigabytes.

That is why diagnostics should distinguish three things:

- the physical size of the file,
- the space used inside the file,
- the space available on the volume.

## Data Files and Log Files Are Two Different Worlds

MDF and NDF files store data and index pages. An LDF file stores transaction log records.

For data files, we can use `FILEPROPERTY`. For the log, `sys.dm_db_log_space_usage`, `DBCC SQLPERF(LOGSPACE)`, and `log_reuse_wait_desc` are more appropriate.

## Basic File Information

```sql
SELECT
    DB_NAME() AS DatabaseName,
    file_id,
    name AS LogicalFileName,
    type_desc AS FileType,
    physical_name,
    size / 128.0 AS FileSizeMB,
    CASE
        WHEN max_size = -1 THEN NULL
        ELSE max_size / 128.0
    END AS MaxSizeMB,
    CASE
        WHEN is_percent_growth = 1
            THEN CONCAT(growth, '%')
        ELSE CONCAT(growth / 128.0, ' MB')
    END AS FileGrowth
FROM sys.database_files
ORDER BY file_id;
```

## Data File Space Usage

```sql
SELECT
    DB_NAME() AS DatabaseName,
    df.file_id,
    df.name AS LogicalFileName,
    df.physical_name,
    df.size / 128.0 AS FileSizeMB,
    FILEPROPERTY(df.name, 'SpaceUsed') / 128.0 AS UsedSpaceMB,
    (df.size - FILEPROPERTY(df.name, 'SpaceUsed')) / 128.0 AS FreeSpaceMB,
    CAST(
        100.0 * FILEPROPERTY(df.name, 'SpaceUsed')
        / NULLIF(df.size, 0)
        AS decimal(10,2)
    ) AS UsedPercent
FROM sys.database_files AS df
WHERE df.type = 0
ORDER BY df.file_id;
```

Run this query in the context of the database being examined.

## Transaction Log Usage

```sql
SELECT
    DB_NAME() AS DatabaseName,
    total_log_size_in_bytes / 1024.0 / 1024 AS TotalLogSizeMB,
    used_log_space_in_bytes / 1024.0 / 1024 AS UsedLogSpaceMB,
    used_log_space_in_percent AS UsedLogSpacePercent,
    log_space_in_bytes_since_last_backup / 1024.0 / 1024
        AS LogGeneratedSinceLastBackupMB
FROM sys.dm_db_log_space_usage;
```

If the log is 95% full, do not start with a shrink operation.

First, investigate the cause:

```sql
SELECT
    name,
    recovery_model_desc,
    log_reuse_wait_desc
FROM sys.databases
WHERE database_id = DB_ID();
```

## Free Space on Volumes

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

## What Should You Check During Diagnostics?

1. What is the file's size?
2. How much space is used?
3. Is there a file-size limit?
4. How is autogrowth configured?
5. How much free space remains on the disk?
6. How quickly is the database growing?
7. Does the problem concern data files or the log?

## Summary

Understanding actual space usage requires examining several layers together.

A calm DBA does not ask only:

> How large is the file?

They also ask:

> How much space is used, why is it used, and when will we run out?
