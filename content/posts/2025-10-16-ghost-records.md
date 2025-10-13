---
title: "Ghost Records – duchy w bazie danych"
date: 2025-10-16
slug: ghost-records
tags: [SQLServer, Internals, DBCC, GhostCleanup, DBA]
draft: false
---

W bazie danych straszy.  
Nie w horrorze, ale w DMV: `sys.dm_db_index_physical_stats`.  
Gdy kasujesz wiersz, SQL Server nie usuwa go od razu — zostawia „ducha” (ghost record), który czeka, aż *ghost cleanup task* wykona egzorcyzm.

To dzięki temu `ROLLBACK` może przywrócić dane — a `DELETE` nie musi blokować świata.

> „To, czego nie widzisz, nie znaczy, że tego nie ma — zwłaszcza w bazie danych.”

Zajrzyj do wnętrza i poznaj, jak działa system, który dba o spójność nawet po katastrofie.
