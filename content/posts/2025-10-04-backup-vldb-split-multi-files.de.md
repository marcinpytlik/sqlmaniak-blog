---
title: "VLDB-Backups über 4 TB: Aufteilung auf mehrere Dateien und effiziente Wiederherstellung"
date: "2025-10-04"
slug: "backup-vldb-split-multi-files-de"
draft: false
description: "Eine praktische Backup- und Restore-Strategie für sehr große Datenbanken: Striping, Komprimierung, MAXTRANSFERSIZE und BUFFERCOUNT."
tags: ["Backup","Wiederherstellung","Storage"]
author: "Marcin Pytlik | SQLManiak"
banner: "/images/backup-vldb-split-multi-files.png"

---

## Einleitung
Wenn ein FULL-Backup 4 TB überschreitet, wird ein herkömmliches Backup in eine Datei unhandlich. Verwende ein *Striped Backup* mit mehreren Dateien und passe die I/O-Parameter an.

## Backup mit mehreren Stripes
```sql
BACKUP DATABASE BigDb TO 
 DISK='X:\bck\BigDb_full_1.bak',
 DISK='X:\bck\BigDb_full_2.bak',
 DISK='Y:\bck\BigDb_full_3.bak',
 DISK='Y:\bck\BigDb_full_4.bak'
WITH COMPRESSION, STATS=5, CHECKSUM, MAXTRANSFERSIZE=4194304, BUFFERCOUNT=200;
```

## Parallele Wiederherstellung
```sql
RESTORE DATABASE BigDb FROM 
 DISK='X:\bck\BigDb_full_1.bak', DISK='X:\bck\BigDb_full_2.bak',
 DISK='Y:\bck\BigDb_full_3.bak', DISK='Y:\bck\BigDb_full_4.bak'
WITH MOVE 'BigDb' TO 'D:\data\BigDb.mdf',
     MOVE 'BigDb_log' TO 'L:\log\BigDb.ldf',
     STATS=5, CHECKSUM, REPLACE;
```

## Tipps
- Verteile Dateien auf unterschiedliche LUNs bzw. Controller.
- Teste Wiederherstellungen *häufiger als gedacht*.
- Dokumentiere die Backup-Kette FULL → DIFF → LOG.
