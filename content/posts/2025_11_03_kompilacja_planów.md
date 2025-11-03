---
title: "Kiedy SQL Server kompiluje nowy plan zapytania?"
date: 2025-11-05
slug: kompilacja-planow
tags: [SQLServer, Internals, QueryOptimizer, PlanCache]
draft: false
---

SQL Server jest sprytny. Nie kompiluje planów za każdym razem — robi to **tylko wtedy, gdy naprawdę musi**.  
Za każdym wykonaniem zapytania optymalizator najpierw zagląda do *plan cache*. Jeśli znajdzie pasujący plan – użyje go ponownie (to tzw. *re-use*).  

### 🔍 Kiedy powstaje nowy plan?

Nowy plan kompilowany jest m.in. gdy:
- **brak pasującego planu** w cache,
- **zmieniły się statystyki** (AUTO_UPDATE_STATISTICS),
- **użyto opcji zmieniającej kontekst** (`RECOMPILE`, `OPTION (RECOMPILE)`),
- **parametry** zmieniły selektywność (i włącza się *Parameter Sensitive Plan Optimization*),
- lub **plan został usunięty** z cache (np. po `DBCC FREEPROCCACHE`).

### 🧠 Jak to podejrzeć?

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

### 🧩 Dlaczego to ważne?

Częste rekompilacje = niepotrzebne zużycie CPU.  
Z kolei zbyt agresywne ponowne używanie planów może prowadzić do *parameter sniffing*.  
Balans pomiędzy tymi zjawiskami to jedna z tajemnic wydajności SQL Servera.

> „Nie każda mądrość wymaga nowego planu – czasem wystarczy dobrze pamiętać stary.” — SQLManiak
