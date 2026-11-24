---
title: "SQL Server Backup: A Green Job Is Not a Recovery Strategy"
date: 2026-06-07T20:00:00+01:00
slug: sql-server-backup-zielony-job-to-nie-strategia-restore
description: "A successful SQL Server Agent backup job is only the beginning. A real strategy means restoring to the right point in time within an acceptable time."
tags: [SQLServer, Backup, Restore, DBA, DisasterRecovery]
categories: [SQL Server]
draft: false
---

I am returning to the blog with a subject that often seems simple in SQL Server — at least at first glance.

Backup.

In many environments, discussions about data safety end with one sentence:

> The backup job is green.

That is good, but it does not yet mean the organization has a real recovery strategy.

![SQL Server Backup and Restore — DBA Package](/images/sql-server-backup-restore-pakiet-dba-cover.png)

## A Green Job Only Confirms an Operation Completed

A green SQL Server Agent job status means a particular operation completed successfully. That matters, but it tells us very little.

It does not tell us whether:

- the backup file still exists,
- it is accessible from the server on which we will restore,
- it contains the correct database,
- we have a complete LOG backup chain,
- the TDE certificate and private key are available,
- the backup can actually be restored,
- restoration meets the required RTO,
- the business accepts potential data loss within the RPO.

Monitoring job status alone is not enough.

## Backup Is Not the Goal

Backup is a means to an end. The goal is successful data recovery after a failure, user error, database corruption, server loss, or security incident.

Compare these questions:

```text
Czy backup się wykonał?
```

and:

```text
Czy potrafię odtworzyć bazę do właściwego punktu w czasie i w akceptowalnym czasie?
```

The first concerns a technical operation; the second concerns DBA responsibility.

## RPO and RTO Must Come First

A backup strategy should follow two values:

- **RPO** — the maximum amount of data loss the organization can tolerate.
- **RTO** — how quickly the system must be restored after an outage.

If the business can tolerate at most 15 minutes of lost data, a daily LOG backup is not sufficient. If the system must return within an hour but a full restore takes six hours, merely having a backup does not meet the business requirement.

This is where the real strategy discussion begins.

## The Log Chain — The Quiet Hero of Recovery

For databases using `FULL` or `BULK_LOGGED` recovery, the LOG backup chain is essential.

It enables recovery to a particular point in time, subject to recovery-model limitations.

Example:

```text
20:00 FULL backup
22:00 DIFF backup
22:15 LOG backup
22:30 LOG backup
22:45 LOG backup
23:00 LOG backup
```

If we need to restore the database to 22:37, FULL and DIFF alone are insufficient. We need the appropriate part of the log chain and `STOPAT`.

Here is the problem: many administrators check whether LOG backup jobs ran, but do not verify chain continuity.

A simple check against LOG backup history:

```sql
DECLARE @DatabaseName sysname = N'ERP';

WITH LogBackups AS
(
    SELECT
        bs.database_name,
        bs.backup_start_date,
        bs.backup_finish_date,
        bs.first_lsn,
        bs.last_lsn,
        LAG(bs.last_lsn) OVER
        (
            PARTITION BY bs.database_name
            ORDER BY bs.backup_start_date
        ) AS previous_last_lsn
    FROM msdb.dbo.backupset AS bs
    WHERE bs.database_name = @DatabaseName
      AND bs.type = 'L'
)
SELECT
    database_name,
    backup_start_date,
    backup_finish_date,
    previous_last_lsn,
    first_lsn,
    last_lsn,
    CASE
        WHEN previous_last_lsn IS NULL THEN 'PIERWSZY LOG W WYNIKU'
        WHEN previous_last_lsn = first_lsn THEN 'OK - CIAGLOSC'
        ELSE 'UWAGA - PRZERWA W LANCUCHU'
    END AS log_chain_status
FROM LogBackups
ORDER BY backup_start_date;
```

This does not replace a complete restore procedure, but it can quickly expose a potential problem.

## TDE: A Database Backup May Not Be Enough

If a database uses TDE, a database backup alone may not be sufficient.

You also need:

- the TDE certificate,
- its private key,
- the password protecting the certificate backup,
- a secure place to store these items,
- a tested restore procedure on another instance.

Without the TDE certificate, the backup may exist but be impossible to restore where it is needed.

This is the kind of issue that often surfaces only during an outage or DR test. Better to discover it during a test.

## RESTORE VERIFYONLY Is Not a Restore Test

`RESTORE VERIFYONLY` is useful, but it is not a complete restoration test.

It can help confirm that a backup appears readable, but it does not answer every question:

- Will the database restore completely?
- Are the file paths correct?
- Are all striped backup files available?
- Are the TDE certificates accessible?
- Will the application start after restoration?
- Will `DBCC CHECKDB` pass afterward?
- How long does the entire procedure really take?

The real test of a backup is a restore test.

## Minimum DBA Checklist

To determine whether backups are merely an operation or part of a strategy, start with these questions:

- Do we know the RPO and RTO for every important database?
- Do we know which databases use `SIMPLE`, `FULL`, or `BULK_LOGGED`?
- Are LOG backups scheduled according to RPO?
- Do we check log-chain continuity?
- Do we perform restore tests regularly?
- Do we measure restore duration, not just backup duration?
- Do we back up system databases after configuration changes?
- Do we have backups of TDE certificates?
- Is there an emergency procedure for losing a server or storage?
- Does anyone besides one person know how to restore the system?

If the answer to most of these is “I don't know,” the backups may work, but the strategy needs improvement.

## Why I Am Writing This

Over the years, I have seen environments where backups formally existed. Jobs were green, files were created, and monitoring was quiet.

The problem appeared only when something had to be restored.

One file was missing. Logs were missing. The TDE certificate existed only on the old server. Nobody knew which DIFF was correct. Restoration took far longer than expected. The application did not work after recovery because some data lived outside SQL Server.

That is why I like to repeat:

> It is not about whether the backup succeeded.
> It is about whether the restore succeeds.

## Additional Resource

Based on these experiences, I prepared a practical DBA package:

**SQL Server Backup and Restore — DBA Package**

It includes:

- a PDF e-book,
- T-SQL and PowerShell scripts,
- DBA checklists,
- restore runbooks,
- emergency procedures,
- resources covering RPO, RTO, LSN, log chains, TDE, gMSA, backup monitoring, and restore tests.

Package link:

[SQL Server Backup and Restore — DBA Package](https://pytlik.gumroad.com/l/sql-server-backup-restore-pakiet-dba)

This is not about clicking “Backup.” It is about thinking through data recovery in a real SQL Server environment.

---

If all you have today are green backup jobs, ask yourself one question:

**When did you last actually restore a database from backup?**
