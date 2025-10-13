---
title: "Walec ARIES – jak SQL zapisuje historię transakcji"
date: 2025-10-29
slug: walec-aries
tags: [SQLServer, Internals, WAL, ARIES, Recovery]
draft: false
---

ARIES (Algorithm for Recovery and Isolation Exploiting Semantics) to dusza systemu transakcyjnego.  
Każda zmiana w SQL Serverze zostaje zapisana w logu zanim trafi na dysk — to zasada *Write-Ahead Logging*.  
Log to pamiętnik: nie kłamie, nie zapomina i pozwala cofnąć czas.

### 🔍 Zajrzyj w DMV
```sql
-- zobacz aktywność logu transakcyjnego
SELECT name, log_reuse_wait_desc, recovery_model_desc
FROM sys.databases
WHERE database_id = DB_ID();
```

> „Historia to pamięć systemu.” — SQLManiak
