---
title: "When Does SQL Server Compile a New Query Plan?"
date: 2025-11-03
slug: kompilacja-planow
tags: [SQLServer, Internals, QueryOptimizer, PlanCache]
draft: false
---

SQL Server is clever. It does not compile a new plan for every execution — it does so **when compilation is needed**. Before executing a query, the engine checks the *plan cache*. If a suitable cached plan exists, it may reuse it.

### 🔍 When is a new plan created?

Compilation or recompilation may occur when:
- **no suitable plan** is available in the cache,
- **statistics change** and a relevant recompile threshold is reached,
- **a recompilation option** is used (`RECOMPILE`, `OPTION (RECOMPILE)`),
- **Parameter Sensitive Plan Optimization** selects among previously compiled variants for different parameter ranges; selection itself does not necessarily mean a new compilation,
- or **a plan is evicted** from the cache, for example after `DBCC FREEPROCCACHE`.

### 🧠 How can you inspect this?

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

### 🧩 Why does it matter?

Frequent recompilation can consume unnecessary CPU. On the other hand, overly aggressive reuse can expose *parameter sniffing* problems. Balancing these behaviors is one of the keys to SQL Server performance.

> “Not every good decision needs a new plan — sometimes remembering the old one is enough.” — SQLManiak
