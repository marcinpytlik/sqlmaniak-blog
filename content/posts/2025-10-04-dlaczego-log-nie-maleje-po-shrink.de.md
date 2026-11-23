---
title: "Warum die Transaktionsprotokolldatei trotz SHRINK nicht kleiner wird"
date: "2025-10-04"
slug: "dlaczego-log-nie-maleje-po-shrink-de"
draft: false
description: "Ein Leitfaden zu Hindernissen beim Log-Shrink: VLFs, offene Transaktionen, fehlende Log-Backups und Replikation."
tags: ["Transaction Log","VLF","Backup"]
author: "Marcin Pytlik | SQLManiak"
banner: "/images/dlaczego-log-nie-maleje-po-shrink.png"

---

## Einleitung
„Ich habe SHRINK ausgeführt und nichts ist passiert.“ Ein Klassiker. Eine Protokolldatei lässt sich nicht verkleinern, wenn ein *aktiver Log-Bereich* am Dateiende liegt oder Transaktionen offen bleiben. Wir untersuchen das Schritt für Schritt.

## Schnelldiagnose
```sql
-- Aktywny log, VLF-y
DBCC LOGINFO;   -- w nowszych wersjach: sys.dm_db_log_info(DB_ID())

SELECT vlf_sequence_number, vlf_active, file_id FROM sys.dm_db_log_info(DB_ID())
ORDER BY vlf_sequence_number;
```

### Häufigste Hindernisse
- Offene oder lang laufende Transaktionen, auch vergessene implizite Transaktionen in SSMS.
- Fehlende Log-Backup-Kette: FULL-Recovery ohne `BACKUP LOG`.
- Replikation, CDC oder Log Shipping halten Log-Einträge zurück.
- Zu viele kleine VLFs durch winzige FILEGROWTH-Schritte.

## Speicherplatz zurückgewinnen
1. **Log-Backup erstellen** bei FULL oder BULK_LOGGED.
2. **Lang laufende Transaktionen ermitteln und behandeln**:
```sql
SELECT s.session_id, r.start_time, r.status, r.command, r.wait_type, s.login_name, s.host_name
FROM sys.dm_exec_requests r
JOIN sys.dm_exec_sessions s ON s.session_id=r.session_id
WHERE r.database_id = DB_ID();
```
3. **Replikation oder CDC nur bei betrieblicher Sicherheit pausieren**.
4. **Kontrolliert verkleinern**:
```sql
USE MyDb;
DBCC SHRINKFILE (MyDb_log, 102400); -- target w MB
```
5. **Sinnvolles FILEGROWTH und eine Basisgröße festlegen**, beispielsweise 64–128 GB für starkes OLTP, anhand von Messwerten.

## VLF-Pflege
- Prüfe die Anzahl der VLFs; Hunderte sind sinnvoller als Zehntausende.
- Plane gegebenenfalls BACKUP LOG → SHRINKFILE → Vergrößerung in einem Schritt.
```sql
-- Przykład: ustaw 64GB i growth 4GB
DBCC SHRINKFILE (MyDb_log, 1024); -- tymczasowe przycięcie
ALTER DATABASE MyDb MODIFY FILE (NAME=MyDb_log, SIZE=65536MB, FILEGROWTH=4096MB);
```

## Überprüfung und Monitoring
- Verwende `sys.dm_db_log_space_usage` und `sys.dm_db_log_stats(DB_ID())`.
- Beobachte in Grafana Log-Auslastung, VLF-Anzahl und Autogrowth-Häufigkeit.

## Anti-Patterns
- Nächtliches Shrinken verursacht unnötiges Nachwachsen und kann Leistung kosten.
- Sehr kleine FILEGROWTH-Schritte erzeugen übermäßig viele VLFs.
- FULL-Recovery ohne Log-Backup-Strategie.
