---
title: "TempDB: Der Spielplatz von SQL Server"
date: 2025-10-28
slug: tempdb-laboratorium
tags: [SQLServer, TempDB, Internals, IO, Performance]
draft: false
---

**TempDB ist das Labor von SQL Server.** Temporäre Tabellen, Sortierungen, Worktables, Spools, Hash-Operationen und Zeilenversionen für Snapshot Isolation können darauf angewiesen sein. Wenn die Datenbank der Verstand ist, dann ist *TempDB ihre Werkstatt*.

Eine überlastete TempDB bremst das gesamte System aus — wie eine zu kleine Werkbank.

## ⚙️ Was landet in TempDB?

- Temporäre Tabellen (`#local`, `##global`).
- Tabellenvariablen (`@table`).
- Sortier- und Hash-Arbeit für `ORDER BY`, `GROUP BY` und Joins.
- Zeilenversionen für Snapshot Isolation / RCSI, wenn der Version Store in TempDB liegt.
- Arbeiten von `DBCC CHECKDB`.
- Spools, Worktables und Workfiles.

## 🧠 TempDB-Architektur

TempDB wird **von der gesamten SQL-Server-Instanz gemeinsam verwendet** und bei jedem Start neu erstellt.

- Mehrere Datendateien und eine Transaktionsprotokolldatei.
- **Mehrere gleich große Datendateien** sind häufig sinnvoll, um Allocation Contention zu reduzieren.
- Verwende **feste Autogrowth-Schritte** statt Prozentwerten und dimensioniere die Dateien im Voraus.

## 🔍 DMVs untersuchen

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

## 🧪 Kurzer Test: TempDB unter Druck

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

Überwache während des Tests DMVs und Performance Counter.

## ⚖️ Bewährte Vorgehensweisen

- Erwäge mehrere Datendateien; beginne mit bewährten Empfehlungen und passe die Anzahl anhand gemessener Contention an, statt eine starre CPU-Datei-Formel zu verwenden.
- Halte Dateigrößen und Wachstumsschritte konsistent (zum Beispiel 512 MB).
- Verwende schnellen SSD-/NVMe-Speicher und passende Anfangsgrößen.
- Überwache `PAGELATCH_%`-Waits in `tempdb`:

```sql
SELECT * FROM sys.dm_os_waiting_tasks WHERE wait_type LIKE 'PAGELATCH_%' AND resource_description LIKE '2:%';
```

📂 Repository: [TempDB](https://github.com/marcinpytlik/SQLManiak/tree/master/sqlmaniak_blog/TEMP_DB)

> „Ohne kontrolliertes Chaos gibt es keine Kreativität.“ — inspiriert von Feynman
