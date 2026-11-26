---
title: "tempdb: Wann und wie man sie wirklich verkleinert — ohne Mythen"
date: "2025-10-04"
slug: "tempdb-shrink-bez-mitow"
draft: false
description: "Wachstum der tempdb diagnostizieren und ihre Größe mit einem praktischen Runbook, Skripten und Checkliste sicher reduzieren."
tags: ["SQL Server", "tempdb", "Performance", "DBA", "Runbook"]
author: "Marcin Pytlik | SQLManiak"
banner: "/images/tempdb-shrink-bez-mitow.png"
---

## Einleitung

tempdb ist weder ein Papierkorb noch ein magischer Puffer, der sich von selbst repariert. Wenn sie wächst, benötigen Abfragen, Sortierungen, Spools und Transaktionsversionierung zusätzlichen Platz. Hier ist ein praktisches Runbook ohne Mythen.

## Kurzfassung

1. Diagnostiziere, *warum* tempdb wächst: Version Store, Rehashing bei Hash Joins oder Spills.
2. Beseitige die Ursache: Ausführungspläne, Indizes, Hints und Memory Grants.
3. Erst danach kommt ein Shrink infrage — durch einen geplanten Dienstneustart oder `DBCC SHRINKFILE` mit passender Dateigröße.

## Diagnose: Was belegt tempdb?

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

### Häufige Probleme

- Dauerhafte Spills wegen fehlender Indizes oder zu kleiner Memory Grants.
- `READ_COMMITTED_SNAPSHOT` zusammen mit langen Transaktionen, wodurch Versionen nicht rechtzeitig bereinigt werden.
- Große Sortierungen oder `HASH MATCH`-Operationen auf `NVARCHAR(MAX)`- / `VARBINARY(MAX)`-Spalten.

## Wann und wie verkleinern?

- **Erst nach der Ursachenbehebung.** Sonst wächst tempdb erneut.
- **tempdb wird beim SQL-Server-Start neu angelegt.** Ein geplanter Neustart kann die konfigurierten Startgrößen wiederherstellen, muss aber als Ausfall geplant werden.

### Verfahren ohne Neustart

```sql
USE master;
-- 1) Przenieś tempdb do docelowego rozmiaru i plików
ALTER DATABASE tempdb MODIFY FILE (NAME = tempdev, SIZE = 8192MB, FILEGROWTH = 256MB);
ALTER DATABASE tempdb MODIFY FILE (NAME = templog, SIZE = 2048MB, FILEGROWTH = 256MB);
-- 2) Przytnij pliki (powtarzaj do skutku, obserwuj sys.dm_db_file_space_usage)
DBCC SHRINKFILE (tempdev, 8192);
DBCC SHRINKFILE (templog, 2048);
```

Das Beispiel legt Zielgrößen fest und fordert danach Shrink an. `MODIFY FILE` verkleinert eine bereits größere Datei nicht automatisch. `DBCC SHRINKFILE` erreicht die Zielgröße möglicherweise nicht, wenn Seiten nicht verschoben werden können.

> Mehrere passend dimensionierte tempdb-Datendateien können Allocation-Latch-Contention reduzieren. Beginne mit der Microsoft-Empfehlung und passe die Anzahl anhand der gemessenen Contention an; eine universelle Formel gibt es nicht.

```sql
-- Dodanie plików (przykład)
ALTER DATABASE tempdb ADD FILE (NAME = tempdev2, FILENAME='T:\tempdb\tempdb2.ndf', SIZE=8192MB, FILEGROWTH=256MB);
```

## Überprüfung

- Vergleiche freien und belegten Platz mit `sys.dm_db_file_space_usage`.
- Prüfe, ob der Version Store leer oder im erwarteten Bereich ist.
- Kontrolliere in Grafana weniger `tempdb used space` und das Ausbleiben dauerhafter Spills in Query Store.

## Checkliste

- [ ] Ursache des Wachstums ermittelt.
- [ ] Pläne, Indizes oder Memory Grants korrigiert.
- [ ] Sinnvolle `SIZE`- und `FILEGROWTH`-Werte konfiguriert.
- [ ] Zusätzliche Datendateien nur bei nachgewiesenem Bedarf ergänzt.
- [ ] Ergebnis im Monitoring überprüft.
