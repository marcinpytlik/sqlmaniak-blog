---
title: "When Does SQL Server Compile a New Query Plan?"
date: 2025-11-03
slug: kompilacja-planow
tags: [SQLServer, Internals, QueryOptimizer, PlanCache]
draft: false
---

SQL Server is clever: it does not compile a plan on every execution, but only when necessary. For each execution, the engine first looks for a reusable plan in the **plan cache**. When it finds a suitable cached plan, it can reuse it.

### 🔍 When Is a New Plan Compiled?

Compilation may happen when:

- **No matching plan** exists in the cache.
- **Statistics change**, potentially invalidating a plan (`AUTO_UPDATE_STATISTICS`).
- **Recompilation is requested** through `RECOMPILE` or `OPTION (RECOMPILE)`.
- **Parameter-sensitive plan optimization** chooses or creates plan variants for eligible parameterized queries; changing a parameter value alone does not necessarily force recompilation.
- **A plan is evicted or cleared**, for example through `DBCC FREEPROCCACHE`.

### 🧠 How Can We Inspect the Cache?

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

### 🧩 Why Does This Matter?

Frequent recompilations can waste CPU. Conversely, excessive reuse of an unsuitable plan can cause parameter-sniffing performance problems.

Finding the right balance is central to SQL Server performance.

> “Not every problem requires a new plan; sometimes remembering the right old one is enough.” — SQLManiak
