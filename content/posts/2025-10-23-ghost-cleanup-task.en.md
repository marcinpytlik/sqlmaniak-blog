---
title: "Ghost Cleanup Task in Action"
date: 2025-10-23
slug: ghost-cleanup-task
tags: [SQLServer, Internals, GhostRecords, DMV, Performance]
draft: false
---

SQL Server resembles an organism that can keep itself clean. When a row is deleted, its ghost does not disappear immediately — it remains in the data structure like a trace of a dead cell. Only the *Ghost Cleanup Task* arrives later to tidy things up quietly and restore balance.

It is SQL Server's immune system: working in the background, out of sight, to keep the database from filling up with dead records.

---

## 🔍 Look inside the DMV

```sql
-- znajdź indeksy zawierające ghost records
SELECT 
    object_name(object_id) AS TableName, 
    index_id, 
    ghost_record_count
FROM sys.dm_db_index_physical_stats(DB_ID(), NULL, NULL, NULL, 'DETAILED')
WHERE ghost_record_count > 0;
```

> “Order is not the absence of chaos, but the ability to control it.” — attributed to Kant

---

## 🧪 Lab: Watch ghosts in action

This experiment shows that a deleted record may not disappear physically straight away.

### 1️⃣ Create the test environment

```sql
USE tempdb;
GO
IF OBJECT_ID('dbo.GhostDemo') IS NOT NULL DROP TABLE dbo.GhostDemo;
CREATE TABLE dbo.GhostDemo
(
    Id INT IDENTITY(1,1) PRIMARY KEY,
    Payload CHAR(100) NOT NULL DEFAULT REPLICATE('x', 100)
);
GO

INSERT INTO dbo.GhostDemo DEFAULT VALUES;
GO 10000
```

### 2️⃣ Delete some rows

```sql
DELETE TOP (5000) FROM dbo.GhostDemo;
GO
```

### 3️⃣ Inspect the index structure

```sql
-- jeszcze przed sprzątaniem
SELECT 
    object_name(object_id) AS TableName, 
    index_id, 
    ghost_record_count
FROM sys.dm_db_index_physical_stats(DB_ID(), OBJECT_ID('dbo.GhostDemo'), NULL, NULL, 'DETAILED');
```

### 4️⃣ Trigger Ghost Cleanup Task

Normally, cleanup is asynchronous, but you can request it explicitly:

```sql
-- uruchom wewnętrzny task
DBCC FORCEGHOSTCLEANUP;
GO
```

### 5️⃣ Verify again

```sql
SELECT 
    object_name(object_id) AS TableName, 
    index_id, 
    ghost_record_count
FROM sys.dm_db_index_physical_stats(DB_ID(), OBJECT_ID('dbo.GhostDemo'), NULL, NULL, 'DETAILED');
```

📊 After a while, `ghost_record_count` may decrease as the ghost records are cleaned up.

---

## 🔬 Internals

Ghost Cleanup runs as a separate **background task** within SQL Server. It periodically examines pages containing ghosted records and removes eligible rows later, minimizing disruption to concurrent workloads.

Key points:
- it operates **at the instance level**, rather than as a dedicated task per database,
- its scheduling interval is **roughly 10 seconds**, depending on version and activity,
- cleanup uses **cooperative scheduling**,
- it can be requested with `DBCC FORCEGHOSTCLEANUP`,
- **In-Memory OLTP** tables use separate garbage-collection mechanisms.

---

## 🧠 What to remember

| Concept | Description |
|---|---|
| Ghost Record | A record marked as deleted but still physically present on a data page. |
| Cleanup Task | A background process that removes eligible ghost records asynchronously. |
| DMV | `sys.dm_db_index_physical_stats` reports ghost-record counts. |
| Explicit request | `DBCC FORCEGHOSTCLEANUP` requests ghost cleanup. |

---

> 💡 **Pro tip:** If data files are growing or fragmentation is high, check whether mass DELETE operations have left many ghost records. In some cases, an *ALTER INDEX REBUILD* may be worth considering.

---
