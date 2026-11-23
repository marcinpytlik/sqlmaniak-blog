---
title: "The ARIES Engine: How SQL Server Records Transaction History"
date: 2025-10-29
slug: walec-aries
tags: [SQLServer, Internals, WAL, ARIES, Recovery]
draft: false
---

SQL Server does not forget. Before modified data pages are written to disk, the engine records **the history of what has changed**. This is the foundation of **ARIES (Algorithm for Recovery and Isolation Exploiting Semantics)**, a key part of reliable transaction processing.

> “History is a system's memory.” — SQLManiak

---

## ⚙️ Write-Ahead Logging (WAL)

Every modification in SQL Server is represented in the transaction log (`.ldf`):

1. A log record describing the change is created, identified by an LSN (Log Sequence Number).
2. The log record is flushed to durable storage.
3. Only then may the modified data page be written to disk.

This is **Write-Ahead Logging (WAL)**: log first, data page later. It allows SQL Server to recover after a failure.

---

## 🔁 ARIES in three acts

When the server starts after a crash, it does not guess. It **reads the log** to reconstruct the database state.

| Phase | What happens | Purpose |
|---|---|---|
| **Analysis** | Identifies active transactions and dirty pages | “Who was still working?” |
| **Redo** | Repeats necessary logged changes | “Reconstruct the state.” |
| **Undo** | Rolls back transactions that did not commit | “Clean up the unfinished work.” |

> ARIES resembles replaying a film: find a suitable recovery point, replay what is needed, and undo unfinished actions.

---

## 🧩 What does a log record contain?

A log record may contain fields such as:

| Field | Meaning |
|---|---|
| **LSN** | Sequential identifier of a log record |
| **PrevLSN** | Previous record in the transaction |
| **Transaction ID** | Unique transaction identifier |
| **PageID / FileID** | Identification of the data page |
| **Operation** | For example, `LOP_INSERT_ROWS` or `LOP_COMMIT_XACT` |
| **Before/After Image** | Information describing the change, depending on operation |

The sequence of these records is SQL Server's black box.

---

## 🔍 Inspect the DMVs and log

```sql
-- aktywność logu dla bieżącej bazy
SELECT name, log_reuse_wait_desc, recovery_model_desc
FROM sys.databases
WHERE database_id = DB_ID();
```

```sql
-- podgląd użycia logu
DBCC SQLPERF(LOGSPACE);
```

```sql
-- odczyt surowego logu (tylko lab!)
SELECT [Current LSN], [Operation], [Transaction ID], [Transaction Name], [Context]
FROM fn_dblog(NULL, NULL)
WHERE [Transaction Name] IS NOT NULL;
```

---

## 🧪 Mini demo: ARIES in action

```sql
USE tempdb;
GO
CREATE TABLE dbo.LogDemo(id INT IDENTITY, txt NVARCHAR(100));
GO
BEGIN TRAN
INSERT INTO dbo.LogDemo VALUES (N'Pierwszy wpis');
INSERT INTO dbo.LogDemo VALUES (N'Drugi wpis');
ROLLBACK TRAN;
```

In the log, you can find records such as:
`LOP_BEGIN_XACT → LOP_INSERT_ROWS → LOP_ABORT_XACT`

Each has its own **LSN**, enabling SQL Server to determine which changes must be undone.

---

## ⚡ Checkpoint and recovery

A checkpoint helps bound recovery work by writing dirty pages and recording recovery information. It does not mean every transaction has committed or that no further recovery is needed.

After a restart, SQL Server uses recovery metadata and the log to perform **Analysis**, **Redo**, and **Undo**, restoring a transactionally consistent state.

Inspect the DMV:

```sql
SELECT database_id, last_checkpoint_lsn FROM sys.database_recovery_status;
```

---

## 🧠 Monitoring the log

```sql
-- użycie logu (rozmiar, procent)
SELECT total_log_size_in_bytes/1024/1024 AS TotalMB,
       used_log_space_in_bytes/1024/1024 AS UsedMB,
       used_log_space_in_percent AS UsedPercent
FROM sys.dm_db_log_space_usage;

-- aktywne transakcje
SELECT transaction_id, name, transaction_begin_time, transaction_state
FROM sys.dm_tran_active_transactions;
```

---

## ⚙️ Good practices

✅ **Regular transaction log backups** under FULL recovery.  
✅ **Short transactions** to avoid prolonged log reuse waits.  
✅ **Fast storage for the `.ldf` file**, which is written frequently.  
✅ **Monitor `log_reuse_wait_desc`** — prolonged `ACTIVE_TRANSACTION` may indicate an open transaction preventing reuse.  
✅ **Never delete the transaction log manually.**

---

## 🧩 Understanding ARIES means understanding SQL Server

ARIES is not just an acronym in a textbook. It is a recovery mechanism that protects data every day. It knows how to **undo unfinished work**, **reconstruct changes** after a failure, and **preserve consistency** despite transaction chaos.

> “SQL Server does not forget. It remembers — in the log.” — SQLManiak

---

📘 Demo repository:
👉 [ARIES](https://github.com/marcinpytlik/SQLManiak/blob/master/sqlmaniak_blog/ARIES/README.md)
