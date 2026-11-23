---
title: "PAGE Restore: Database Surgery"
date: 2025-10-24
slug: page-restore
tags: [SQLServer, Backup, Restore, Internals, PageRestore]
draft: false
---

When a database contains billions of data pages, a full restore can feel like a heart transplant. Sometimes, however, a precise operation is enough: restoring only the damaged page. *PAGE restore* is SQL Server's surgical procedure for repairing a fragment rather than restoring the entire database.

## 🧩 The idea

SQL Server stores data in 8 KB pages. When a page is damaged by an I/O problem, disk failure, or checksum error, the engine can mark it as suspect. Under the right conditions, you can restore **only the affected page** from backup, without restoring the entire database or data file.

This is one of the most precise mechanisms in the **Database Engine recovery infrastructure**.

## 🧠 When PAGE RESTORE is possible

✅ The database must use the **FULL** or **BULK_LOGGED** recovery model.

✅ You need:
- A usable **full backup** (and possibly a differential backup).
- The required **transaction log backups** to bring the restored page forward.
- Identifiers of the damaged pages (`file_id:page_id`).

## 🔍 Diagnosis

```sql
-- sprawdź, które strony zostały oznaczone jako uszkodzone
SELECT database_id, file_id, page_id, event_type, error_count, last_update_date
FROM msdb.dbo.suspect_pages;
```

The `event_type` values include:
- `1` — error 823 (I/O).
- `2` — bad checksum.
- `3` — torn page.
- `4` — restored.
- `5` — deallocated.
- `7` — bad header.

## 🧪 Laboratory demonstration

```sql
-- 1️⃣ Wymuszenie błędu (symulacja – nie rób w produkcji!)
DBCC WRITEPAGE ('AdventureWorks2022', 1, 200, 0, 1, 0x45, 1);

-- 2️⃣ Próba odczytu
DBCC CHECKDB('AdventureWorks2022') WITH NO_INFOMSGS, ALL_ERRORMSGS;
GO
SELECT * FROM msdb.dbo.suspect_pages;

-- 3️⃣ PAGE RESTORE – przywracamy tylko uszkodzoną stronę (1:200)
RESTORE DATABASE AdventureWorks2022
PAGE='1:200'
FROM DISK = 'D:\Backups\AdventureWorks2022_FULL.bak'
WITH NORECOVERY;
GO

-- 4️⃣ Odtwarzamy logi, by baza była spójna
RESTORE LOG AdventureWorks2022
FROM DISK = 'D:\Backups\AdventureWorks2022_LOG.trn'
WITH RECOVERY;
GO
```

> The goal is to restore a single 8 KB page and return the database to a consistent state without a complete database restore. Actual recovery steps depend on the database state and available log backups.

**Warning:** `DBCC WRITEPAGE` deliberately corrupts a page. Use this example only in an isolated, disposable lab — never in production.

## 📊 Checking the result

```sql
SELECT * FROM msdb.dbo.suspect_pages WHERE event_type = 4;
```

An `event_type = 4` entry indicates that the suspect-page record was marked as restored.

## 🧰 Useful diagnostic tools

| Tool | Purpose |
|---|---|
| `DBCC CHECKDB` | Detect and report corruption. |
| `msdb.dbo.suspect_pages` | Track suspect-page events. |
| `DBCC PAGE` | Inspect an individual page (lab diagnostics). |
| `RESTORE HEADERONLY / FILELISTONLY` | Inspect backup metadata before recovery. |
| `sys.dm_io_virtual_file_stats` | Review I/O metrics while investigating the incident. |

## 🧩 A DBA's strategy

PAGE RESTORE is an emergency recovery tool, not a replacement for full backups. Include it in your disaster-recovery plan as a **targeted procedure**, for example:
- when a large database (over 1 TB) contains a small number of damaged pages,
- when restoring an entire database would cause excessive downtime,
- or when replicated data makes minimizing the recovery window especially important.

> “The art of repair lies in understanding which parts should be left untouched.”
> — *inspired by William James*

📚 **Repository:**
[SQLManiak/docs/PageRestore](https://github.com/marcinpytlik/SQLManiak/tree/master/docs/PageRestore.sql)

### 🧩 Checklist

- [ ] FULL / BULK_LOGGED recovery model.
- [ ] Identified `file_id:page_id`.
- [ ] Available full and required log backups.
- [ ] Backup verification with `RESTORE VERIFYONLY`.
- [ ] `RESTORE DATABASE … PAGE = 'X:Y' WITH NORECOVERY`.
- [ ] Required `RESTORE LOG` operations, followed by recovery.
- [ ] Validation using `DBCC CHECKDB` and `suspect_pages`.

*PAGE restore is surgery, not transplantation. You repair what needs attention rather than replacing everything.*
