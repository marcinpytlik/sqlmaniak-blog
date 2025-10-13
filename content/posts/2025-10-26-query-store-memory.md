---
title: "Query Store – pamięć planów, pamięć błędów"
date: 2025-10-26
slug: query-store-memory
tags: [SQLServer, QueryStore, Performance, Internals, Plans]
draft: false
---

Query Store to pamięć długotrwała SQL Servera – zapisuje plany, decyzje, a czasem i pomyłki.  
Dzięki niemu system potrafi uczyć się na błędach – zachowuje historię wykonania zapytań i pozwala DBA prześledzić ewolucję wydajności. To jak pamiętnik z poprzednich dni – czasem pełen wniosków, czasem skruchy.

### 🔍 Zajrzyj w DMV
```sql
-- pokaż zapisane plany i statystyki wykonania w Query Store
SELECT TOP 20 qs.query_id, p.plan_id, rs.avg_duration, rs.last_execution_time
FROM sys.query_store_query AS qs
JOIN sys.query_store_plan AS p ON qs.query_id = p.query_id
JOIN sys.query_store_runtime_stats AS rs ON p.plan_id = rs.plan_id
ORDER BY rs.last_execution_time DESC;
```

> „Kto nie pamięta błędów, skazany jest na ich powtarzanie.” — Santayana
