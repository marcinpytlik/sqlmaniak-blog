---
title: "Backup VLDB > 4TB: jak dzielić na wiele plików i sprawnie odtwarzać"
date: "2025-10-04"
slug: "backup-vldb-split-multi-files"
draft: false
description: "Praktyczna strategia backupu/restore dla bardzo dużych baz: striped backup, kompresja, MAXTRANSFERSIZE, BUFFERCOUT."
tags: ["SQL Server", "Backup", "VLDB", "Restore", "Storage"]
author: "Marcin Pytlik | SQLManiak"
lang: "pl"
banner: "/images/backup-vldb-split-multi-files.png"
canonical: "https://sqlmaniak.blog/backup-vldb-split-multi-files"
---

Lead
----
Gdy FULL ma 4TB+, „zwykły” backup to ból. Użyj *striped backup* na wiele plików i odpowiednio dobierz parametry I/O.

## Backup w paskach
```sql
BACKUP DATABASE BigDb TO 
 DISK='X:\bck\BigDb_full_1.bak',
 DISK='X:\bck\BigDb_full_2.bak',
 DISK='Y:\bck\BigDb_full_3.bak',
 DISK='Y:\bck\BigDb_full_4.bak'
WITH COMPRESSION, STATS=5, CHECKSUM, MAXTRANSFERSIZE=4194304, BUFFERCOUNT=200;
```

## Restore równoległy
```sql
RESTORE DATABASE BigDb FROM 
 DISK='X:\bck\BigDb_full_1.bak', DISK='X:\bck\BigDb_full_2.bak',
 DISK='Y:\bck\BigDb_full_3.bak', DISK='Y:\bck\BigDb_full_4.bak'
WITH MOVE 'BigDb' TO 'D:\data\BigDb.mdf',
     MOVE 'BigDb_log' TO 'L:\log\BigDb.ldf',
     STATS=5, CHECKSUM, REPLACE;
```

## Tips
- Pliki rozłóż na różne LUN-y/kontrolery.  
- Testuj restore *częściej niż myślisz*.  
- Dokumentuj łańcuch BACKUP FULL → DIFF → LOG.
