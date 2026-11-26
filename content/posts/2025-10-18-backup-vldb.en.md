---
title: "VLDB Backups Over 4 TB — How to Avoid the Traps"
date: 2025-10-18
slug: backup-vldb
tags: [SQLServer, Backup, Restore, HighAvailability, DBA]
draft: false
---

For a small database, a backup may seem like a simple button. For databases of 4 TB and more, it is a strategy.

SQL Server can back up extremely large databases, but infrastructure becomes the limiting factor: I/O, networking, storage capacity, and sometimes the false belief that a completed backup guarantees recovery.

In the world of **Very Large Databases (VLDBs)**, backup is a logistical process. It requires planning, testing, segmentation, and clear calculations: how much data, how quickly, where, and why?

## 1. Striped Backup — Not a Luxury

Backing up 4 TB to a single file creates operational risks. Divide the backup into stripes, preferably across independent storage resources:

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

Striping distributes work and allows parallel writes. Depending on the environment, this can make a dramatic difference in backup duration. The quoted six-hour versus fifty-minute example is illustrative, not a performance guarantee.

## 2. Filegroup Backup — Protect What Changes

For a VLDB, a daily full backup may be unnecessarily expensive. If the database separates historical, reporting, and current data, consider **partial** or **filegroup backups**:

```sql
BACKUP DATABASE ERP_DB FILEGROUP = 'FG_ACTIVE' 
TO DISK = 'X:\Backups\ERP_DB_FG_ACTIVE.bak' 
WITH COMPRESSION, CHECKSUM;
```

These can reduce backup volume for active filegroups. However, the restore strategy becomes more complex: verify filegroup dependencies, recovery model, log backups, and recoverability before choosing this approach.

## 3. Restore Testing — The Often-Missed Step

A backup you have never restored is only a binary file whose recoverability remains unproven.

Restoring a VLDB requires capacity, time, procedures, and a carefully planned restore sequence.

Test it:

- Restore the backup to another instance.
- Adjust file paths.
- Measure and record recovery time.

Only then can you assess whether the backup supports your recovery objectives.

## 4. DIFF + LOG — A Practical Compromise

One possible policy is a weekly full backup, daily differential backups, and transaction-log backups every hour or more often.

For VLDBs, choose the schedule from **RPO and RTO**, not a universal rule.

In the `FULL` recovery model, log backups are essential for maintaining a recoverable log chain and enabling point-in-time recovery.

## 5. Compression and Deduplication

SQL Server backup compression can substantially reduce output size; in some workloads the reduction may approach 70%, but the actual ratio depends on the data.

For a hypothetical 24 TB backup, a strong compression ratio might reduce transfer and storage requirements significantly.

Backup platforms such as Veeam, Commvault, and Rubrik may add deduplication benefits.

## 6. Retention and Rotation

VLDB backups can quickly occupy hundreds of terabytes. Define a retention policy, for example 14 days online, 30 days offline, and one year in WORM archival storage, if required by policy.

Automate cleanup of old backups:

```sql
EXECUTE dbo.usp_CleanupOldBackups 
    @Path = 'X:\Backups\', 
    @RetentionDays = 14;
```

**Note:** `dbo.usp_CleanupOldBackups` is a custom procedure in this example, not a built-in SQL Server stored procedure. Implement and test it before use.

## 7. Monitoring and Alerts

Every backup should have a recorded result and duration. Monitor `msdb.dbo.backupset`, for example with Telegraf, InfluxDB, and Grafana.

Alert when backup duration exceeds its normal range or when an expected backup record is missing.

## 8. The Psychology of Backup

Many experienced DBAs have been caught out not by T-SQL syntax but by a false sense of security.

A backup provides confidence only when it is **tested, repeatable, and measurable**.

> “You don't really have a backup until you've restored it.”

This remains true even as databases grow faster than storage arrays.

## 9. Sample Scripts and Configuration

The repository contains materials for VLDB backup strategies on SQL Server 2022:

- **T-SQL scripts** for striped, full, differential, and log backups.
- **PowerShell** for automation and retention.
- **Telegraf + InfluxDB** monitoring dashboards.
- **Restore-test checklists**.

[SQLManiak — Backup & Restore Scripts (GitHub)](https://github.com/marcinpytlik/SQLManiak/tree/master/labs/06-internals/Lab07_Backup_Restore_Perf)

---

A backup taking hours is not necessarily the problem. The real problem begins when you do not know **how long recovery will take**.
