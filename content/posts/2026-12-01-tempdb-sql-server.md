---
title: "TempDB — co warto sprawdzić, zanim zacznie być problemem"
date: 2026-12-01T20:00:00+01:00
slug: tempdb-sql-server
description: "Praktyczna checklista TempDB w SQL Server: pliki, autogrowth, wolne miejsce, wykorzystanie, version store i symptomy problemów."
tags: [SQLServer, TempDB, Performance, DBA, Configuration]
categories: [SQL Server]
draft: false
---

TempDB jest współdzielona przez całą instancję.

Jeżeli zaczyna mieć problem, skutki mogą pojawić się w wielu bazach jednocześnie.

## Sprawdź pliki

```sql
SELECT
    file_id,
    name,
    type_desc,
    size * 8.0 / 1024 AS SizeMB,
    growth,
    is_percent_growth,
    physical_name
FROM tempdb.sys.database_files
ORDER BY file_id;
```

Zwróć uwagę na liczbę plików danych, ich rozmiary, autogrowth i lokalizację.

## Aktualne wykorzystanie

```sql
SELECT
    SUM(user_object_reserved_page_count) * 8.0 / 1024 AS UserObjectsMB,
    SUM(internal_object_reserved_page_count) * 8.0 / 1024 AS InternalObjectsMB,
    SUM(version_store_reserved_page_count) * 8.0 / 1024 AS VersionStoreMB,
    SUM(unallocated_extent_page_count) * 8.0 / 1024 AS FreeSpaceMB
FROM tempdb.sys.dm_db_file_space_usage;
```

## Version Store

Jeżeli używasz Snapshot Isolation albo RCSI, obserwuj version store. Długa transakcja może utrzymywać stare wersje rekordów znacznie dłużej, niż się spodziewasz.

## Autogrowth

Autogrowth powinien być zabezpieczeniem, a nie normalnym mechanizmem zapewniania przestrzeni.

## Podsumowanie

TempDB rzadko psuje się „nagle”. Zwykle wcześniej daje sygnały: wzrost wykorzystania, autogrowth, długie transakcje, I/O albo presję na version store.