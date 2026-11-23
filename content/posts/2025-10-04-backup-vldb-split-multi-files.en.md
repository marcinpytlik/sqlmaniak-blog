---
title: "VLDB backups over 4 TB: splitting across files and restoring efficiently"
date: "2025-10-04"
slug: "backup-vldb-split-multi-files-en"
draft: false
description: "A practical backup and restore strategy for very large databases: striped backups, compression, MAXTRANSFERSIZE and BUFFERCOUNT."
tags: ["Backup","Restore","Storage"]
author: "Marcin Pytlik | SQLManiak"
banner: "/images/backup-vldb-split-multi-files.png"

---

## Introduction
When a FULL backup exceeds 4 TB, a conventional single-file backup becomes cumbersome. Use a *striped backup* across multiple files and tune the I/O parameters appropriately.

## Striped backup
```sql
BACKUP DATABASE BigDb TO 
 DISK='X:\bck\BigDb_full_1.bak',
 DISK='X:\bck\BigDb_full_2.bak',
 DISK='Y:\bck\BigDb_full_3.bak',
 DISK='Y:\bck\BigDb_full_4.bak'
WITH COMPRESSION, STATS=5, CHECKSUM, MAXTRANSFERSIZE=4194304, BUFFERCOUNT=200;
```

## Parallel restore
```sql
RESTORE DATABASE BigDb FROM 
 DISK='X:\bck\BigDb_full_1.bak', DISK='X:\bck\BigDb_full_2.bak',
 DISK='Y:\bck\BigDb_full_3.bak', DISK='Y:\bck\BigDb_full_4.bak'
WITH MOVE 'BigDb' TO 'D:\data\BigDb.mdf',
     MOVE 'BigDb_log' TO 'L:\log\BigDb.ldf',
     STATS=5, CHECKSUM, REPLACE;
```

## Tips
- Distribute files across separate LUNs or controllers.
- Test restores *more often than you think necessary*.
- Document the FULL → DIFF → LOG backup chain.
