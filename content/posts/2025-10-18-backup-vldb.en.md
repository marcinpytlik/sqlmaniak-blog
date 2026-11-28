---
title: "VLDB Backup Above 4 TB — How to Avoid the Trap"
date: 2025-10-18
slug: backup-vldb
tags: [SQLServer, Backup, Restore, HighAvailability, DBA]
draft: false
---

With a small database, backup may seem as simple as pressing a button. With a database of 4 TB or more, it becomes a strategy.

SQL Server can back up very large databases, but the practical limits come from infrastructure: I/O, network capacity, storage, and sometimes the mistaken belief that a completed backup guarantees recovery.

In the world of very large databases (VLDBs), backup is a **logistics process**. It requires planning, testing, segmentation, and careful calculation: *how much data, how quickly, to which destination, and for what recovery objective?*

## 1. Striped Backup — Not a Luxury

Writing a 4 TB backup to a single file can become an operational bottleneck. Distribute the backup across multiple stripes, ideally on independent storage resources:

```sql
BACKUP DATABASE ERPCS_PROD
TO
    DISK = 'X:\Backups\ERPCS_PROD_1.bak',
    DISK = 'Y:\Backups\ERPCS_PROD_2.bak',
    DISK = 'Z:\Backups\ERPCS_PROD_3.bak',
    DISK = 'W:\Backups\ERPCS_PROD_4.bak'
WITH
    COMPRESSION,
    CHECKSUM,
    STATS = 5,
    MAXTRANSFERSIZE = 4194304,
    BUFFERCOUNT = 384;
```

Striping lets SQL Server write in parallel and can spread the I/O load. Depending on storage and compression, the difference can be dramatic — but the cited six-hour versus 50-minute comparison is an illustrative scenario, not a guaranteed result.

## 2. Filegroup Backup — Protect What Changes

A daily full backup of a VLDB may be impractical. If the database is logically partitioned into current, reporting, and archival filegroups, consider partial or filegroup backups:

```sql
BACKUP DATABASE ERP_DB FILEGROUP = 'FG_ACTIVE' 
TO DISK = 'X:\Backups\ERP_DB_FG_ACTIVE.bak' 
WITH COMPRESSION, CHECKSUM;
```

This can reduce backup volume for active portions of a database. However, filegroup backups require a carefully designed restore sequence and appropriate log backups. Do not assume backing up only the active filegroup provides complete recoverability.

## 3. Restore Testing — The Frequently Missed Step

A backup that has never been restored is only an unproven binary file.

VLDB restores require sufficient capacity, time, documented procedures, and realistic recovery plans. Test on another instance, adjust file paths, measure duration, and record the results.

Only then do you have evidence that the backup is usable.

## 4. Differential and Log Backups — A Practical Balance

One possible strategy is a weekly full backup, daily differentials, and hourly (or more frequent) transaction log backups. The actual schedule must follow the required RPO and RTO.

In FULL or BULK_LOGGED recovery, transaction log backups are essential for managing the log chain and enabling point-in-time recovery where supported. The restore point and options depend on the recovery model and operations performed.

## 5. Compression and Deduplication

SQL Server backup compression can substantially reduce backup size, depending on the data. A 70% reduction is possible for some datasets, but is not a universal expectation.

For a 24 TB backup, that could mean a much smaller amount of data to store and transfer. Deduplicating backup platforms such as Veeam, Commvault, and Rubrik may offer further savings, depending on workload and architecture.

## 6. Retention and Rotation

VLDB backup archives can quickly reach hundreds of terabytes. Define a retention policy, for example 14 days online, 30 days offline, and a year in WORM storage — but only if it matches compliance and recovery requirements.

An illustrative cleanup call:

```sql
EXECUTE dbo.usp_CleanupOldBackups 
    @Path = 'X:\Backups\', 
    @RetentionDays = 14;
```

**Important:** `dbo.usp_CleanupOldBackups` is a custom procedure, not a built-in SQL Server stored procedure. It must exist and be reviewed before this example can run.

## 7. Monitoring and Alerts

Track backup success, duration, and age. Use `msdb.dbo.backupset` as one monitoring source, for example with Telegraf, InfluxDB, and Grafana. Alert on missing backups or unexpected duration increases. Also monitor whether backup files are accessible and restorable.

## 8. The Psychology of Backup

The biggest failures often come from a false sense of safety, not a T-SQL syntax error. A backup only provides confidence when recovery is **tested, repeatable, and measurable**.

> You do not really have a backup until you have restored it.

## 9. Example Scripts and Configuration

My repository includes materials for SQL Server 2022 VLDB backup strategies: T-SQL for striped/full/differential/log backups, PowerShell for automation and retention, monitoring dashboards using Telegraf and InfluxDB, and a restore-test checklist.

[SQLManiak — Backup & Restore Scripts on GitHub](https://github.com/marcinpytlik/SQLManiak/tree/master/labs/06-internals/Lab07_Backup_Restore_Perf)

---

If a backup takes hours, that alone is not necessarily a problem. The real problem is not knowing **how long recovery will take**.
