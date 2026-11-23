---
title: "Query Store: Memory of Plans, Memory of Mistakes"
date: 2025-10-26
slug: query-store-memory
tags: [SQLServer, QueryStore, Performance, Internals, Plans]
draft: false
---

Query Store is SQL Server's long-term memory: it records plans, decisions, and sometimes mistakes. By retaining query execution history, it allows DBAs to track how performance evolves and learn from regressions. Think of it as a diary of previous days, sometimes full of insights, sometimes regrets.

## 🧠 How Query Store works

Queries processed by SQL Server may be captured in **Query Store**, together with execution plans and runtime statistics. Over time, the engine accumulates evidence about which plans performed well and which caused regressions.

> You might call Query Store SQL Server's “black box”: it records evidence of optimizer decisions over time.

## ⚙️ Enabling Query Store

```sql
ALTER DATABASE [AdventureWorks2022]
SET QUERY_STORE = ON
(
    OPERATION_MODE = READ_WRITE,
    CLEANUP_POLICY = (STALE_QUERY_THRESHOLD_DAYS = 30),
    DATA_FLUSH_INTERVAL_SECONDS = 900,
    INTERVAL_LENGTH_MINUTES = 60,
    MAX_STORAGE_SIZE_MB = 1024
);
```

## 🔍 Look into the views

```sql
SELECT TOP 20 
    qs.query_id, p.plan_id, rs.avg_duration, rs.last_execution_time
FROM sys.query_store_query AS qs
JOIN sys.query_store_plan AS p ON qs.query_id = p.query_id
JOIN sys.query_store_runtime_stats AS rs ON p.plan_id = rs.plan_id
ORDER BY rs.last_execution_time DESC;
```

## 🧩 Plan regression

```sql
EXEC sp_query_store_force_plan @query_id = 42, @plan_id = 7;
```

## 🧹 Clearing Query Store

```sql
ALTER DATABASE [AdventureWorks2022] SET QUERY_STORE CLEAR ALL;
```

> A DBA who deletes history loses an opportunity to learn.

## 💬 Reflection

Query Store is more than a technical feature. It is a metaphor for learning from mistakes, both for SQL Server and for those of us who administer it.

> “Those who cannot remember the past are condemned to repeat it.” — *George Santayana*

## ✅ Checklist

[View the DBA checklist](https://github.com/marcinpytlik/SQLManiak/tree/master/labs/QueryStore/checklists/QueryStore-Checklist.md)

📂 Repository: [SQLManiak/QueryStore-Labs](https://github.com/marcinpytlik/SQLManiak/tree/master/labs/QueryStore)
