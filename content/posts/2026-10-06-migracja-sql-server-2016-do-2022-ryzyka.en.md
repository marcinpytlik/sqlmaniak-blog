---
title: "Migrating SQL Server 2016 to 2022 — What the Upgrade Wizard Doesn't Tell You"
date: 2026-10-06
slug: migracja-sql-server-2016-do-2022-ryzyka
description: "Key migration risks: compatibility level, execution plans, logins, jobs, SSIS, HA/DR, and post-migration testing."
tags: [SQLServer, Migration, SQLServer2022, DBA, Upgrade]
categories: [SQL Server]
draft: false
---

The setup wizard can check many technical prerequisites. But it does not know your business processes, application dependencies, or the behavior of your most important queries.

## Two Levels of Migration

Distinguish between:

1. Moving the database to a newer engine.
2. Increasing its compatibility level.

## What Must Be Migrated Beyond User Databases?

- Logins and SIDs.
- Server roles and permissions.
- Credentials and proxies.
- Jobs, operators, and alerts.
- Linked servers and Database Mail.
- Certificates and keys.
- SSISDB.
- Instance-level settings.

## Orphaned Users

```sql
SELECT
    dp.name AS DatabaseUser,
    dp.type_desc
FROM sys.database_principals AS dp
LEFT JOIN sys.server_principals AS sp
    ON dp.sid = sp.sid
WHERE dp.authentication_type_desc = 'INSTANCE'
  AND sp.sid IS NULL
  AND dp.name NOT IN
  (
      N'guest',
      N'dbo',
      N'sys',
      N'INFORMATION_SCHEMA'
  );
```

## Compatibility Level

```sql
SELECT
    name,
    compatibility_level
FROM sys.databases
ORDER BY name;
```

Changing it:

```sql
ALTER DATABASE [TwojaBaza]
SET COMPATIBILITY_LEVEL = 160;
```

should be a separate phase, accompanied by Query Store and regression monitoring.

## Performance Risks

- Parameter sniffing.
- Cardinality estimation.
- Scalar UDF inlining.
- Table variables and multi-statement table-valued functions (MSTVFs).
- Batch mode on rowstore.
- Memory grants.
- Legacy hints.

## Post-Migration Testing

Check database state, `DBCC CHECKDB`, logins, jobs, backups, monitoring, applications, integrations, performance, HA/DR, alerts, and the SQL Server Error Log.

## Rollback Plan

A rollback may involve redirecting the application to the old instance, a tail-log backup, changing an alias or DNS record, restoring a database, and reverting integration changes. Design this plan before migration; not every migration can simply be reversed.

## Summary

A migration does not end when the database reports `ONLINE`. A careful DBA evaluates whether the entire system works, is monitored, and can be safely recovered.
