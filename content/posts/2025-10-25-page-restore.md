---
title: "PAGE Restore – chirurgia bazy danych"
date: 2025-10-25
slug: page-restore
tags: [SQLServer, Backup, Restore, Internals, PageRestore]
draft: false
---

Kiedy baza ma miliardy stron danych, pełny restore bywa jak przeszczep serca. Ale czasem wystarczy precyzyjna operacja – przywrócenie tylko uszkodzonej strony.  
*PAGE restore* to chirurgiczna procedura SQL Servera: przywraca fragment, nie zatrzymując całego organizmu.

### 🔍 Zajrzyj w DMV
```sql
-- sprawdź, które strony zostały oznaczone jako uszkodzone
SELECT * FROM msdb.dbo.suspect_pages;
```

> „Sztuka naprawy polega na zrozumieniu, które fragmenty należy zostawić w spokoju.” — insp. William James
