---
title: "Ghost Cleanup Task w akcji"
date: 2025-10-24
slug: ghost-cleanup-task
tags: [SQLServer, Internals, GhostRecords, DMV, Performance]
draft: false
---

SQL Server przypomina organizm, który potrafi sam utrzymać czystość. Gdy rekord zostaje usunięty, jego duch nie znika od razu — pozostaje w strukturze danych, jak ślad po zmarłej komórce. Dopiero *Ghost Cleanup Task* przychodzi, by po cichu posprzątać, przywracając równowagę systemu.

To układ odpornościowy SQL Servera – działa w tle, gdy nikt nie patrzy, i dba o to, by baza nie zarosła martwymi danymi.

### 🔍 Zajrzyj w DMV
```sql
-- znajdź indeksy zawierające ghost records
SELECT object_name(object_id) AS TableName, index_id, ghost_record_count
FROM sys.dm_db_index_physical_stats(DB_ID(), NULL, NULL, NULL, 'DETAILED')
WHERE ghost_record_count > 0;
```

> „Porządek nie polega na braku chaosu, lecz na jego kontrolowaniu.” — Kant
