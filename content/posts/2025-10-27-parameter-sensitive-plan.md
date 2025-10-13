---
title: "Parameter Sensitive Plan – inteligencja kontekstowa SQL Servera"
date: 2025-10-27
slug: parameter-sensitive-plan
tags: [SQLServer, PSP, Performance, QueryOptimization, Internals]
draft: false
---

Każdy plan zapytania to decyzja, jak przejść od danych do wyniku. Ale jeden plan dla wszystkich parametrów to jak jeden rozmiar buta dla wszystkich nóg.  
*Parameter Sensitive Plan (PSP)* w SQL Server 2022 wprowadza nową elastyczność — system uczy się reagować na kontekst i dopasowuje plan do danych wejściowych.

### 🔍 Zajrzyj w DMV
```sql
-- sprawdź parametry i warianty planów dla zapytań PSP
SELECT query_id, count(distinct plan_id) AS Variants
FROM sys.query_store_plan
GROUP BY query_id
HAVING count(distinct plan_id) > 1;
```

> „Inteligencja to zdolność adaptacji do zmian.” — Stephen Hawking
