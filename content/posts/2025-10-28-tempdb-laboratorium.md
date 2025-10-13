---
title: "TempDB – plac zabaw SQL Servera"
date: 2025-10-28
slug: tempdb-laboratorium
tags: [SQLServer, TempDB, Internals, IO, Performance]
draft: false
---

TempDB to laboratorium SQL Servera. Wszystko, co chwilowe – tabele tymczasowe, sortowania, wersje stron – trafia właśnie tam.  
Jeśli baza danych to umysł, TempDB jest jego warsztatem. Brak równowagi w TempDB spowalnia cały system, jak zbyt mały blat stołu w laboratorium.

### 🔍 Zajrzyj w DMV
```sql
-- pokaż aktywność w TempDB
SELECT database_id, file_id, num_of_writes, num_of_reads
FROM sys.dm_io_virtual_file_stats(DB_ID('tempdb'), NULL);
```

> „Nie ma kreatywności bez kontrolowanego chaosu.” — inspiracja: Feynman
