---
title: "Ghost Records: Ghosts in the Database"
date: 2025-10-16
slug: ghost-records
tags: [SQLServer, Internals, DBCC, GhostCleanup, DBA]
draft: false
---

The database is haunted. Not in a horror movie, but in the DMV `sys.dm_db_index_physical_stats`. When you delete a row, SQL Server does not necessarily remove it immediately. Instead, it leaves behind a **ghost record** waiting for the *ghost cleanup task* to perform its exorcism.

This approach supports transactional rollback and avoids unnecessary disruption during `DELETE`. The engine prefers to mark a record as deleted rather than immediately rearrange the data page.

> “Just because you cannot see something does not mean it is not there — especially in a database.”

---

### How a ghost is created

When you execute `DELETE`, SQL Server:
1. Marks the record as *ghosted* using metadata in its record header.
2. Makes the deleted record invisible to ordinary queries.
3. Leaves the bytes on the data page until they can be cleaned up safely.

This is not a bug; it is a **performance and recovery mechanism**. It helps the engine roll back changes and coordinate concurrent operations without immediately removing every deleted record.

---

### The exorcism: Ghost Cleanup Task

Periodically, the background *ghost cleanup task* finds and physically removes eligible ghost records. It cannot always do so immediately. SQL Server must account for:
- active transactions that may still need the record,
- row versions required by concurrent readers,
- locking or other conditions that delay cleanup.

Ghost records can therefore persist longer after large deletes, long-running transactions, or when **READ_COMMITTED_SNAPSHOT** is enabled and readers retain versions in tempdb.

---

### How to find them

You cannot see ghosts with `SELECT *`, but you can look for them with diagnostic tools:

```sql
DBCC CHECKTABLE ('TwojaTabela') WITH TABLERESULTS;
```

The output can include a `GhostRecCnt` value showing records awaiting cleanup. You can also examine the DMV:

```sql
SELECT
    object_name(object_id) AS [Tabela],
    index_type_desc,
    ghost_record_count
FROM sys.dm_db_index_physical_stats(DB_ID(), NULL, NULL, NULL, 'DETAILED')
WHERE ghost_record_count > 0;
```

---

### When ghosts do not disappear

Sometimes *ghost cleanup* cannot keep up, for example after heavy `DELETE` activity. A diagnostic command sometimes used in controlled environments is:

```sql
DBCC FORCEGHOSTCLEANUP;
```

This explicitly requests ghost cleanup. Be careful: it can generate I/O, so consider its impact and avoid using it casually on production systems.

---

### Why does this matter?

Ghost records are part of SQL Server's broader recovery and concurrency machinery, which relies on **write-ahead logging** and transactional consistency. A deletion is not always an instantaneous physical removal.

Deleting data is a process, not a moment. Every `DELETE` is a promise that the engine will eventually clean up when it is safe.

---

> “Sometimes what is dead still lives — until the transaction log records that it is truly gone.”

---

### Experiment

Try it yourself:

```sql
CREATE TABLE GhostDemo(Id INT IDENTITY PRIMARY KEY, Data CHAR(200) DEFAULT 'x');
GO
INSERT INTO GhostDemo DEFAULT VALUES;
GO 1000
DELETE FROM GhostDemo WHERE Id <= 900;
GO
DBCC CHECKTABLE('GhostDemo') WITH TABLERESULTS;
```

Check `GhostRecCnt` and observe how long deleted records remain. Wait a little and run the check again to see whether cleanup has caught up.

---

Looking into ghost records is like observing the **in-between state of data** — the space between “was there” and “is gone.” SQL Server understands these boundaries, keeping our data world orderly even when it occasionally seems haunted.
