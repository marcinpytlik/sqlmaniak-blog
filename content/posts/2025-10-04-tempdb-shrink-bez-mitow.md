---
title: "tempdb: kiedy i jak naprawdę ją shrinkować (bez mitów)"
date: "2025-10-04"
slug: "tempdb-shrink-bez-mitow"
draft: false
description: "Jak diagnozować rozrost tempdb i bezpiecznie ją przyciąć – krok po kroku, z gotowymi skryptami i checklistą weryfikacji."
tags: ["SQL Server", "tempdb", "Performance", "DBA", "Runbook"]
author: "Marcin Pytlik | SQLManiak"
lang: "pl"
banner: "/images/tempdb-shrink-bez-mitow.png"
canonical: "https://sqlmaniak.blog/tempdb-shrink-bez-mitow"
---

Lead
----
tempdb to nie kosz na śmieci ani magiczny bufor, który „sam się ogarnia”. Jeśli rośnie – to dlatego, że Twoje zapytania, sortowania, spule i wersjonowanie transakcji potrzebują miejsca. Tu masz praktyczny runbook bez mitów.

## TL;DR
1) Zdiagnozuj *dlaczego* rośnie (`version store`, rehash w hash joinach, spill do tempdb).  
2) Usuń przyczynę (plany, indeksy, hinty, rozmiary pamięci).  
3) Dopiero na końcu — shrink z restartem usługi lub `DBCC SHRINKFILE` + `ALTER DATABASE tempdb MODIFY FILE`.

## Diagnoza: co zżera tempdb
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

### Klasyka błędów
- *Nieustanny spill* przez brak indeksu lub zbyt mało pamięci w grantach.  
- Uruchomione `READ_COMMITTED_SNAPSHOT` + długie transakcje → wersje nie są zbierane.  
- Potężne sortowania/`HASH MATCH` na kolumnach NVARCHAR(MAX)/VARBINARY(MAX).

## Kiedy i jak shrinkować
- **Po usunięciu przyczyny.** Inaczej wróci jak bumerang.
- **tempdb resetuje się przy starcie usługi.** Najczystszy shrink to okno serwisowe + restart SQL Server.

### Procedura bez restartu
```sql
USE master;
-- 1) Przenieś tempdb do docelowego rozmiaru i plików
ALTER DATABASE tempdb MODIFY FILE (NAME = tempdev, SIZE = 8192MB, FILEGROWTH = 256MB);
ALTER DATABASE tempdb MODIFY FILE (NAME = templog, SIZE = 2048MB, FILEGROWTH = 256MB);
-- 2) Przytnij pliki (powtarzaj do skutku, obserwuj sys.dm_db_file_space_usage)
DBCC SHRINKFILE (tempdev, 8192);
DBCC SHRINKFILE (templog, 2048);
```

> Wiele mniejszych plików danych (po 1 na 4 rdzenie, max 8) pomaga z latchami PFS/GAM/SGAM.
```sql
-- Dodanie plików (przykład)
ALTER DATABASE tempdb ADD FILE (NAME = tempdev2, FILENAME='T:\tempdb\tempdb2.ndf', SIZE=8192MB, FILEGROWTH=256MB);
```

## Weryfikacja
- `sys.dm_db_file_space_usage` – wolne vs użyte.  
- Brak aktywnego version store (lub w normie).  
- W Grafanie: spadek `tempdb used space`, brak długich spillów w Query Store.

## Checklista „done”
- [ ] Zidentyfikowana przyczyna rozrostu  
- [ ] Poprawione plany/indeksy/granty pamięci  
- [ ] Ustawione rozsądne SIZE/FILEGROWTH  
- [ ] Ewentualne dodatkowe pliki danych (1/4 rdzeni, ≤8)  
- [ ] Wynik zweryfikowany w monitoringu
