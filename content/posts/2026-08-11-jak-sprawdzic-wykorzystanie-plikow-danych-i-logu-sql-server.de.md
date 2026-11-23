---
title: "Tatsächliche Auslastung von Datendateien und Transaktionslog prüfen"
date: 2026-08-11
slug: jak-sprawdzic-wykorzystanie-plikow-danych-i-logu-sql-server
description: "Praktische T-SQL-Abfragen zu Größe, Belegung und freiem Speicher in SQL-Server-Datendateien und Transaktionslogs."
tags: [SQLServer, MDF, NDF, LDF, TransactionLog, DBA, Monitoring]
categories: [SQL Server]
draft: false
---

Die Größe einer Datenbankdatei sagt noch nicht aus, wie viele Daten sie tatsächlich enthält.

Eine MDF-Datei kann 500 GB groß sein, aber nur 350 GB Daten enthalten. Eine Logdatei kann 100 GB umfassen, obwohl der aktive Teil des Logs nur wenige Gigabyte belegt.

Deshalb sollten wir bei der Diagnose drei Informationen unterscheiden:

- die physische Größe der Datei,
- den belegten Speicher innerhalb der Datei,
- den verfügbaren Speicher auf dem Volume.

## Datendateien und Logdateien sind zwei verschiedene Welten

MDF- und NDF-Dateien speichern Daten- und Indexseiten. Eine LDF-Datei enthält Transaktionslogeinträge.

Für Datendateien können wir `FILEPROPERTY` verwenden. Für das Log eignen sich `sys.dm_db_log_space_usage`, `DBCC SQLPERF(LOGSPACE)` und `log_reuse_wait_desc` besser.

## Grundlegende Dateiinformationen

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

## Speicherbelegung der Datendateien

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

Führe diese Abfrage im Kontext der zu untersuchenden Datenbank aus.

## Auslastung des Transaktionslogs

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

Wenn das Log zu 95 % belegt ist, beginne nicht mit einem Shrink.

Untersuche zuerst die Ursache:

```sql
SELECT
    name,
    recovery_model_desc,
    log_reuse_wait_desc
FROM sys.databases
WHERE database_id = DB_ID();
```

## Freier Speicher auf den Volumes

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

## Was sollte man bei der Diagnose prüfen?

1. Wie groß ist die Datei?
2. Wie viel Speicher ist belegt?
3. Ist eine maximale Dateigröße festgelegt?
4. Wie ist Autogrowth konfiguriert?
5. Wie viel freier Speicher ist auf dem Datenträger vorhanden?
6. Wie schnell wächst die Datenbank?
7. Betrifft das Problem die Datendateien oder das Log?

## Zusammenfassung

Die tatsächliche Speichernutzung lässt sich nur beurteilen, wenn mehrere Ebenen gemeinsam betrachtet werden.

Ein besonnener DBA fragt nicht nur:

> Wie groß ist die Datei?

Er fragt auch:

> Wie viel Speicher ist belegt, warum ist er belegt und wann wird der Platz knapp?
