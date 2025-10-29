---
title: "TempDB – plac zabaw SQL Servera"
date: 2025-10-28
slug: tempdb-laboratorium
tags: [SQLServer, TempDB, Internals, IO, Performance]
draft: false
---

**TempDB to laboratorium SQL Servera.**
Wszystko, co chwilowe – tabele tymczasowe, sortowania, wersje stron, spool’e, hash joiny, wersje snapshot isolation – trafia właśnie tam.
Jeśli baza danych to umysł, *TempDB jest jego warsztatem*.

Brak równowagi w TempDB spowalnia cały system, jak zbyt mały blat stołu w laboratorium.

## ⚙️ Co trafia do TempDB
- tabele tymczasowe (`#local`, `##global`)
- zmienne tabelaryczne (`@table`)
- sortowania i hashowania (ORDER BY, GROUP BY, JOIN)
- wersje stron przy snapshot isolation / RCSI
- operacje DBCC CHECKDB
- spool’e i worktable/workfile

## 🧠 Architektura TempDB
TempDB jest **wspólna dla całego serwera** (jedna na instancję) i odtwarza się przy restarcie.
- wiele plików danych + jeden plik logu
- zalecane **wiele równych plików danych**
- autogrowth w **MB** (nie w %), pre-size po starcie

## 🔍 Zajrzyj w DMV
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

## 🧪 Szybki test – presja na TempDB
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
Podczas testu śledź DMV i perfmon.

## ⚖️ Dobre praktyki
- 1 plik na rdzeń do 8, potem ~¼ rdzeni (zwykle 8–12)
- równe rozmiary i growth w MB (np. 512 MB)
- szybki dysk (SSD/NVMe), pre-size po starcie
- monitoruj `PAGELATCH_%` na `tempdb`:
```sql
SELECT * FROM sys.dm_os_waiting_tasks WHERE wait_type LIKE 'PAGELATCH_%' AND resource_description LIKE '2:%';
```
📂 Repo: [TempDB](https://github.com/marcinpytlik/SQLManiak/tree/master/sqlmaniak_blog/TEMP_DB)
> „Nie ma kreatywności bez kontrolowanego chaosu.” — inspiracja: Feynman
