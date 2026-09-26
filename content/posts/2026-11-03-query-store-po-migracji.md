---
title: "Query Store po migracji — jak wykrywać regresje planów wykonania"
date: 2026-11-03T20:00:00+01:00
slug: query-store-po-migracji
description: "Jak wykorzystać Query Store po migracji SQL Server do porównania planów, wykrywania regresji i bezpiecznego reagowania na problemy wydajnościowe."
tags: [SQLServer, QueryStore, Performance, Migration, DBA]
categories: [SQL Server]
draft: false
---

Po migracji najgorsze problemy wydajnościowe nie zawsze pojawiają się od razu.

Często aplikacja działa poprawnie, ale pojedyncze zapytania zaczynają korzystać z gorszych planów. Query Store pozwala zobaczyć zmianę zamiast jej zgadywać.

## Czy Query Store działa?

```sql
SELECT
    actual_state_desc,
    desired_state_desc,
    current_storage_size_mb,
    max_storage_size_mb,
    readonly_reason
FROM sys.database_query_store_options;
```

Jeżeli Query Store przeszedł w tryb `READ_ONLY`, najpierw ustal dlaczego.

## Jeden query_id, wiele planów

```sql
SELECT
    p.query_id,
    p.plan_id,
    p.is_forced_plan,
    p.last_execution_time
FROM sys.query_store_plan AS p
WHERE p.query_id = 123
ORDER BY p.last_execution_time DESC;
```

Jeżeli po migracji pojawił się nowy plan, porównaj jego statystyki z wcześniejszym.

## Co porównywać?

- duration,
- CPU,
- logical reads,
- liczbę wykonań,
- waity,
- rozkład parametrów.

Zmiana planu sama w sobie nie jest regresją. Regresją jest pogorszenie zachowania zapytania w reprezentatywnym obciążeniu.

## Force plan — ostrożnie

```sql
EXEC sys.sp_query_store_force_plan
    @query_id = 123,
    @plan_id = 456;
```

To może szybko ograniczyć skutki regresji, ale nie zastępuje analizy przyczyny.

## Podsumowanie

Query Store jest szczególnie wartościowy wtedy, gdy system się zmienia.

Spokojny DBA nie pyta tylko: „czy jest wolno?”. Pyta: „co zmieniło się w zachowaniu konkretnego zapytania?”.