---
title: "Wann kompiliert SQL Server einen neuen Abfrageplan?"
date: 2025-11-03
slug: kompilacja-planow
tags: [SQLServer, Internals, QueryOptimizer, PlanCache]
draft: false
---

SQL Server ist clever: Er kompiliert nicht bei jeder Ausführung neu, sondern nur, wenn es nötig ist. Die Engine sucht zunächst im **Plan Cache** nach einem wiederverwendbaren Plan. Ist ein passender Plan vorhanden, kann sie ihn erneut nutzen.

### 🔍 Wann wird ein neuer Plan kompiliert?

Eine Kompilierung kann erfolgen, wenn:

- **Kein passender Plan** im Cache vorhanden ist.
- **Statistiken geändert wurden** und ein Plan dadurch ungültig wird (`AUTO_UPDATE_STATISTICS`).
- **Eine Neukompilierung angefordert wird**, etwa durch `RECOMPILE` oder `OPTION (RECOMPILE)`.
- **Parameter Sensitive Plan Optimization** für geeignete parametrisierte Abfragen Planvarianten auswählt oder erzeugt; ein geänderter Parameterwert allein erzwingt nicht zwangsläufig eine Neukompilierung.
- **Ein Plan entfernt oder verdrängt wurde**, beispielsweise durch `DBCC FREEPROCCACHE`.

### 🧠 Wie untersuchen wir den Cache?

```sql
-- podejrzyj, ile planów trzyma SQL Server
SELECT COUNT(*) AS PlansInCache FROM sys.dm_exec_cached_plans;

-- zobacz najczęściej używane plany
SELECT TOP 10 usecounts, objtype, cacheobjtype, size_in_bytes / 1024 AS KB,
       DB_NAME(st.dbid) AS DatabaseName, st.text
FROM sys.dm_exec_cached_plans cp
CROSS APPLY sys.dm_exec_sql_text(cp.plan_handle) st
ORDER BY usecounts DESC;
```

### 🧩 Warum ist das wichtig?

Häufige Neukompilierungen können unnötig CPU verbrauchen. Umgekehrt kann die Wiederverwendung eines ungeeigneten Plans zu Performanceproblemen durch Parameter Sniffing führen.

Die richtige Balance ist entscheidend für die Performance von SQL Server.

> „Nicht jedes Problem benötigt einen neuen Plan — manchmal reicht es, sich an den richtigen alten zu erinnern.“ — SQLManiak
