---
title: "Wann kompiliert SQL Server einen neuen Abfrageplan?"
date: 2025-11-03
slug: kompilacja-planow
tags: [SQLServer, Internals, QueryOptimizer, PlanCache]
draft: false
---

SQL Server ist clever. Er kompiliert nicht bei jeder Ausführung einen neuen Plan, sondern **wenn eine Kompilierung erforderlich ist**. Vor der Ausführung prüft die Engine den *Plan Cache*. Ist ein passender Plan vorhanden, kann er wiederverwendet werden.

### 🔍 Wann entsteht ein neuer Plan?

Eine Kompilierung oder Neukompilierung kann stattfinden, wenn:
- **kein passender Plan** im Cache verfügbar ist,
- **sich Statistiken ändern** und eine relevante Recompile-Schwelle erreicht wird,
- **eine Recompile-Option** verwendet wird (`RECOMPILE`, `OPTION (RECOMPILE)`),
- **Parameter Sensitive Plan Optimization** zwischen bereits kompilierten Varianten für unterschiedliche Parameterbereiche auswählt; die Auswahl selbst bedeutet nicht zwangsläufig eine Neukompilierung,
- oder **ein Plan aus dem Cache entfernt** wird, beispielsweise nach `DBCC FREEPROCCACHE`.

### 🧠 Wie kannst du das untersuchen?

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

Häufige Neukompilierungen können unnötig CPU verbrauchen. Andererseits kann eine zu aggressive Wiederverwendung zu *Parameter-Sniffing*-Problemen führen. Das Gleichgewicht zwischen diesen Effekten ist einer der Schlüssel zur SQL-Server-Performance.

> „Nicht jede gute Entscheidung braucht einen neuen Plan — manchmal reicht es, sich an den alten zu erinnern.“ — SQLManiak
