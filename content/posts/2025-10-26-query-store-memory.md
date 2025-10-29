---
title: "Query Store – pamięć planów, pamięć błędów"
date: 2025-10-26
slug: query-store-memory
tags: [SQLServer, QueryStore, Performance, Internals, Plans]
draft: false
---

Query Store to pamięć długotrwała SQL Servera – zapisuje plany, decyzje, a czasem i pomyłki.  
Dzięki niemu system potrafi uczyć się na błędach – zachowuje historię wykonania zapytań i pozwala DBA prześledzić ewolucję wydajności.  
To jak pamiętnik z poprzednich dni – czasem pełen wniosków, czasem skruchy.

## 🧠 Jak działa Query Store
Każde zapytanie, które trafi do silnika SQL Servera, może zostać zapisane w **Query Store** – wraz z planem wykonania i statystykami runtime.  
Z biegiem czasu serwer gromadzi wiedzę: które plany były dobre, a które doprowadziły do regresji.  

> Można powiedzieć, że Query Store to „czarna skrzynka” SQL Servera — zapisuje wszystko, co działo się w optimizerze.

## ⚙️ Włączenie Query Store
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

## 🔍 Zajrzyj w DMV
```sql
SELECT TOP 20 
    qs.query_id, p.plan_id, rs.avg_duration, rs.last_execution_time
FROM sys.query_store_query AS qs
JOIN sys.query_store_plan AS p ON qs.query_id = p.query_id
JOIN sys.query_store_runtime_stats AS rs ON p.plan_id = rs.plan_id
ORDER BY rs.last_execution_time DESC;
```

## 🧩 Plan Regression
```sql
EXEC sp_query_store_force_plan @query_id = 42, @plan_id = 7;
```

## 🧹 Czyszczenie Query Store
```sql
ALTER DATABASE [AdventureWorks2022] SET QUERY_STORE CLEAR ALL;
```

> DBA, który usuwa historię, traci możliwość nauki.

## 💬 Refleksja
Query Store to nie tylko mechanizm techniczny.  
To metafora uczenia się na błędach – zarówno dla SQL Servera, jak i dla nas, administratorów.  

> „Kto nie pamięta błędów, skazany jest na ich powtarzanie.” — *George Santayana*

## ✅ Checklista
[Zobacz checklistę dla DBA](https://github.com/marcinpytlik/SQLManiak/tree/master/labs/QueryStore/checklists/QueryStore-Checklist.md)

📂 Repo: [SQLManiak/QueryStore-Labs](https://github.com/marcinpytlik/SQLManiak/tree/master/labs/QueryStore)
