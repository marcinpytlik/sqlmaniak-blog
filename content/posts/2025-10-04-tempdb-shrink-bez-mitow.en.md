---
title: "tempdb: When and How to Shrink It — Without Myths"
date: "2025-10-04"
slug: "tempdb-shrink-bez-mitow"
draft: false
description: "Diagnose tempdb growth and safely reduce its size using a practical runbook, scripts, and a verification checklist."
tags: ["SQL Server", "tempdb", "Performance", "DBA", "Runbook"]
author: "Marcin Pytlik | SQLManiak"
banner: "/images/tempdb-shrink-bez-mitow.png"
canonical: "https://sqlmaniak.blog/tempdb-shrink-bez-mitow"
---

## Introduction

tempdb is neither a trash bin nor a magical buffer that fixes itself. When it grows, your queries, sorts, spools, and transaction versioning are consuming space. Here is a practical runbook without myths.

## TL;DR

1. Diagnose *why* tempdb is growing: version store, hash-join rehashing, or spills.
2. Fix the root cause: execution plans, indexes, hints, and memory grants.
3. Only then consider shrinking, whether through a planned service restart or `DBCC SHRINKFILE` combined with appropriate file sizing.

## Diagnosis: What Consumes tempdb?

```sql
-- 1) Tabela wersji (Snapshot Isolation/ADR)
SELECT TOP(10) database_id, total_version_store_reserved_page_count*8/1024 AS MB
FROM sys.dm_tran_version_store_space_usage
ORDER BY 2 DESC;

-- 2) Najwięksi alokujący
SELECT TOP(20)
  t.session_id, t.request_id, t.task_alloc*8/1024 AS MB_alloc, t.task_dealloc*8/1024 AS MB_dealloc,
  s.login_name, r.command, r.status, r.wait_type, r.cpu_time, r.total_elapsed_time
FROM (
  SELECT session_id, request_id,
         SUM(internal_objects_alloc_page_count + user_objects_alloc_page_count) AS task_alloc,
         SUM(internal_objects_dealloc_page_count + user_objects_dealloc_page_count) AS task_dealloc
  FROM sys.dm_db_task_space_usage
  GROUP BY session_id, request_id) AS t
LEFT JOIN sys.dm_exec_sessions s ON s.session_id=t.session_id
LEFT JOIN sys.dm_exec_requests r ON r.session_id=t.session_id AND r.request_id=t.request_id
ORDER BY MB_alloc DESC;
```

### Common Problems

- Persistent spills due to missing indexes or insufficient memory grants.
- `READ_COMMITTED_SNAPSHOT` combined with long-running transactions, preventing timely version cleanup.
- Large sorts or `HASH MATCH` operations on `NVARCHAR(MAX)` / `VARBINARY(MAX)` columns.

## When and How to Shrink

- **Only after removing the cause.** Otherwise growth will return.
- **tempdb is recreated when SQL Server starts.** A planned restart can return it to configured startup sizes, but the outage must be coordinated.

### Procedure Without Restart

```sql
USE master;
-- 1) Przenieś tempdb do docelowego rozmiaru i plików
ALTER DATABASE tempdb MODIFY FILE (NAME = tempdev, SIZE = 8192MB, FILEGROWTH = 256MB);
ALTER DATABASE tempdb MODIFY FILE (NAME = templog, SIZE = 2048MB, FILEGROWTH = 256MB);
-- 2) Przytnij pliki (powtarzaj do skutku, obserwuj sys.dm_db_file_space_usage)
DBCC SHRINKFILE (tempdev, 8192);
DBCC SHRINKFILE (templog, 2048);
```

The sample sets target sizes and then requests a shrink. Remember that `MODIFY FILE` does not itself shrink an already larger file, and `DBCC SHRINKFILE` may not reach the target if pages cannot be moved.

> Multiple appropriately sized tempdb data files can help reduce allocation latch contention. Start with established Microsoft guidance and adjust based on observed contention; the number of files is not a universal formula.

```sql
-- Dodanie plików (przykład)
ALTER DATABASE tempdb ADD FILE (NAME = tempdev2, FILENAME='T:\tempdb\tempdb2.ndf', SIZE=8192MB, FILEGROWTH=256MB);
```

## Verification

- Use `sys.dm_db_file_space_usage` to compare free and used space.
- Confirm that version-store usage is absent or within expected limits.
- In Grafana, verify lower `tempdb used space` and the absence of persistent spills in Query Store.

## Done Checklist

- [ ] Identified the cause of growth.
- [ ] Corrected plans, indexes, or memory grants.
- [ ] Configured reasonable `SIZE` and `FILEGROWTH`.
- [ ] Added data files only when justified by workload and contention.
- [ ] Verified the result in monitoring.
