---
title: "Jak sprawdzić rzeczywiste wykorzystanie plików danych i logu transakcyjnego?"
date: 2026-08-11
slug: jak-sprawdzic-wykorzystanie-plikow-danych-i-logu-sql-server
description: "Praktyczne zapytania T-SQL pokazujące rozmiar, zajętość i wolne miejsce w plikach danych oraz logu transakcyjnym SQL Server."
tags: [SQLServer, MDF, NDF, LDF, TransactionLog, DBA, Monitoring]
categories: [SQL Server]
draft: false
---

Rozmiar pliku bazy danych nie mówi jeszcze, ile danych rzeczywiście się w nim znajduje.

Plik MDF może mieć 500 GB, ale zawierać tylko 350 GB danych. Plik logu może mieć 100 GB, mimo że aktywna część logu zajmuje zaledwie kilka gigabajtów.

Dlatego podczas diagnostyki warto rozdzielić trzy informacje:

- fizyczny rozmiar pliku,
- przestrzeń zajętą wewnątrz pliku,
- przestrzeń dostępną na woluminie.

## Pliki danych i plik logu to dwa różne światy

Pliki MDF i NDF przechowują strony danych oraz indeksów. Plik LDF przechowuje rekordy logu transakcyjnego.

Dla plików danych możemy użyć `FILEPROPERTY`. Dla logu lepiej wykorzystać `sys.dm_db_log_space_usage`, `DBCC SQLPERF(LOGSPACE)` oraz `log_reuse_wait_desc`.

## Podstawowe informacje o plikach

```sql
SELECT
    DB_NAME() AS DatabaseName,
    file_id,
    name AS LogicalFileName,
    type_desc AS FileType,
    physical_name,
    size / 128.0 AS FileSizeMB,
    CASE
        WHEN max_size = -1 THEN NULL
        ELSE max_size / 128.0
    END AS MaxSizeMB,
    CASE
        WHEN is_percent_growth = 1
            THEN CONCAT(growth, '%')
        ELSE CONCAT(growth / 128.0, ' MB')
    END AS FileGrowth
FROM sys.database_files
ORDER BY file_id;
```

## Zajętość plików danych

```sql
SELECT
    DB_NAME() AS DatabaseName,
    df.file_id,
    df.name AS LogicalFileName,
    df.physical_name,
    df.size / 128.0 AS FileSizeMB,
    FILEPROPERTY(df.name, 'SpaceUsed') / 128.0 AS UsedSpaceMB,
    (df.size - FILEPROPERTY(df.name, 'SpaceUsed')) / 128.0 AS FreeSpaceMB,
    CAST(
        100.0 * FILEPROPERTY(df.name, 'SpaceUsed')
        / NULLIF(df.size, 0)
        AS decimal(10,2)
    ) AS UsedPercent
FROM sys.database_files AS df
WHERE df.type = 0
ORDER BY df.file_id;
```

To zapytanie należy wykonać w kontekście analizowanej bazy.

## Wykorzystanie logu transakcyjnego

```sql
SELECT
    DB_NAME() AS DatabaseName,
    total_log_size_in_bytes / 1024.0 / 1024 AS TotalLogSizeMB,
    used_log_space_in_bytes / 1024.0 / 1024 AS UsedLogSpaceMB,
    used_log_space_in_percent AS UsedLogSpacePercent,
    log_space_in_bytes_since_last_backup / 1024.0 / 1024
        AS LogGeneratedSinceLastBackupMB
FROM sys.dm_db_log_space_usage;
```

Jeżeli log jest zajęty w 95%, nie zaczynaj od shrink.

Najpierw sprawdź przyczynę:

```sql
SELECT
    name,
    recovery_model_desc,
    log_reuse_wait_desc
FROM sys.databases
WHERE database_id = DB_ID();
```

## Wolne miejsce na woluminach

```sql
SELECT DISTINCT
    vs.volume_mount_point,
    vs.logical_volume_name,
    vs.total_bytes / 1024.0 / 1024 / 1024 AS TotalSizeGB,
    vs.available_bytes / 1024.0 / 1024 / 1024 AS FreeSpaceGB,
    CAST(
        100.0 * vs.available_bytes / NULLIF(vs.total_bytes, 0)
        AS decimal(10,2)
    ) AS FreeSpacePercent
FROM sys.master_files AS mf
CROSS APPLY sys.dm_os_volume_stats(mf.database_id, mf.file_id) AS vs
ORDER BY vs.volume_mount_point;
```

## Co sprawdzać podczas diagnostyki?

1. Ile miejsca ma plik?
2. Ile miejsca jest wykorzystane?
3. Czy plik ma ustawiony limit?
4. Jak skonfigurowano autogrowth?
5. Ile miejsca pozostało na dysku?
6. Jak szybko baza rośnie?
7. Czy problem dotyczy danych, czy logu?

## Podsumowanie

Rzeczywiste wykorzystanie przestrzeni wymaga spojrzenia na kilka warstw jednocześnie.

Spokojny DBA nie pyta wyłącznie:

> Jak duży jest plik?

Pyta również:

> Ile miejsca jest zajęte, dlaczego jest zajęte i kiedy skończy się przestrzeń?
