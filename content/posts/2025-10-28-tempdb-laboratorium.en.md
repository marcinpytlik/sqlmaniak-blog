---
title: "TempDB: SQL Server's Playground"
date: 2025-10-28
slug: tempdb-laboratorium
tags: [SQLServer, TempDB, Internals, IO, Performance]
draft: false
---

**TempDB is SQL Server's laboratory.** Temporary tables, sorts, worktables, spools, hash operations, and row versions used by snapshot isolation may all rely on it. If the database is the mind, *TempDB is its workshop*.

An overloaded TempDB slows down the whole system, like a workbench that is too small for the job.

## ⚙️ What goes into TempDB?

- Temporary tables (`#local`, `##global`).
- Table variables (`@table`).
- Sort and hash work for `ORDER BY`, `GROUP BY`, and joins.
- Row versions for snapshot isolation / RCSI when the version store is in TempDB.
- Work performed by `DBCC CHECKDB`.
- Spools, worktables, and workfiles.

## 🧠 TempDB architecture

TempDB is **shared by the entire SQL Server instance** and is recreated when the instance starts.

- Multiple data files and a transaction log file.
- **Multiple equally sized data files** are often recommended to address allocation contention.
- Use **fixed-size autogrowth increments** rather than percentages, and pre-size files appropriately.

## 🔍 Inspect the DMVs

```sql
-- IO statystyki dla TempDB
SELECT database_id, file_id, num_of_writes, num_of_reads
FROM sys.dm_io_virtual_file_stats(DB_ID('tempdb'), NULL);
```

```sql
-- Zuzycie przestrzeni
SELECT SUM(user_object_reserved_page_count)*8/1024.0 AS UserObj_MB,
       SUM(internal_object_reserved_page_count)*8/1024.0 AS InternalObj_MB,
       SUM(version_store_reserved_page_count)*8/1024.0 AS VersionStore_MB
FROM sys.dm_db_file_space_usage;
```

## 🧪 Quick test: pressure on TempDB

```sql
USE tempdb;
GO
DECLARE @i INT = 1;
WHILE @i <= 1000
BEGIN
    CREATE TABLE #demo (id INT IDENTITY, c CHAR(8000));
    INSERT INTO #demo DEFAULT VALUES;
    DROP TABLE #demo;
    SET @i += 1;
END
```

Monitor DMVs and performance counters while the test runs.

## ⚖️ Good practices

- Consider multiple data files; start with established guidance and adjust based on measured contention rather than applying a rigid CPU-to-file formula.
- Keep data-file sizes and growth increments consistent (for example, 512 MB).
- Use fast SSD/NVMe storage and appropriate initial sizes.
- Monitor `PAGELATCH_%` waits in `tempdb`:

```sql
SELECT * FROM sys.dm_os_waiting_tasks WHERE wait_type LIKE 'PAGELATCH_%' AND resource_description LIKE '2:%';
```

📂 Repository: [TempDB](https://github.com/marcinpytlik/SQLManiak/tree/master/sqlmaniak_blog/TEMP_DB)

> “There is no creativity without controlled chaos.” — inspired by Feynman
